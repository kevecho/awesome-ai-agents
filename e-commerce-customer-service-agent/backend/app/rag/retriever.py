"""
RAG retriever that combines vector search with optional reranking.

Coordinates document retrieval, reranking, and context assembly
for the RAG pipeline.
"""

from typing import Any, Optional

from app.services.embedding_service import EmbeddingService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class Retriever:
    """Retrieve relevant documents for a query.

    Pipeline:
    1. Embed query
    2. Search vector store
    3. Optionally rerank results
    4. Return formatted context
    """

    def __init__(
        self,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        enable_rerank: bool = False,
    ):
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.enable_rerank = enable_rerank
        self.embedding_service = EmbeddingService()

    async def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant documents for a query.

        Args:
            query: Search query text.
            category: Optional category filter.

        Returns:
            List of relevant documents with scores.
        """
        # Step 1: Embed the query
        query_embedding = await self.embedding_service.encode_single(query)

        # Step 2: Vector search
        from app.rag.vector_store import VectorStore
        store = VectorStore()
        results = await store.search(
            query_embedding,
            top_k=self.top_k,
            threshold=self.similarity_threshold,
            category=category,
        )

        # Step 3: Rerank (if enabled)
        if self.enable_rerank and results:
            results = await self._rerank(query, results)

        return results

    async def _rerank(
        self,
        query: str,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Rerank results using cross-encoder model.

        In production, this would use a cross-encoder like
        ms-marco-MiniLM-L-6v2 for more accurate relevance scoring.
        """
        # Placeholder for reranking logic
        return sorted(
            results,
            key=lambda x: x.get("score", 0.0),
            reverse=True,
        )
