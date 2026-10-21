"""
Pydantic schemas for intent recognition and entity extraction.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """A named entity extracted from user text."""

    type: str = Field(..., description="Entity type (e.g. order_no, phone, product_name)")
    value: str = Field(..., description="Extracted entity value")
    start: int = Field(0, description="Character start position")
    end: int = Field(0, description="Character end position")


class IntentResult(BaseModel):
    """Complete intent recognition result."""

    intent_code: str = Field(..., description="Intent code")
    intent_name: str = Field(..., description="Intent display name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    entities: list[Entity] = Field(default_factory=list, description="Extracted entities")
    handler_type: str = Field("llm", description="Recommended handler")
    priority: int = Field(0, description="Intent priority")


class IntentClassifyRequest(BaseModel):
    """Request to classify intent from text."""

    text: str = Field(..., min_length=1, max_length=2000, description="User input text")
    user_id: Optional[int] = Field(None, description="User ID for context")


class IntentClassifyResponse(BaseModel):
    """Response with classified intent."""

    intent: IntentResult = Field(..., description="Classification result")
    processing_time_ms: float = Field(..., description="Time taken for classification")


class IntentBatchRequest(BaseModel):
    """Request to classify multiple texts."""

    texts: list[str] = Field(..., min_length=1, max_length=50, description="Texts to classify")


class IntentBatchResponse(BaseModel):
    """Response with batch classification results."""

    results: list[IntentClassifyResponse] = Field(..., description="Per-text results")
