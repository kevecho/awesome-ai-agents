"""
Product search tool for the agent.

Searches the product catalog for items matching user queries.
"""

import re
from typing import Any

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class QueryProductTool:
    """Search the product catalog for items matching user criteria."""

    def __init__(self):
        self.name = "query_product"
        self.description = (
            "Search for products by name, category, brand, or keywords. "
            "Returns product details including price, stock, and ratings."
        )
        self.requires_auth = False

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a product search.

        Args:
            params: Dict with 'user_message' containing search keywords.

        Returns:
            Dict with search results and formatted response.
        """
        user_message = params.get("user_message", "")

        logger.info(f"Product search: '{user_message[:60]}...'")

        keywords = self._extract_keywords(user_message)

        if not keywords:
            return {
                "success": True,
                "response": (
                    "What product are you looking for? "
                    "You can search by name, brand, or category, "
                    "for example: 'iPhone 15' or 'running shoes'."
                ),
                "products": [],
            }

        try:
            # In production, query the product database
            products = await self._search_catalog(keywords)
            response = self._format_results(products, keywords)

            return {
                "success": True,
                "response": response,
                "products": products,
            }
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return {
                "success": False,
                "response": "Product search is temporarily unavailable.",
            }

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract product-related keywords from user text."""
        categories = [
            "phone", "laptop", "tablet", "headphones", "speaker", "camera",
            "clothing", "shoes", "bag", "cosmetics", "skincare",
            "appliance", "furniture", "toy", "book", "food",
            "iPhone", "Nike", "Adidas", "Apple", "Dyson",
            "Xiaomi", "Huawei", "Samsung", "Sony", "Philips",
        ]

        found = []
        text_lower = text.lower()

        for cat in categories:
            if cat.lower() in text_lower:
                found.append(cat)

        if not found:
            words = re.findall(r"[\w]{3,}", text)
            found = words[:2]

        return found

    async def _search_catalog(self, keywords: list[str]) -> list[dict]:
        """Search the product catalog. In production, queries the database."""
        # Placeholder for database query
        return []

    def _format_results(self, products: list[dict], keywords: list[str]) -> str:
        """Format product search results for display."""
        if not products:
            kw_str = " ".join(keywords)
            return (
                f"No products found matching '{kw_str}'. "
                "Try different keywords, or let me connect you with a product specialist."
            )

        lines = [f"Found {len(products)} results for your search:
"]
        for i, p in enumerate(products[:5], 1):
            name = p.get("name", "Unknown Product")
            price = p.get("price", 0)
            lines.append(f"{i}. {name} - ${price:.2f}")

        return "
".join(lines)

    def get_schema(self) -> dict[str, Any]:
        """Return the JSON Schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Product search keywords",
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional product category filter",
                    },
                },
                "required": ["keywords"],
            },
        }
