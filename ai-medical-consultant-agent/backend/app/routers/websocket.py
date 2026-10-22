# ============================================================
# AI Medical Consultant - WebSocket Router
# ============================================================
# 基于文档核心调用关系图 - WebSocket实时流式问答
# ============================================================
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.database import Consultation, Message, User, get_db
from app.models.schemas import ChatRequest
from app.services.agent_service import medical_agent
from app.middleware.auth import decode_access_token

router = APIRouter()


@router.websocket("/api/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket实时流式问诊

    流程:
    1. 验证用户Token
    2. 接收用户消息
    3. Agent处理（症状分析 → RAG检索 → LLM生成）
    4. 流式推送回复（token by token）
    5. 推送结构化元数据（分诊、诊断等）
    6. 持久化存储消息
    """
    await websocket.accept()

    # 验证Token
    user = None
    if token:
        payload = decode_access_token(token)
        if payload:
            user_id = int(payload.get("sub", 0))
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

    if not user:
        await websocket.send_json({"type": "error", "content": "认证失败，请先登录"})
        await websocket.close()
        return

    consultation = None

    try:
        while True:
            # 接收消息
            raw = await websocket.receive_text()
            data = json.loads(raw)

            consultation_id = data.get("consultation_id")
            message_text = data.get("message", "")

            if not message_text:
                continue

            # 验证问诊会话
            result = await db.execute(
                select(Consultation).where(Consultation.id == consultation_id)
            )
            consultation = result.scalar_one_or_none()

            if not consultation or consultation.user_id != user.id:
                await websocket.send_json({"type": "error", "content": "无效的问诊会话"})
                continue

            # 保存用户消息
            user_msg = Message(
                consultation_id=consultation_id,
                role="user",
                content=message_text,
                message_type="text",
            )
            db.add(user_msg)
            await db.commit()

            # 加载对话历史
            history_result = await db.execute(
                select(Message)
                .where(Message.consultation_id == consultation_id)
                .order_by(Message.created_at.desc())
                .limit(20)
            )
            history = history_result.scalars().all()
            history_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(history)
            ]

            # Agent处理并流式输出
            assistant_content = ""
            metadata = {}

            async for chunk in medical_agent.process(
                user_message=message_text,
                consultation_id=consultation_id,
                conversation_history=history_messages,
            ):
                chunk_type = chunk.get("type", "token")
                chunk_content = chunk.get("content", "")
                chunk_meta = chunk.get("metadata", {})

                if chunk_type == "token":
                    assistant_content += chunk_content

                if chunk_type == "complete":
                    metadata = chunk_meta

                await websocket.send_json(chunk)

            # 保存AI回复
            if assistant_content:
                ai_msg = Message(
                    consultation_id=consultation_id,
                    role="assistant",
                    content=assistant_content,
                    message_type=metadata.get("intent", "text"),
                    metadata_json=metadata,
                )
                db.add(ai_msg)
                await db.commit()

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={user.id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "content": str(e)})
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
