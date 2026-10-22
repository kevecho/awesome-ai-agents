# ============================================================
# AI Medical Consultant - Structured Output Schemas
# ============================================================
# 专门用于校验 LLM 结构化输出（JSON mode / function calling）。
# 与 app/models/schemas.py 分离——那是 API 响应模型，这是 LLM 输出校验。
# ============================================================
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ==================== 通用异常 ====================

class StructuredOutputError(Exception):
    """LLM 结构化输出解析/校验失败——调用方应据此 fail-closed。"""


# ==================== 症状分析 ====================

class SymptomItem(BaseModel):
    """单条症状——对应 prompt `symptom_analysis` 的 symptoms[]"""
    name: str
    location: str = ""
    duration: str = ""
    severity: str = ""


class SymptomAnalysis(BaseModel):
    """症状分析结果——对应 prompt `symptom_analysis` 的顶层 JSON"""
    symptoms: List[SymptomItem] = Field(default_factory=list)
    missing_info: List[str] = Field(default_factory=list)
    is_emergency: bool = False
    suggested_department: str = ""


# ==================== 分诊 ====================

class TriageResult(BaseModel):
    """分诊结果——对应 prompt `triage` 的顶层 JSON"""
    urgency: Literal["normal", "urgent", "emergency"] = "normal"
    department: str = ""
    reasoning: str = ""
    confidence: float = Field(default=0.0, ge=0, le=1)


# ==================== 诊断 ====================

class ConditionItem(BaseModel):
    """单条鉴别诊断——对应 prompt `diagnosis` 的 possible_conditions[]"""
    name: str
    probability: Literal["high", "medium", "low"] = "medium"
    basis: str = ""
    description: str = ""


class DiagnosisResult(BaseModel):
    """诊断结果——对应 prompt `diagnosis` 的顶层 JSON"""
    possible_conditions: List[ConditionItem] = Field(default_factory=list)
    suggested_exams: List[str] = Field(default_factory=list)
    care_advice: List[str] = Field(default_factory=list)
    when_to_seek_emergency: str = ""
