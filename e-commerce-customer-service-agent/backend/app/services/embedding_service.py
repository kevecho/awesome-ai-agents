"""
Embedding service for text vectorization.

Supports OpenAI embeddings and local embedding models through a unified interface.
"""

from typing import Optional

import httpx

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings.

    Uses the provider specified in settings.EMBEDDING_PROVIDER.
    Currently supports OpenAI-compatible embedding APIs.
    """

    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER
        self.model = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

        if self.provider == "openai":
            self.api_key = settings.LLM_API_KEY
            self.api_base = settings.LLM_API_BASE
        else:
            # Local embedding service
            self.api_key = "not-needed"
            self.api_base = settings.LOCAL_LLM_API_BASE

    async def encode(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.
            batch_size: Maximum texts per API call.

        Returns:
            List of embedding vectors, each a list of floats.
        """
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await self._encode_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def _encode_batch(self, texts: list[str]) -> list[list[float]]:
        """Encode a single batch of texts."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": texts,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.api_base}/embeddings",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return [item["embedding"] for item in data["data"]]
        except Exception as e:
            logger.error(f"Embedding API error: {e}")
            raise

    async def encode_single(self, text: str) -> list[float]:
        """Generate an embedding for a single text string.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as a list of floats.
        """
        results = await self.encode([text])
        return results[0]
