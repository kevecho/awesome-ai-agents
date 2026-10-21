"""Intent definition ORM model."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import BigInteger,Boolean, DateTime, Enum, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Intent(Base):
    """Predefined intent configuration for NLU intent classification."""

    __tablename__ = "intents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="Intent ID")
    intent_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Intent display name"
    )
    intent_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="Intent code identifier"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Intent description"
    )
    handler_type: Mapped[str] = mapped_column(
        Enum("rag", "tool", "transfer", "llm", "fallback", name="handler_type_enum"),
        nullable=False,
        comment="How this intent should be handled",
    )
    handler_config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Handler-specific configuration"
    )
    sample_utterances: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Example user messages for training"
    )
    priority: Mapped[int] = mapped_column(
        Integer, default=0, comment="Priority (higher = more important)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Whether this intent is enabled"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="Creation time"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="Last update time"
    )

    def __repr__(self) -> str:
        return f"<Intent(code='{self.intent_code}', handler='{self.handler_type}')>"


class IntentRecord(Base):
    """Log of intent recognition results for analytics and improvement."""

    __tablename__ = "intent_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[Optional[int]] = mapped_column(nullable=True, comment="Session ID")
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    recognized_intent: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    entities: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    handler_used: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="Human-verified correctness (for feedback loop)"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
