"""检索增强生成（RAG）服务。"""

from typing import Any, Optional

from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RAGService:
    """RAG 管线，用于知识增强的回答生成。"""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()

    async def retrieve(
        self, query: str, top_k: int = 5,
        similarity_threshold: float = 0.7,
        category: Optional[str] = None,
    ) -> str:
        """检索与查询相关的知识库文档。"""
        logger.info(f"RAG 检索: '{query[:80]}...'")
        query_embedding = await self.embedding_service.encode_single(query)
        results = await self._vector_search(query_embedding, top_k, similarity_threshold, category)
        context = self._format_context(results)
        return context

    async def _vector_search(
        self, query_embedding: list[float], top_k: int,
        threshold: float, category: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        try:
            from app.rag.vector_store import VectorStore
            store = VectorStore()
            return await store.search(query_embedding, top_k=top_k, threshold=threshold, category=category)
        except Exception as e:
            logger.warning(f"向量搜索不可用: {e}")
            return []

    def _format_context(self, results: list[dict[str, Any]]) -> str:
        if not results:
            return ""
        parts = []
        for i, doc in enumerate(results, 1):
            score = doc.get("score", 0.0)
            category = doc.get("category", "通用")
            question = doc.get("question", "")
            answer = doc.get("answer", "")
            parts.append(
                f"[文档 {i}] 相关度: {score:.2f} | 分类: {category}\n"
                f"问题: {question}\n答案: {answer}"
            )
        return "\n\n".join(parts)

    async def generate(self, query: str, context: str, system_prompt: Optional[str] = None) -> str:
        if not context:
            return "抱歉，我在知识库中没有找到与您问题相关的信息。是否需要我为您转接人工客服？"
        system = system_prompt or (
            "你是电商平台的客服助手。请仅根据提供的知识库文档回答用户问题。"
            "如果文档中没有包含答案，请明确说明，并建议联系人工客服。保持回答简洁、专业、准确。"
        )
        user_message = f"知识库上下文:\n\n{context}\n\n用户问题: {query}\n\n请基于以上提供的知识库内容回答问题。"
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user_message}]
        return await self.llm_service.chat(messages)

    async def add_document(self, question: str, answer: str, category: str, keywords: Optional[str] = None) -> str:
        text = f"{category} {question} {answer}"
        embedding = await self.embedding_service.encode_single(text)
        vector_id = f"kb_{hash(text) & 0xFFFFFFFF:08x}"
        try:
            from app.rag.vector_store import VectorStore
            store = VectorStore()
            await store.insert(vector_id=vector_id, embedding=embedding,
                metadata={"question": question, "answer": answer, "category": category, "keywords": keywords or ""})
        except Exception as e:
            logger.warning(f"向量存储写入失败: {e}")
        logger.info(f"文档已添加: {vector_id}")
        return vector_id
