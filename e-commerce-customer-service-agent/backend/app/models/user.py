"""User ORM model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger,Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """User account for customers, agents, and administrators."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="User ID")
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="Username"
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True, comment="Email address"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, nullable=True, index=True, comment="Phone number"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Bcrypt password hash"
    )
    user_type: Mapped[str] = mapped_column(
        Enum("customer", "agent", "admin", name="user_type_enum"),
        default="customer",
        nullable=False,
        comment="User role type",
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Avatar image URL"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Account enabled flag"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="Account creation time"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update time",
    )

    sessions = relationship("Session", back_populates="user")
    orders = relationship("Order", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
