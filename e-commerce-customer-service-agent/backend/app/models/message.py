"""Chat message ORM model."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, Float, ForeignKey, Integer,
    JSON, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Message(Base):
    """A single message within a chat session."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="Message ID"
    )
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False,
        index=True, comment="Session ID"
    )
    sender_type: Mapped[str] = mapped_column(
        Enum("user", "bot", "agent", name="sender_type_enum"),
        nullable=False,
        comment="Message sender type",
    )
    sender_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="Sender user/agent ID"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Message content"
    )
    content_type: Mapped[str] = mapped_column(
        Enum("text", "image", "voice", "file", "quick_reply", name="content_type_enum"),
        default="text",
        comment="Message content type",
    )
    intent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("intents.id", ondelete="SET NULL"),
        nullable=True,
        comment="Recognized intent ID",
    )
    intent_confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Intent confidence score (0.0 - 1.0)"
    )
    sentiment: Mapped[Optional[str]] = mapped_column(
        Enum("positive", "neutral", "negative", name="sentiment_enum"),
        nullable=True,
        comment="Sentiment classification",
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Sentiment score (-1.0 to 1.0)"
    )
    is_human_transfer: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether this triggered human transfer"
    )
    is_generated: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Whether content was AI-generated"
    )
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional metadata"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="Message creation time"
    )

    session = relationship("Session", back_populates="messages")
    intent = relationship("Intent")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, sender='{self.sender_type}', type='{self.content_type}')>"
