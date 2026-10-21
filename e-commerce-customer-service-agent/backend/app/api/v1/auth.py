"""
Authentication API endpoints.

Provides user registration, login, and token refresh.
"""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.schemas.user import (
    TokenResponse,
    UserCreateRequest,
    UserLoginRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user account and return an access token."""
    # Check if username exists
    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists.",
        )

    # Check if email exists
    if request.email:
        result = await db.execute(select(User).where(User.email == request.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            )

    user = User(
        username=request.username,
        email=request.email,
        phone=request.phone,
        password_hash=get_password_hash(request.password),
        user_type="customer",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "user_type": user.user_type}
    )

    logger.info(f"User registered: {user.username} (id={user.id})")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate a user and return an access token."""
    # Try to find user by username, email, or phone
    user: Optional[User] = None

    result = await db.execute(
        select(User).where(
            (User.username == request.username)
            | (User.email == request.username)
            | (User.phone == request.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "user_type": user.user_type}
    )

    logger.info(f"User logged in: {user.username}")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get the current authenticated user's profile."""
    user_id = int(current_user["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    request: UserUpdateRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update the current user's profile."""
    user_id = int(current_user["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)

    return UserResponse.model_validate(user)
