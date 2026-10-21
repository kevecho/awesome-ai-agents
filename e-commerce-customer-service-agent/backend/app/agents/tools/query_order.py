"""
Order query tool for the agent.

Retrieves order details, status, and tracking information from the order system.
"""

import re
from typing import Any, Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class QueryOrderTool:
    """Query order information by order number or list recent orders."""

    def __init__(self):
        self.name = "query_order"
        self.description = (
            "Query order details including status, tracking, shipping address, "
            "and payment information."
        )
        self.requires_auth = True

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute an order query.

        Args:
            params: Dict with 'user_message' and optional 'user_id'.

        Returns:
            Dict with query results and formatted response.
        """
        user_message = params.get("user_message", "")
        user_id = params.get("user_id")

        logger.info(f"Order query: user_id={user_id}, message='{user_message[:60]}...'")

        order_no = self._extract_order_no(user_message)

        try:
            if order_no:
                result = await self._query_single_order(order_no, user_id)
            else:
                result = await self._query_recent_orders(user_id)

            return result
        except Exception as e:
            logger.error(f"Order query failed: {e}")
            return {
                "success": False,
                "response": (
                    "I was unable to retrieve your order information at this time. "
                    "Please try again or contact our support hotline."
                ),
            }

    def _extract_order_no(self, text: str) -> Optional[str]:
        """Extract an order number from user text."""
        patterns = [
            r"ORDER[\w]{8,20}",
            r"DD[\d]{10,}",
            r"order[\s#]*(\w{10,20})",
            r"(\w{10,20})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0) if match.lastindex is None else match.group(1)
        return None

    async def _query_single_order(
        self, order_no: str, user_id: Optional[int]
    ) -> dict[str, Any]:
        """Query a specific order. In production, queries the database."""
        return {
            "success": True,
            "response": (
                f"Order {order_no}:
"
                "Status: Shipped
"
                "The order system integration will display full details here. "
                "In production, this would show real-time order status, tracking "
                "number, estimated delivery date, and shipping address."
            ),
            "order": {"order_no": order_no},
        }

    async def _query_recent_orders(
        self, user_id: Optional[int]
    ) -> dict[str, Any]:
        """Query recent orders for a user. In production, queries the database."""
        return {
            "success": True,
            "response": (
                "Here are your recent orders:
"
                "1. ORDER20260715001 - Shipped (July 15, 2026)
"
                "2. ORDER20260710003 - Delivered (July 12, 2026)
"
                "3. ORDER20260705008 - Completed (July 8, 2026)

"
                "Reply with the order number for detailed information."
            ),
            "orders": [],
        }

    def get_schema(self) -> dict[str, Any]:
        """Return the JSON Schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "order_no": {
                        "type": "string",
                        "description": "Order number (optional; omit to list all orders)",
                    },
                },
                "required": [],
            },
        }
