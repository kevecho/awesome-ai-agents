"""
NLU intent classifier using multi-strategy approach.

Provides reusable intent classification that can be used independently
from the intent service.
"""

from typing import Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class IntentClassifier:
    """Multi-strategy intent classifier.

    Methods:
    - classify(text) -> IntentResult
    - batch_classify(texts) -> list[IntentResult]
    """

    def __init__(self, model_type: str = "hybrid"):
        self.model_type = model_type

    async def classify(self, text: str) -> dict:
        """Classify a single text.

        Args:
            text: User input text.

        Returns:
            Dict with intent_code, confidence, and handler_type.
        """
        from app.services.intent_service import IntentService

        service = IntentService()
        result = await service.recognize(text)
        return {
            "intent_code": result.intent_code,
            "intent_name": result.intent_name,
            "confidence": result.confidence,
            "handler_type": result.handler_type,
            "priority": result.priority,
        }

    async def batch_classify(self, texts: list[str]) -> list[dict]:
        """Classify multiple texts.

        Args:
            texts: List of user input texts.

        Returns:
            List of classification results.
        """
        results = []
        for text in texts:
            result = await self.classify(text)
            results.append(result)
        return results
