#!/usr/bin/env python3
"""Initialize the database with tables and seed data."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.core.config import settings
from app.core.database import engine, Base
## 导入models文件夹下面的所有文件
from app.models.intent import Intent
from app.models.user import User
from app.models.session import Session
from app.models.message import Message
from app.models.knowledge import KnowledgeItem, Order, Product, Ticket


# from app.models import (
#     User, Session, Message, Intent, KnowledgeItem,
#     Order, Product, Ticket,
# )


async def init_database():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully.")


async def seed_default_data():
    """Insert default intent definitions."""
    from app.core.database import async_session
    from app.models.intent import Intent

    default_intents = [
        Intent(intent_code="order_query", intent_name="Order Query",
               handler_type="tool", priority=8, sample_utterances="Where is my order?|Track order"),
        Intent(intent_code="refund_request", intent_name="Refund Request",
               handler_type="tool", priority=10, sample_utterances="I want a refund|Return my money"),
        Intent(intent_code="product_inquiry", intent_name="Product Inquiry",
               handler_type="rag", priority=5, sample_utterances="Tell me about this product|How much is"),
        Intent(intent_code="complaint", intent_name="Complaint",
               handler_type="transfer", priority=10, sample_utterances="This is terrible|I want to complain"),
        Intent(intent_code="human_agent", intent_name="Human Agent Request",
               handler_type="transfer", priority=10, sample_utterances="Speak to human|Real person"),
        Intent(intent_code="greeting", intent_name="Greeting",
               handler_type="llm", priority=1, sample_utterances="Hello|Hi|Good morning"),
    ]

    async with async_session() as session:
        for intent in default_intents:
            existing = await session.execute(
                __import__("sqlalchemy").select(Intent).where(Intent.intent_code == intent.intent_code)
            )
            if not existing.scalar_one_or_none():
                session.add(intent)

        await session.commit()
    print("Default intent data seeded.")


if __name__ == "__main__":
    print(settings.DATABASE_URL)
    asyncio.run(init_database())
    asyncio.run(seed_default_data())
