# ============================================================
# AI Medical Consultant - Pydantic Schemas
# ============================================================
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== User ====================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: Optional[str] = None
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ==================== Consultation ====================

class ConsultationCreate(BaseModel):
    title: str = "新问诊"


class ConsultationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    status: str
    symptom_summary: Optional[str] = None
    triage_result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    messages: List["MessageResponse"] = []

    class Config:
        from_attributes = True


# ==================== Message ====================

class MessageCreate(BaseModel):
    content: str
    role: str = "user"  # user, assistant, system
    message_type: str = "text"


class MessageResponse(BaseModel):
    id: int
    consultation_id: int
    role: str
    content: str
    message_type: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Chat / WebSocket ====================

class ChatRequest(BaseModel):
    consultation_id: int
    message: str


class ChatResponse(BaseModel):
    consultation_id: int
    message: str
    message_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    type: str  # "token", "symptom", "triage", "diagnosis", "complete", "error"
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None


# ==================== Knowledge ====================

class KnowledgeCreate(BaseModel):
    title: str
    category: str  # disease, drug, exam, guideline
    content: str
    source: Optional[str] = None


class KnowledgeSearch(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None


class KnowledgeResponse(BaseModel):
    id: int
    title: str
    category: str
    content: str
    source: Optional[str] = None
    score: Optional[float] = None

    class Config:
        from_attributes = True


# ==================== Agent ====================

class AgentSymptomInput(BaseModel):
    consultation_id: int
    symptoms: List[str] = Field(..., description="Collected symptoms list")


class AgentTriageResult(BaseModel):
    department: str
    urgency: str  # normal, urgent, emergency
    confidence: float
    reasoning: str


class AgentDiagnosisResult(BaseModel):
    possible_conditions: List[Dict[str, Any]]  # [{name, probability, description}]
    suggested_exams: List[str]
    care_advice: List[str]
    disclaimer: str = "本内容由AI生成，仅供参考，不构成医疗建议。如有不适请及时就医。"


# ==================== Symptom Collection ====================

class SymptomItem(BaseModel):
    name: str
    location: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None  # mild, moderate, severe
    description: Optional[str] = None


class SymptomCollectionState(BaseModel):
    consultation_id: int
    collected_symptoms: List[SymptomItem] = []
    missing_info: List[str] = []  # What else to ask
    is_complete: bool = False
    next_question: Optional[str] = None
