"""
ML-based sentiment analyzer.

Thin wrapper around the sentiment service for use in ML pipelines.
"""

from app.services.sentiment_service import SentimentService, SentimentType


class SentimentAnalyzer:
    """ML sentiment analysis model wrapper."""

    def __init__(self):
        self.service = SentimentService()

    async def predict(self, text: str) -> dict:
        """Predict sentiment for a text.

        Returns:
            Dict with 'label' (positive/neutral/negative) and 'score' (float).
        """
        sentiment, score = await self.service.analyze(text)
        return {"label": sentiment.value, "score": score}

    async def predict_batch(self, texts: list[str]) -> list[dict]:
        """Predict sentiment for multiple texts."""
        results = []
        for text in texts:
            results.append(await self.predict(text))
        return results
