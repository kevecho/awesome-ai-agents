"""
Support ticket creation tool for the agent.

Creates a support ticket for issues that require follow-up
but do not need immediate human attention.
"""

import random
import time
from typing import Any

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CreateTicketTool:
    """Create a support ticket for tracking and follow-up."""

    def __init__(self):
        self.name = "create_ticket"
        self.description = (
            "Create a support ticket to track issues that require follow-up "
            "but do not need immediate human intervention."
        )
        self.requires_auth = True

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create a support ticket.

        Args:
            params: Dict with 'session_id', 'user_id', 'type', 'title', and 'content'.

        Returns:
            Dict with ticket number and confirmation.
        """
        session_id = params.get("session_id", "")
        user_id = params.get("user_id")
        ticket_type = params.get("type", "consult")
        title = params.get("title", "Customer inquiry")
        content = params.get("content", "")

        ticket_no = f"TKT{int(time.time())}{random.randint(100, 999)}"

        logger.info(f"Ticket created: {ticket_no}, type={ticket_type}")

        type_names = {
            "complaint": "Complaint",
            "refund": "Refund Request",
            "consult": "General Inquiry",
            "suggestion": "Feedback",
            "other": "Other",
        }

        return {
            "success": True,
            "response": (
                f"Support ticket {ticket_no} has been created.

"
                f"Type: {type_names.get(ticket_type, ticket_type)}
"
                f"Status: Pending review

"
                "Our team typically responds within 24 hours. "
                "You will receive an update via your registered contact method. "
                "Is there anything else I can help with?"
            ),
            "ticket_no": ticket_no,
        }

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["complaint", "refund", "consult", "suggestion"],
                        "description": "Ticket type",
                    },
                    "title": {
                        "type": "string",
                        "description": "Brief ticket title",
                    },
                    "content": {
                        "type": "string",
                        "description": "Detailed ticket description",
                    },
                },
                "required": ["type", "content"],
            },
        }
