"""Groq provider running Llama 3.3-70b (groq SDK)."""
from __future__ import annotations

import re

from .base import LLMProvider

# Multimodal (vision) model used automatically when a message contains an image.
_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Llama on Groq sometimes emits tool calls as text instead of structured
# tool_calls, causing a 400 'tool_use_failed'. Recover them from the body.
_FUNC_TAG = re.compile(r"<function=(\w+)\s*(\{.*?\})\s*(?:</function>)?", re.DOTALL)


def _recover_tool_calls(exc: Exception) -> dict | None:
    body = getattr(exc, "body", None)
    if not isinstance(body, dict):
        return None
    err = body.get("error", {}) or {}
    if err.get("code") != "tool_use_failed":
        return None
    generation = err.get("failed_generation", "") or ""
    calls = [
        {"id": f"call_{i}", "name": m.group(1), "arguments": m.group(2)}
        for i, m in enumerate(_FUNC_TAG.finditer(generation))
    ]
    if not calls:
        return None
    content = generation.split("<function=")[0].strip()
    return {"content": content or None, "tool_calls": calls}


class GroqProvider(LLMProvider):
    name = "groq"

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        from groq import AsyncGroq  # lazy import

        self._client = AsyncGroq(api_key=api_key)

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
        # Switch to the vision model automatically when an image is present.
        multimodal = any(isinstance(m.get("content"), list) for m in messages)
        model = _VISION_MODEL if multimodal else self.model
        kwargs: dict = {"model": model, "messages": messages, "temperature": 0.2}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        try:
            resp = await self._client.chat.completions.create(**kwargs)
        except Exception as exc:  # noqa: BLE001
            recovered = _recover_tool_calls(exc)
            if recovered is not None:
                return recovered
            raise
        msg = resp.choices[0].message
        tool_calls = [
            {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
            for tc in (msg.tool_calls or [])
        ]
        return {"content": msg.content, "tool_calls": tool_calls}
