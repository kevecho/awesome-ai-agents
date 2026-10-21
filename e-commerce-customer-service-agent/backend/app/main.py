"""
FastAPI application entry point.

Creates and configures the FastAPI application with all middleware,
routers, and lifecycle handlers.
"""

import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    Startup:
        - Creates database tables (for development; use Alembic in production)
        - Initializes connection pools
        - Logs startup confirmation

    Shutdown:
        - Closes database connection pool
        - Performs graceful cleanup
    """
    logger.info(
        "Application starting",
        extra={"project": settings.PROJECT_NAME, "version": settings.VERSION},
    )

    # In production, use Alembic migrations instead of create_all
    if settings.DEBUG:
        from app.core.database import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified (DEBUG mode)")

    logger.info("Application startup complete")
    yield

    logger.info("Application shutting down")
    await engine.dispose()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent customer service system for e-commerce platforms",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
from app.api.v1.chat import router as chat_router
from app.api.v1.intent import router as intent_router
from app.api.v1.agent import router as agent_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.order import router as order_router
from app.api.v1.product import router as product_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router

API_PREFIX = "/api/v1"

app.include_router(chat_router, prefix=f"{API_PREFIX}/chat", tags=["Chat"])
app.include_router(intent_router, prefix=f"{API_PREFIX}/intent", tags=["Intent"])
app.include_router(agent_router, prefix=f"{API_PREFIX}/agent", tags=["Agent"])
app.include_router(knowledge_router, prefix=f"{API_PREFIX}/knowledge", tags=["Knowledge"])
app.include_router(order_router, prefix=f"{API_PREFIX}/order", tags=["Order"])
app.include_router(product_router, prefix=f"{API_PREFIX}/product", tags=["Product"])
app.include_router(analytics_router, prefix=f"{API_PREFIX}/analytics", tags=["Analytics"])
app.include_router(auth_router, prefix=f"{API_PREFIX}/auth", tags=["Auth"])


@app.get("/")
async def root() -> dict:
    """Root endpoint returning API information."""
    return {
        "message": "E-Commerce Customer Service API",
        "version": settings.VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for monitoring and load balancers."""
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "version": settings.VERSION,
        "database": db_status,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=18080,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
