"""
Order service API endpoints.
"""

from fastapi import APIRouter

from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.get("/{order_no}")
async def get_order(order_no: str) -> dict:
    """Get order details by order number."""
    from app.agents.tools.query_order import QueryOrderTool

    tool = QueryOrderTool()
    result = await tool.execute({
        "user_message": order_no,
        "user_id": None,
    })
    return result
