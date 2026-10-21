"""Chat session ORM model."""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger, DateTime, Enum, ForeignKey, Integer, String, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Session(Base):
    """A chat session between a user and the customer service system."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Session ID"
    )
    session_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True, comment="Session UUID"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        index=True, comment="User ID"
    )
    agent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="Assigned human agent ID"
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "waiting", "transferred", "closed", name="session_status_enum"),
        default="active",
        nullable=False,
        comment="Session status",
    )
    channel: Mapped[str] = mapped_column(
        String(20), default="web", comment="Source channel (web, mobile, wechat, etc.)"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="Session start time"
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Session end time"
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Last message timestamp"
    )
    message_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="Total message count"
    )
    satisfaction_score: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="User satisfaction rating (1-5)"
    )

    user = relationship("User", back_populates="sessions")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, session_id='{self.session_id}', status='{self.status}')>"
