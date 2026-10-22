# ============================================================
# AI Medical Consultant - Consultation Router
# ============================================================
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Consultation, Message, User, get_db
from app.models.schemas import (
    ConsultationCreate, ConsultationResponse,
    MessageCreate, MessageResponse,
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/consult", tags=["问诊"])


@router.post("/", response_model=ConsultationResponse)
async def create_consultation(
    data: ConsultationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新的问诊会话"""
    import datetime
    consultation = Consultation(
        user_id=current_user.id,
        title=data.title,
    )
    db.add(consultation)
    await db.commit()
    # Build response manually to avoid async lazy-loading issues
    return ConsultationResponse(
        id=consultation.id,
        user_id=consultation.user_id,
        title=consultation.title,
        status=consultation.status or "active",
        symptom_summary=consultation.symptom_summary,
        triage_result=consultation.triage_result,
        created_at=consultation.created_at or datetime.datetime.utcnow(),
        updated_at=consultation.updated_at or datetime.datetime.utcnow(),
        messages=[],
    )


@router.get("/", response_model=List[ConsultationResponse])
async def list_consultations(
    search: str = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的所有问诊会话，支持按标题搜索"""
    query = (
        select(Consultation)
        .options(selectinload(Consultation.messages))
        .where(Consultation.user_id == current_user.id)
    )
    if search:
        query = query.where(Consultation.title.contains(search))
    query = query.order_by(Consultation.updated_at.desc())

    result = await db.execute(query)
    consultations = result.unique().scalars().all()
    return consultations


@router.get("/{consultation_id}", response_model=ConsultationResponse)
async def get_consultation(
    consultation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个问诊会话详情"""
    result = await db.execute(
        select(Consultation)
        .options(selectinload(Consultation.messages))
        .where(Consultation.id == consultation_id)
    )
    consultation = result.unique().scalar_one_or_none()

    if not consultation:
        raise HTTPException(status_code=404, detail="问诊会话不存在")
    if consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此问诊会话")

    return consultation


@router.post("/{consultation_id}/messages", response_model=MessageResponse)
async def add_message(
    consultation_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加消息到问诊会话"""
    result = await db.execute(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    consultation = result.scalar_one_or_none()

    if not consultation:
        raise HTTPException(status_code=404, detail="问诊会话不存在")
    if consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")

    message = Message(
        consultation_id=consultation_id,
        role=data.role,
        content=data.content,
        message_type=data.message_type,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.patch("/{consultation_id}/complete")
async def complete_consultation(
    consultation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """结束问诊会话"""
    import datetime
    result = await db.execute(
        select(Consultation).where(Consultation.id == consultation_id)
    )
    consultation = result.scalar_one_or_none()

    if not consultation:
        raise HTTPException(status_code=404, detail="问诊会话不存在")
    if consultation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作")
    if consultation.status == "completed":
        raise HTTPException(status_code=400, detail="该问诊已结束")

    consultation.status = "completed"
    consultation.updated_at = datetime.datetime.utcnow()
    await db.commit()

    return {
        "id": consultation.id,
        "status": consultation.status,
        "message": "问诊已结束",
    }
