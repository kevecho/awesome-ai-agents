"""
Abstract base class for all agents.

Provides session management, tool registration, state tracking,
and conversation history management.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional
import uuid

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseAgent(ABC):
    """Abstract agent providing core capabilities.

    Subclasses must implement process() to handle user input.
    The base class provides:
    - Session and agent identity management
    - Tool registration and lookup
    - State persistence
    - Conversation history with configurable window
    """

    def __init__(self, session_id: str, user_id: Optional[int] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.agent_id = str(uuid.uuid4())[:12]
        self.state: dict[str, Any] = {}
        self.tools: dict[str, Any] = {}
        self.conversation_history: list[dict[str, str]] = []
        self.created_at = datetime.utcnow().isoformat()

        logger.info(f"Agent {self.agent_id} initialized for session {session_id[:8]}")

    def register_tool(self, name: str, tool: Any) -> None:
        """Register a tool that the agent can invoke.

        Args:
            name: Unique tool identifier.
            tool: Tool instance with an async execute(params) method.
        """
        self.tools[name] = tool
        logger.debug(f"Tool registered: {name}")

    def get_tool(self, name: str) -> Optional[Any]:
        """Look up a registered tool by name."""
        return self.tools.get(name)

    def update_state(self, key: str, value: Any) -> None:
        """Store a value in the agent's ephemeral state."""
        self.state[key] = value

    def get_state(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the agent's state."""
        return self.state.get(key, default)

    def add_to_history(self, role: str, content: str) -> None:
        """Append a message to conversation history.

        Args:
            role: 'user', 'assistant', or 'system'.
            content: Message text.
        """
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_history(self, last_n: Optional[int] = None) -> list[dict[str, str]]:
        """Get conversation history, optionally limited to last N messages.

        Args:
            last_n: Number of most recent messages to return.

        Returns:
            List of message dicts with role and content keys.
        """
        if last_n is None:
            return self.conversation_history
        return self.conversation_history[-last_n:]

    def clear_history(self) -> None:
        """Reset conversation history."""
        self.conversation_history = []
        logger.info(f"Agent {self.agent_id} history cleared")

    @abstractmethod
    async def process(self, input_text: str) -> dict[str, Any]:
        """Process user input and return a response.

        Args:
            input_text: User message text.

        Returns:
            Dict with at minimum a 'response' key containing the reply text.
        """
        ...

    def to_dict(self) -> dict[str, Any]:
        """Serialize agent metadata to a dictionary."""
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "state": self.state,
            "tools": list(self.tools.keys()),
            "history_count": len(self.conversation_history),
            "created_at": self.created_at,
        }
