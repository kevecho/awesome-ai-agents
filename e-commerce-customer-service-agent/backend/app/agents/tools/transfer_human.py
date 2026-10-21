"""
Human agent transfer tool.

Transfers the current conversation to a human support agent
when the AI cannot resolve the user's issue.
"""

import random
import time
from typing import Any, Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class TransferHumanTool:
    """Transfer the conversation to a human customer service agent."""

    def __init__(self):
        self.name = "transfer_human"
        self.description = (
            "Transfer the user to a human customer service agent for complex "
            "issues, complaints, or when explicitly requested."
        )
        self.requires_auth = False

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Initiate a transfer to a human agent.

        Args:
            params: Dict with 'session_id', 'user_id', and 'reason'.

        Returns:
            Dict with transfer confirmation, queue position, and wait time.
        """
        session_id = params.get("session_id", "")
        user_id = params.get("user_id")
        reason = params.get("reason", "user_requested")

        logger.info(
            f"Human transfer: session={session_id[:8]}, reason={reason}"
        )

        try:
            transfer_result = await self._queue_transfer(session_id, user_id, reason)
            message = self._generate_message(reason, transfer_result)

            return {
                "success": True,
                "response": message,
                "transfer_id": transfer_result.get("transfer_id"),
                "queue_position": transfer_result.get("position"),
                "estimated_wait_seconds": transfer_result.get("wait_seconds"),
            }
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            return {
                "success": False,
                "response": (
                    "I was unable to connect you to a human agent at this moment. "
                    "Please call our support hotline at 400-XXX-XXXX for immediate assistance."
                ),
            }

    async def _queue_transfer(
        self, session_id: str, user_id: Optional[int], reason: str
    ) -> dict[str, Any]:
        """Add the user to the human agent queue.

        In production, this would use Redis or a message queue.
        """
        transfer_id = f"TRF{int(time.time())}{random.randint(1000, 9999)}"
        position = random.randint(0, 2)
        wait_seconds = position * 180

        return {
            "transfer_id": transfer_id,
            "position": position,
            "wait_seconds": wait_seconds,
        }

    def _generate_message(self, reason: str, result: dict[str, Any]) -> str:
        """Generate an appropriate transfer message based on the reason."""
        position = result.get("position", 0)
        wait_minutes = result.get("wait_seconds", 180) // 60

        if reason == "complaint":
            return (
                "I sincerely apologize for the negative experience. "
                "I am transferring you to a specialist who can address your concerns directly. "
                f"Current queue position: {position + 1}. "
                f"Estimated wait: {wait_minutes} minute(s).

"
                "A support specialist will review your conversation history "
                "before joining, so you will not need to repeat yourself. "
                "Thank you for your patience."
            )
        elif reason == "user_requested":
            return (
                f"Connecting you with a human agent now. "
                f"Queue position: {position + 1}. "
                f"Estimated wait: {wait_minutes} minute(s).

"
                "Please stay on this page. The agent will join automatically. "
                "You can also describe your issue now so the agent can review it "
                "before joining."
            )
        else:
            return (
                f"Transferring to a human agent. "
                f"Queue position: {position + 1}. "
                f"Estimated wait: {wait_minutes} minute(s).

"
                "A support specialist will be with you shortly."
            )

    def get_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "enum": [
                            "user_requested",
                            "complaint",
                            "technical_issue",
                            "other",
                        ],
                        "description": "Reason for transfer",
                    },
                },
                "required": ["reason"],
            },
        }
