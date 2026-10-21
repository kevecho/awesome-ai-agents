"""
Pydantic schemas for user management and authentication.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    """Request to register a new user."""

    username: str = Field(..., min_length=2, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$", description="Phone number")
    password: str = Field(..., min_length=6, max_length=128, description="Password")


class UserLoginRequest(BaseModel):
    """Request to login."""

    username: str = Field(..., description="Username or email or phone")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token lifetime in seconds")
    user: "UserResponse"


class UserResponse(BaseModel):
    """Public user profile."""

    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email")
    phone: Optional[str] = Field(None, description="Phone")
    user_type: str = Field("customer", description="User role")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_active: bool = Field(True, description="Account status")
    created_at: Optional[datetime] = Field(None, description="Registration time")

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Request to update user profile."""

    email: Optional[EmailStr] = Field(None, description="New email")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    avatar_url: Optional[str] = Field(None)
