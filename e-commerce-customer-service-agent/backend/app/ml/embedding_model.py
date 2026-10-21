"""
Embedding model wrapper for text vectorization.
"""

from app.services.embedding_service import EmbeddingService


class EmbeddingModel:
    """Embedding model for text-to-vector conversion."""

    def __init__(self):
        self.service = EmbeddingService()

    async def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode texts to embedding vectors."""
        return await self.service.encode(texts)

    async def encode_single(self, text: str) -> list[float]:
        """Encode a single text."""
        return await self.service.encode_single(text)
