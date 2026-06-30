"""Model-agnostic LLM provider interface.

Every concrete provider implements a single async method, ``_generate``.
The public ``complete`` method wraps it with retry + exponential backoff so the
rest of the application gets resilient LLM calls for free and never has to know
which provider is behind the interface.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when a provider call ultimately fails or returns nothing usable."""


class LLMProvider(ABC):
    """Base class for all LLM providers.

    Subclasses set ``name`` and implement ``_generate``. Construction should
    create whatever SDK client is needed; SDKs are imported lazily inside each
    provider module so a missing optional dependency only affects that provider.
    """

    name: str = "base"

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise LLMError(f"{self.name}: missing API key")
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def _generate(self, system: str, user: str) -> str:
        """Perform a single (un-retried) completion call. Return the text."""
        raise NotImplementedError

    async def chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        """Multi-turn chat with optional tool-calling.

        Returns ``{"content": str | None, "tool_calls": [{"id", "name",
        "arguments"}]}``. Override in providers that support function calling.
        """
        raise NotImplementedError(
            f"Tool-calling chat is not implemented for provider '{self.name}'."
        )

    async def complete(self, system: str, user: str) -> str:
        """Run a completion with 3 attempts and exponential backoff.

        Args:
            system: System / instruction prompt.
            user: User prompt.

        Returns:
            The model's text response (non-empty).

        Raises:
            LLMError: if every attempt fails or the response is empty.
        """
        try:
            async for attempt in AsyncRetrying(
                reraise=True,
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(Exception),
                before_sleep=before_sleep_log(logger, logging.WARNING),
            ):
                with attempt:
                    text = await self._generate(system, user)
                    if not text or not text.strip():
                        raise LLMError(f"{self.name} returned an empty response")
                    return text
        except LLMError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalize provider/SDK errors
            raise LLMError(f"{self.name} request failed: {exc}") from exc

        # Unreachable (the loop always returns or raises), but satisfies typing.
        raise LLMError(f"{self.name} produced no response")
