"""
Slot filling for multi-turn dialogue.

Tracks required information slots and prompts the user to fill missing ones
during multi-turn conversations.
"""

from enum import Enum
from typing import Any, Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SlotStatus(str, Enum):
    """Status of a dialogue slot."""
    EMPTY = "empty"
    FILLED = "filled"
    CONFIRMED = "confirmed"


class SlotFiller:
    """Manages dialogue slots for multi-turn task completion.

    Each intent may require specific slots (e.g., order number for
    order queries). This class tracks which slots are filled and
    generates prompts for missing ones.
    """

    # Required slots per intent
    INTENT_SLOTS: dict[str, list[dict[str, str]]] = {
        "order_query": [
            {"name": "order_no", "prompt": "Could you provide your order number?", "required": False},
        ],
        "order_modify": [
            {"name": "order_no", "prompt": "Which order would you like to modify?", "required": True},
            {"name": "new_address", "prompt": "What is the new shipping address?", "required": False},
        ],
        "refund_request": [
            {"name": "order_no", "prompt": "Which order would you like to refund?", "required": True},
            {"name": "reason", "prompt": "What is the reason for the refund?", "required": False},
        ],
        "complaint": [
            {"name": "order_no", "prompt": "Which order is this regarding?", "required": False},
            {"name": "description", "prompt": "Please describe the issue in detail.", "required": True},
        ],
    }

    def __init__(self):
        self.slots: dict[str, dict[str, Any]] = {}

    def init_slots(self, intent_code: str) -> None:
        """Initialize slots for a given intent."""
        intent_slots = self.INTENT_SLOTS.get(intent_code, [])
        self.slots = {
            slot["name"]: {
                "status": SlotStatus.EMPTY,
                "value": None,
                "prompt": slot["prompt"],
                "required": slot.get("required", False),
            }
            for slot in intent_slots
        }

    def fill_slot(self, name: str, value: Any) -> None:
        """Fill a slot with an extracted value."""
        if name in self.slots:
            self.slots[name]["status"] = SlotStatus.FILLED
            self.slots[name]["value"] = value

    def get_missing_slots(self) -> list[str]:
        """Get list of required but unfilled slot names."""
        return [
            name for name, s in self.slots.items()
            if s["required"] and s["status"] == SlotStatus.EMPTY
        ]

    def get_next_prompt(self) -> Optional[str]:
        """Get the prompt for the next unfilled required slot."""
        for name, slot in self.slots.items():
            if slot["required"] and slot["status"] == SlotStatus.EMPTY:
                return slot["prompt"]
        return None

    def is_complete(self) -> bool:
        """Check if all required slots are filled."""
        return len(self.get_missing_slots()) == 0

    def get_filled_values(self) -> dict[str, Any]:
        """Get all filled slot values."""
        return {
            name: slot["value"]
            for name, slot in self.slots.items()
            if slot["status"] in (SlotStatus.FILLED, SlotStatus.CONFIRMED)
        }

    def reset(self) -> None:
        """Reset all slots."""
        self.slots = {}
