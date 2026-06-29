"""OpenAI provider (openai SDK)."""
from __future__ import annotations

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        from openai import AsyncOpenAI  # lazy import

        self._client = AsyncOpenAI(api_key=api_key)

    async def _generate(self, system: str, user: str) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""
