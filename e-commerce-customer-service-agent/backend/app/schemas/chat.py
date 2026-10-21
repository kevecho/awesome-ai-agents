"""
Pydantic schemas for chat-related API requests and responses.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""

    user_id: Optional[int] = Field(None, description="User ID")
    channel: str = Field("web", description="Source channel identifier")
    initial_message: Optional[str] = Field(None, description="Optional first message")


class SessionInfo(BaseModel):
    """Chat session summary information."""

    session_id: str = Field(..., description="Session unique identifier")
    user_id: Optional[int] = Field(None, description="User ID")
    status: str = Field("active", description="Session status")
    channel: str = Field("web", description="Source channel")
    started_at: Optional[datetime] = Field(None, description="Start time")
    message_count: int = Field(0, description="Total messages")
    bot_name: str = Field("XiaoE", description="Bot display name")


class CreateSessionResponse(BaseModel):
    """Response after creating a new session."""

    session: SessionInfo
    welcome_message: str = Field(
        "Hello, I am XiaoE, your intelligent customer service assistant. How can I help you today?",
        description="Initial bot greeting",
    )
    quick_replies: list[str] = Field(default_factory=list, description="Suggested quick replies")


class SendMessageRequest(BaseModel):
    """Request to send a message in a chat session."""

    session_id: str = Field(..., description="Session UUID")
    content: str = Field(..., min_length=1, max_length=2000, description="Message text")
    user_id: Optional[int] = Field(None, description="User ID")
    content_type: str = Field("text", description="Message content type")
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict, description="Extra metadata")


class IntentInfo(BaseModel):
    """Intent recognition result."""

    intent_code: str = Field(..., description="Intent code")
    intent_name: str = Field(..., description="Intent display name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    entities: list[dict[str, Any]] = Field(default_factory=list, description="Extracted entities")
    handler_type: str = Field("llm", description="Processing strategy")
    priority: int = Field(0, description="Intent priority")


class SendMessageResponse(BaseModel):
    """Response after processing a user message."""

    response: str = Field(..., description="Bot response text")
    intent: IntentInfo = Field(..., description="Recognized intent")
    sentiment: str = Field("neutral", description="Detected sentiment")
    sentiment_score: float = Field(0.0, description="Sentiment score (-1.0 to 1.0)")
    quick_replies: list[str] = Field(default_factory=list, description="Suggested follow-ups")
    need_transfer: bool = Field(False, description="Whether human transfer is recommended")


class MessageResponse(BaseModel):
    """A single message in conversation history."""

    id: int = Field(..., description="Message ID")
    session_id: str = Field(..., description="Session UUID")
    sender_type: str = Field(..., description="user, bot, or agent")
    content: str = Field(..., description="Message content")
    content_type: str = Field("text", description="Content type")
    intent: Optional[IntentInfo] = Field(None, description="Recognized intent")
    sentiment: Optional[str] = Field(None, description="Sentiment label")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score")
    created_at: Optional[datetime] = Field(None, description="Creation time")

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Paginated list of messages."""

    messages: list[MessageResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total message count")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Items per page")


class TransferRequest(BaseModel):
    """Request to transfer a session to a human agent."""

    session_id: str = Field(..., description="Session UUID")
    reason: str = Field("user_requested", description="Transfer reason")


class TransferResponse(BaseModel):
    """Response after initiating human transfer."""

    transfer_id: str = Field(..., description="Transfer request ID")
    queue_position: int = Field(..., description="Position in queue")
    estimated_wait_seconds: int = Field(..., description="Estimated wait time")
    message: str = Field(..., description="User-facing transfer message")


class SessionRatingRequest(BaseModel):
    """Request to rate a completed session."""

    session_id: str = Field(..., description="Session UUID")
    score: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    comment: Optional[str] = Field(None, max_length=500, description="Optional feedback")
