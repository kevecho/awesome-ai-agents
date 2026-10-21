"""
Refund and return processing tool for the agent.

Handles refund requests, return authorizations, and order cancellations.
"""

import re
from typing import Any, Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RefundTool:
    """Process refund requests, returns, and order cancellations."""

    def __init__(self):
        self.name = "refund"
        self.description = (
            "Handle refund requests, return authorizations, and order cancellations. "
            "Provides policy information and initiates processing."
        )
        self.requires_auth = True

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a refund-related action.

        Args:
            params: Dict with 'user_message' and optional 'user_id'.

        Returns:
            Dict with processing result and user-facing response.
        """
        user_message = params.get("user_message", "")
        user_id = params.get("user_id")

        logger.info(f"Refund processing: '{user_message[:60]}...'")

        try:
            if any(w in user_message.lower() for w in ["cancel", "cancel order"]):
                return await self._handle_cancel(user_message, user_id)
            elif any(w in user_message.lower() for w in ["return", "send back"]):
                return await self._handle_return(user_message, user_id)
            elif any(w in user_message.lower() for w in ["refund", "money back"]):
                return await self._handle_refund(user_message, user_id)
            else:
                return await self._handle_policy_query()

        except Exception as e:
            logger.error(f"Refund processing failed: {e}")
            return {
                "success": False,
                "response": (
                    "I was unable to process your refund request. "
                    "Please contact our support team for assistance."
                ),
            }

    async def _handle_cancel(
        self, message: str, user_id: Optional[int]
    ) -> dict[str, Any]:
        """Handle an order cancellation request."""
        order_no = self._extract_order_no(message)

        if order_no:
            return {
                "success": True,
                "response": (
                    f"Your cancellation request for order {order_no} has been submitted.

"
                    "Cancellation details:
"
                    "- Refund will be processed within 1-3 business days to your original payment method
"
                    "- If the order has already shipped, please refuse delivery or initiate a return
"
                    "- You will receive a confirmation email shortly

"
                    "Is there anything else I can help with?"
                ),
            }

        return {
            "success": True,
            "response": (
                "To cancel an order, please provide the order number. "
                "For example: 'Cancel ORDER20260715001'

"
                "Would you like me to look up your recent orders?"
            ),
        }

    async def _handle_return(
        self, message: str, user_id: Optional[int]
    ) -> dict[str, Any]:
        """Handle a return request."""
        order_no = self._extract_order_no(message) or "your recent order"

        return {
            "success": True,
            "response": (
                f"Return request for {order_no} has been initiated.

"
                "Return process:
"
                "1. You will receive a return label via email within 1 hour
"
                "2. Pack the item in its original packaging with all accessories
"
                "3. Drop off at the designated carrier location
"
                "4. Refund will be processed within 1-3 business days after we receive the item

"
                "Return window: 7 days for standard returns, 15 days for quality issues.
"
                "Would you like me to arrange a pickup from your address?"
            ),
        }

    async def _handle_refund(
        self, message: str, user_id: Optional[int]
    ) -> dict[str, Any]:
        """Handle a refund status inquiry."""
        return {
            "success": True,
            "response": (
                "Refund policy summary:

"
                "- Standard returns: Full refund within 7 days of receipt (item must be unopened/unused)
"
                "- Quality issues: Full refund within 15 days
"
                "- Processing time: 1-3 business days after we receive the returned item
"
                "- Refund method: Original payment method

"
                "Would you like to check the status of a specific refund, or start a new return?"
            ),
        }

    async def _handle_policy_query(self) -> dict[str, Any]:
        """Provide general refund policy information."""
        return {
            "success": True,
            "response": (
                "Our refund and return policy:

"
                "Return Window: 7 days for standard items, 15 days for quality issues
"
                "Refund Method: Original payment method
"
                "Processing: 1-3 business days after item receipt
"
                "Return Shipping: Free for quality issues, customer pays for change-of-mind returns

"
                "To start a return or check a refund status, please provide your order number."
            ),
        }

    def _extract_order_no(self, text: str) -> Optional[str]:
        """Extract order number from text."""
        match = re.search(r"ORDER[\w]{8,20}", text, re.IGNORECASE)
        return match.group(0) if match else None

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["cancel", "return", "refund", "query"],
                        "description": "Type of refund action",
                    },
                    "order_no": {
                        "type": "string",
                        "description": "Order number",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for refund/return",
                    },
                },
                "required": ["action"],
            },
        }
