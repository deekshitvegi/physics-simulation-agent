"""Anthropic Claude provider (anthropic SDK)."""
from __future__ import annotations

from .base import LLMProvider


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        from anthropic import AsyncAnthropic  # lazy import

        self._client = AsyncAnthropic(api_key=api_key)

    async def _generate(self, system: str, user: str) -> str:
        resp = await self._client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.2,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # Response content is a list of blocks; concatenate the text blocks.
        parts = [
            block.text
            for block in resp.content
            if getattr(block, "type", None) == "text"
        ]
        return "".join(parts)
