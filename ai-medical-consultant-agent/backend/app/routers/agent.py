# ============================================================
# AI Medical Consultant - Agent Router
# ============================================================
from typing import List, Optional
from fastapi import APIRouter, Depends
from app.models.schemas import AgentTriageResult, AgentDiagnosisResult, SymptomItem
from app.services.agent_service import medical_agent
from app.middleware.auth import get_current_user
from app.models.database import User

router = APIRouter(prefix="/api/v1/agent", tags=["智能体"])


@router.post("/triage", response_model=AgentTriageResult)
async def agent_triage(
    symptoms: List[SymptomItem],
    current_user: User = Depends(get_current_user),
):
    """执行分诊决策"""
    symptoms_dict = [s.model_dump() for s in symptoms]
    result = await medical_agent.triage(symptoms_dict)

    return AgentTriageResult(
        department=result.department,
        urgency=result.urgency,
        confidence=result.confidence,
        reasoning=result.reasoning,
    )


@router.post("/diagnose", response_model=AgentDiagnosisResult)
async def agent_diagnose(
    symptoms: List[SymptomItem],
    current_user: User = Depends(get_current_user),
):
    """生成鉴别诊断建议"""
    symptoms_dict = [s.model_dump() for s in symptoms]
    result = await medical_agent.diagnose(symptoms_dict)

    return AgentDiagnosisResult(
        possible_conditions=[c.model_dump() if hasattr(c, 'model_dump') else c for c in result.possible_conditions],
        suggested_exams=result.suggested_exams,
        care_advice=result.care_advice,
    )


@router.get("/state")
async def agent_state(current_user: User = Depends(get_current_user)):
    """获取Agent当前状态"""
    return medical_agent.get_state()


@router.post("/reset")
async def agent_reset(current_user: User = Depends(get_current_user)):
    """重置Agent状态"""
    medical_agent._reset()
    return {"message": "Agent状态已重置"}
