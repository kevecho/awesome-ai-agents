"""Knowledge base and order/product/ticket ORM models."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, Float, ForeignKey, Integer,
    JSON, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class KnowledgeItem(Base):
    """Knowledge base entry for RAG retrieval."""

    __tablename__ = "knowledge"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    vector_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="ID in vector database"
    )
    embedding_model: Mapped[str] = mapped_column(
        String(50), default="text-embedding-ada-002"
    )
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    satisfaction_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Order(Base):
    """Customer order."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(
            "pending", "paid", "shipped", "delivered", "completed",
            "cancelled", "refunded", name="order_status_enum",
        ),
        default="pending",
    )
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    pay_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shipping_address: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    receiver_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    receiver_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tracking_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    express_company: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", back_populates="orders")


class Product(Base):
    """Product catalog entry."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    brand: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    original_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    specifications: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    images: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Ticket(Base):
    """Support ticket for issues requiring human follow-up."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    session_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(
        Enum("complaint", "refund", "consult", "suggestion", "other", name="ticket_type_enum"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("pending", "processing", "resolved", "closed", name="ticket_status_enum"),
        default="pending",
    )
    priority: Mapped[str] = mapped_column(
        Enum("low", "normal", "high", "urgent", name="ticket_priority_enum"),
        default="normal",
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
