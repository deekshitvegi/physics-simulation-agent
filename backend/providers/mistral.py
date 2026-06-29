"""Mistral provider (mistralai SDK, v1.x)."""
from __future__ import annotations

from .base import LLMProvider


class MistralProvider(LLMProvider):
    name = "mistral"

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        from mistralai import Mistral  # lazy import

        self._client = Mistral(api_key=api_key)

    async def _generate(self, system: str, user: str) -> str:
        resp = await self._client.chat.complete_async(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""
