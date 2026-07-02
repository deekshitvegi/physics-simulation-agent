"""Ollama provider — run open-source models locally (free, unlimited, no key).

Requires Ollama installed and running (https://ollama.com), plus a pulled model,
e.g. `ollama pull llama3.1`. Ollama exposes an OpenAI-compatible API, so we reuse
the OpenAI SDK pointed at the local server.
"""
from __future__ import annotations

from .base import LLMProvider


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str):
        # Local Ollama needs no API key; the OpenAI SDK still wants a placeholder.
        super().__init__("ollama-local", model)
        self.base_url = base_url
        from openai import AsyncOpenAI  # lazy import

        self._client = AsyncOpenAI(base_url=base_url, api_key="ollama")

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

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        kwargs: dict = {"model": self.model, "messages": messages, "temperature": 0.2}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        resp = await self._client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        tool_calls = [
            {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
            for tc in (msg.tool_calls or [])
        ]
        return {"content": msg.content, "tool_calls": tool_calls}
