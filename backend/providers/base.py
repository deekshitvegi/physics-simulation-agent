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
        last_exc: Exception | None = None
        async for attempt in AsyncRetrying(
            reraise=False,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(Exception),
        ):
            with attempt:
                try:
                    text = await self._generate(system, user)
                except Exception as exc:  # noqa: BLE001 - surfaced below
                    last_exc = exc
                    logger.warning(
                        "%s completion attempt %d failed: %s",
                        self.name,
                        attempt.retry_state.attempt_number,
                        exc,
                    )
                    raise
                if not text or not text.strip():
                    last_exc = LLMError(f"{self.name} returned an empty response")
                    raise last_exc
                return text

        # AsyncRetrying with reraise=False swallows the final error; re-surface it.
        raise LLMError(
            f"{self.name} failed after 3 attempts: {last_exc}"
        ) from last_exc
