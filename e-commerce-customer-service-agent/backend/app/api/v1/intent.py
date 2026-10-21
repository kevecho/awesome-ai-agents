"""
Intent recognition API endpoints.
"""

from fastapi import APIRouter

from app.schemas.intent import (
    IntentBatchRequest,
    IntentBatchResponse,
    IntentClassifyRequest,
    IntentClassifyResponse,
)
from app.services.intent_service import IntentService
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)
intent_service = IntentService()


@router.post("/classify", response_model=IntentClassifyResponse)
async def classify_intent(
    request: IntentClassifyRequest,
) -> IntentClassifyResponse:
    """Classify the intent of a single text."""
    import time
    start = time.monotonic()

    intent = await intent_service.recognize(request.text, request.user_id)

    elapsed_ms = (time.monotonic() - start) * 1000
    return IntentClassifyResponse(intent=intent, processing_time_ms=round(elapsed_ms, 2))


@router.post("/classify-batch", response_model=IntentBatchResponse)
async def classify_intent_batch(
    request: IntentBatchRequest,
) -> IntentBatchResponse:
    """Classify intents for multiple texts in batch."""
    import time

    results = []
    for text in request.texts:
        start = time.monotonic()
        intent = await intent_service.recognize(text)
        elapsed_ms = (time.monotonic() - start) * 1000
        results.append(
            IntentClassifyResponse(intent=intent, processing_time_ms=round(elapsed_ms, 2))
        )

    return IntentBatchResponse(results=results)
