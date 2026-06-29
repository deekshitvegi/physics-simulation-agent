"""Google Gemini provider (google-generativeai SDK)."""
from __future__ import annotations

from .base import LLMProvider


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        import google.generativeai as genai  # lazy import

        genai.configure(api_key=api_key)
        self._genai = genai

    async def _generate(self, system: str, user: str) -> str:
        model = self._genai.GenerativeModel(
            self.model,
            system_instruction=system,
            generation_config={"temperature": 0.2},
        )
        resp = await model.generate_content_async(user)
        return resp.text or ""
