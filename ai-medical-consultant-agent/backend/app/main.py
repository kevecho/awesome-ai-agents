# ============================================================
# AI Medical Consultant - FastAPI Main Entry
# ============================================================
# 基于文档 4.1.2 FastAPI主入口 实现
# ============================================================
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys
from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.models.database import init_db
from app.services.rag_service import rag_service
from app.routers import user, consult, knowledge, agent, websocket


# ==================== 生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭生命周期"""
    # 启动时
    logger.info("=" * 60)
    logger.info("AI Medical Consultant - 启动中...")
    logger.info(f"LLM Model: {settings.LLM_MODEL}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    logger.info("=" * 60)

    # 初始化数据库表
    try:
        init_db()
        logger.info("[OK] 数据库表初始化完成")
    except Exception as e:
        logger.warning(f"数据库初始化跳过（可能未连接）: {e}")

    # 初始化RAG服务
    try:
        await rag_service.initialize()
        logger.info(f"[OK] RAG服务初始化完成 (文档数: {rag_service.document_count})")
    except Exception as e:
        logger.error(f"RAG服务初始化失败: {e}")

    logger.info("[OK] 服务已就绪")

    yield

    # 关闭时
    logger.info("AI Medical Consultant - 正在关闭...")


# ==================== 创建应用 ====================

app = FastAPI(
    title="AI Medical Consultant",
    description="基于LLM大模型 + Agent架构 + RAG检索增强的智能医疗问诊系统",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ==================== 中间件 ====================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "error": str(exc) if settings.DEBUG else ""},
    )


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response


# ==================== 健康检查 ====================

@app.get("/")
async def root():
    return {
        "service": "AI Medical Consultant",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "llm_model": settings.LLM_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "rag_documents": rag_service.document_count,
    }


# ==================== 注册路由 ====================

app.include_router(user.router)
app.include_router(consult.router)
app.include_router(agent.router)
app.include_router(knowledge.router)
app.include_router(websocket.router)


# ==================== 主入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
