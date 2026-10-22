# ============================================================
# AI Medical Consultant - Database Models
# ============================================================
import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, JSON, Float, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings


class Base(DeclarativeBase):
    pass


# ==================== User ====================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    consultations = relationship("Consultation", back_populates="user")


# ==================== Consultation ====================

class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), default="新问诊")
    status = Column(String(20), default="active")  # active, completed, archived
    symptom_summary = Column(Text, nullable=True)  # AI-summarized symptom
    triage_result = Column(JSON, nullable=True)     # Department recommendation
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="consultations")
    messages = relationship("Message", back_populates="consultation", order_by="Message.created_at")


# ==================== Message ====================

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_type = Column(String(30), default="text")  # text, symptom_collection, triage, diagnosis, follow_up
    metadata_json = Column(JSON, nullable=True)  # Extra structured data
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    consultation = relationship("Consultation", back_populates="messages")


# ==================== Knowledge Document ====================

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # disease, drug, exam, guideline
    content = Column(Text, nullable=False)
    source = Column(String(200), nullable=True)
    chunk_index = Column(Integer, default=0)  # For tracking which chunk
    vector_id = Column(String(100), nullable=True)  # ID in FAISS
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ==================== Database Engine ====================

# Check if using SQLite
_is_sqlite = "sqlite" in settings.DATABASE_URL

if _is_sqlite:
    # SQLite configuration
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
    sync_engine = create_engine(
        settings.DATABASE_URL_SYNC,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL configuration
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=10,
        max_overflow=20,
    )
    sync_engine = create_engine(
        settings.DATABASE_URL_SYNC,
        echo=settings.DEBUG,
    )

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SyncSessionLocal = sessionmaker(
    sync_engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency: Get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """Create all tables (run once at startup)"""
    Base.metadata.create_all(bind=sync_engine)
