"""
Product service API endpoints.
"""

from fastapi import APIRouter, Query

from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/search")
async def search_products(
    keywords: str = Query(..., description="Search keywords"),
) -> dict:
    """Search products by keywords."""
    from app.agents.tools.query_product import QueryProductTool

    tool = QueryProductTool()
    result = await tool.execute({
        "user_message": keywords,
    })
    return result
