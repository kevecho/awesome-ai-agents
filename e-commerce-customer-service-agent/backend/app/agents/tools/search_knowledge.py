"""
Knowledge base search tool for the agent.

Retrieves relevant information from the knowledge base to answer user questions
about products, policies, and frequently asked questions.
"""

from typing import Any

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SearchKnowledgeTool:
    """Search the knowledge base for information relevant to the user query."""

    def __init__(self):
        self.name = "search_knowledge"
        self.description = (
            "Search the knowledge base for product information, platform policies, "
            "and frequently asked questions."
        )
        self.requires_auth = False

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a knowledge base search.

        Args:
            params: Dict with 'user_message', optional 'top_k', optional 'intent'.

        Returns:
            Dict with 'success', 'response', 'results', and 'source' keys.
        """
        user_message = params.get("user_message", "")
        top_k = params.get("top_k", 3)

        logger.info(f"Knowledge search: '{user_message[:60]}...'")

        try:
            from app.services.rag_service import RAGService
            rag = RAGService()
            context = await rag.retrieve(user_message, top_k=top_k)

            if not context:
                return {
                    "success": False,
                    "response": (
                        "I could not find relevant information in the knowledge base. "
                        "Would you like me to connect you with a human agent?"
                    ),
                    "results": [],
                    "source": "knowledge_base",
                }

            response = await rag.generate(user_message, context)

            return {
                "success": True,
                "response": response,
                "results": [{"context": context}],
                "source": "knowledge_base",
            }
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return {
                "success": False,
                "response": "The knowledge base is temporarily unavailable. Please try again later.",
                "results": [],
                "source": "knowledge_base",
            }

    def get_schema(self) -> dict[str, Any]:
        """Return the JSON Schema for this tool's parameters."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's search query",
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional knowledge category filter",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        }
