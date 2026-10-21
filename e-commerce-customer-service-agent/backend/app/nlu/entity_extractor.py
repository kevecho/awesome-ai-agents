"""
Entity extraction from user messages.

Extracts structured entities (order numbers, phone numbers, amounts, dates)
from free-text customer messages using regex patterns.
"""

import re
from typing import Any

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class EntityExtractor:
    """Extract named entities from customer messages.

    Supported entity types:
    - order_no: Order numbers (ORDER prefix or numeric patterns)
    - phone: Chinese mobile phone numbers
    - amount: Currency amounts
    - date: Date expressions
    - email: Email addresses
    """

    PATTERNS: dict[str, str] = {
        "order_no": r"ORDER[\w]{8,20}",
        "phone": r"1[3-9]\d{9}",
        "email": r"[\w.+-]+@[\w-]+\.[\w.-]+",
        "amount": r"(?:CNY|USD|EUR|\$|\u00a5|\u20ac)?\s*(\d+(?:\.\d{1,2})?)\s*(?:yuan|dollars|euros)?",
        "tracking_no": r"(?:SF|YT|JD|STO|YUNDA|ZTO)[\d]{8,20}",
    }

    def extract(self, text: str) -> list[dict[str, Any]]:
        """Extract all entities from a text.

        Args:
            text: Free-text customer message.

        Returns:
            List of extracted entities with type, value, and position.
        """
        entities: list[dict[str, Any]] = []

        for entity_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "type": entity_type,
                    "value": match.group(0) if match.lastindex is None else match.group(1),
                    "start": match.start(),
                    "end": match.end(),
                })

        return entities

    def extract_by_type(self, text: str, entity_type: str) -> list[str]:
        """Extract entities of a specific type only.

        Args:
            text: Free-text message.
            entity_type: Type of entity to extract.

        Returns:
            List of entity values.
        """
        if entity_type not in self.PATTERNS:
            return []

        pattern = self.PATTERNS[entity_type]
        return [
            match.group(0) if match.lastindex is None else match.group(1)
            for match in re.finditer(pattern, text, re.IGNORECASE)
        ]
