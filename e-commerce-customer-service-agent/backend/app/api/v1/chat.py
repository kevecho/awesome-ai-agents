"""
Chat API endpoints for the customer service system.

Provides session management, message sending, and conversation history.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.api.deps import get_db, get_current_active_user, pagination_params
from app.schemas.chat import (
    CreateSessionRequest,
    CreateSessionResponse,
    MessageListResponse,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
    SessionRatingRequest,
    TransferRequest,
    TransferResponse,
)
from app.services.chat_service import ChatService
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)
chat_service = ChatService()


@router.post("/session", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest = None,
) -> CreateSessionResponse:
    """Create a new chat session."""
    if request is None:
        request = CreateSessionRequest()
    result = await chat_service.create_session(
        user_id=request.user_id,
        channel=request.channel,
    )
    return CreateSessionResponse(**result)


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
) -> SendMessageResponse:
    """Send a message and receive an AI-generated response."""
    result = await chat_service.process_message(
        session_id=request.session_id,
        content=request.content,
        user_id=request.user_id,
    )
    return SendMessageResponse(**result)


@router.get("/history", response_model=MessageListResponse)
async def get_history(
    session_id: str = Query(..., description="Session UUID"),
    pagination: dict = Depends(pagination_params),
) -> MessageListResponse:
    """Get conversation history for a session."""
    # In production, fetch from database
    # For now, return empty list (stateless service)
    return MessageListResponse(
        messages=[],
        total=0,
        page=pagination["page"],
        page_size=pagination["page_size"],
    )


@router.post("/transfer", response_model=TransferResponse)
async def transfer_to_human(
    request: TransferRequest,
) -> TransferResponse:
    """Transfer the current session to a human agent."""
    import random
    import time

    transfer_id = f"TRF{int(time.time())}{random.randint(1000, 9999)}"
    queue_position = random.randint(0, 3)

    return TransferResponse(
        transfer_id=transfer_id,
        queue_position=queue_position,
        estimated_wait_seconds=queue_position * 180,
        message=(
            "Your conversation has been transferred. A human agent will join shortly. "
            f"You are number {queue_position + 1} in the queue."
        ),
    )


@router.post("/rate", status_code=status.HTTP_200_OK)
async def rate_session(
    request: SessionRatingRequest,
) -> dict:
    """Submit a satisfaction rating for a completed session."""
    logger.info(
        f"Session rated: {request.session_id[:8]}... -> {request.score}/5"
    )
    return {"status": "ok", "message": "Thank you for your feedback."}
