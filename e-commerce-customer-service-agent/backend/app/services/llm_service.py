"""
LLM provider abstraction layer.

Supports OpenAI, Anthropic, and local (vLLM-compatible) providers through a
unified async interface. Provider selection is controlled by settings.LLM_PROVIDER.
"""

from typing import Any, Optional

import httpx

from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseLLMProvider:
    """Abstract base for LLM providers."""

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        raise NotImplementedError

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        raise NotImplementedError

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        raise NotImplementedError


class OpenAIProvider(BaseLLMProvider):
    """OpenAI-compatible API provider (OpenAI, vLLM, local models)."""

    def __init__(
        self,
        api_key: str,
        api_base: str,
        model: str,
        default_max_tokens: int,
        default_temperature: float,
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Single-turn text generation from a prompt."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, temperature, max_tokens)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Multi-turn chat completion."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.default_temperature,
            "max_tokens": max_tokens or self.default_max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """Streaming chat completion. Yields content chunks."""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.default_temperature,
            "max_tokens": max_tokens or self.default_max_tokens,
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            import json
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            raise


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""

    def __init__(
        self,
        api_key: str,
        model: str,
        default_max_tokens: int,
        default_temperature: float,
    ):
        self.api_key = api_key
        self.model = model
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature
        self.api_base = "https://api.anthropic.com/v1"

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, temperature, max_tokens)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        # Separate system message if present
        system = None
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                api_messages.append(msg)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature or self.default_temperature,
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.api_base}/messages",
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["content"][0]["text"]
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        system = None
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                api_messages.append(msg)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature or self.default_temperature,
            "stream": True,
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.api_base}/messages",
                    headers=self._headers(),
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            import json
                            try:
                                event = json.loads(data_str)
                                if event.get("type") == "content_block_delta":
                                    delta = event.get("delta", {})
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                            except (json.JSONDecodeError, KeyError):
                                continue
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            raise


class LLMService:
    """Unified LLM service with provider abstraction.

    Usage:
        service = LLMService()
        result = await service.generate("Hello, world!")
    """

    def __init__(self):
        self._provider: Optional[BaseLLMProvider] = None

    def _get_provider(self) -> BaseLLMProvider:
        """Lazy-initialize the appropriate LLM provider based on settings."""
        if self._provider is None:
            provider = settings.LLM_PROVIDER.lower()

            if provider == "anthropic":
                if not settings.ANTHROPIC_API_KEY:
                    raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
                self._provider = AnthropicProvider(
                    api_key=settings.ANTHROPIC_API_KEY,
                    model=settings.ANTHROPIC_MODEL,
                    default_max_tokens=settings.LLM_MAX_TOKENS,
                    default_temperature=settings.LLM_TEMPERATURE,
                )
            elif provider == "local":
                self._provider = OpenAIProvider(
                    api_key="not-needed",
                    api_base=settings.LOCAL_LLM_API_BASE,
                    model=settings.LOCAL_LLM_MODEL,
                    default_max_tokens=settings.LLM_MAX_TOKENS,
                    default_temperature=settings.LLM_TEMPERATURE,
                )
            else:
                # Default to OpenAI-compatible
                if not settings.LLM_API_KEY:
                    raise ValueError("LLM_API_KEY is required for OpenAI provider")
                self._provider = OpenAIProvider(
                    api_key=settings.LLM_API_KEY,
                    api_base=settings.LLM_API_BASE,
                    model=settings.LLM_MODEL,
                    default_max_tokens=settings.LLM_MAX_TOKENS,
                    default_temperature=settings.LLM_TEMPERATURE,
                )

        return self._provider

    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text from a single prompt."""
        return await self._get_provider().generate(prompt, temperature, max_tokens)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a chat completion from a message history."""
        return await self._get_provider().chat(messages, temperature, max_tokens)

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """Stream a chat completion, yielding content chunks."""
        async for chunk in self._get_provider().chat_stream(
            messages, temperature, max_tokens
        ):
            yield chunk
