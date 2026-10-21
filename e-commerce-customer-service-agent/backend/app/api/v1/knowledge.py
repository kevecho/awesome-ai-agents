"""
Knowledge base management API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.services.rag_service import RAGService
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)
rag_service = RAGService()


@router.get("/search")
async def search_knowledge(
    query: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(5, ge=1, le=20, description="Maximum results"),
    category: Optional[str] = Query(None, description="Filter by category"),
) -> dict:
    """Search the knowledge base for relevant documents."""
    context = await rag_service.retrieve(
        query=query,
        top_k=top_k,
        category=category,
    )

    if not context:
        return {"results": [], "query": query, "message": "No matching documents found."}

    return {"results": [{"context": context}], "query": query}


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def add_document(
    question: str,
    answer: str,
    category: str = "general",
    keywords: Optional[str] = None,
) -> dict:
    """Add a document to the knowledge base."""
    vector_id = await rag_service.add_document(
        question=question,
        answer=answer,
        category=category,
        keywords=keywords,
    )
    return {"vector_id": vector_id, "status": "created"}
