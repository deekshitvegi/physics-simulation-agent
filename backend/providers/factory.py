"""Provider factory.

Reads configuration and returns the correct ``LLMProvider`` implementation.
The concrete provider modules (and their SDKs) are imported lazily inside
``create`` so that listing *available* providers never requires importing any
SDK — it only checks which API keys are configured.
"""
from __future__ import annotations

from config import Settings, get_settings

from .base import LLMError, LLMProvider

# name -> (settings key attr, settings model attr)
_REGISTRY: dict[str, tuple[str, str]] = {
    "gemini": ("gemini_api_key", "gemini_model"),
    "groq": ("groq_api_key", "groq_model"),
    "mistral": ("mistral_api_key", "mistral_model"),
    "claude": ("anthropic_api_key", "anthropic_model"),
    "openai": ("openai_api_key", "openai_model"),
}

SUPPORTED_PROVIDERS: list[str] = list(_REGISTRY.keys())


class ProviderNotConfigured(LLMError):
    """Raised when the requested provider has no API key configured."""


class UnknownProvider(LLMError):
    """Raised when an unsupported provider name is requested."""


class ProviderFactory:
    @staticmethod
    def available(settings: Settings | None = None) -> list[str]:
        """Return providers that have an API key configured."""
        settings = settings or get_settings()
        return [
            name
            for name, (key_attr, _) in _REGISTRY.items()
            if getattr(settings, key_attr, None)
        ]

    @staticmethod
    def create(
        name: str | None = None, settings: Settings | None = None
    ) -> LLMProvider:
        """Instantiate a provider by name (defaults to ``LLM_PROVIDER``)."""
        settings = settings or get_settings()
        name = (name or settings.llm_provider or "gemini").strip().lower()

        if name not in _REGISTRY:
            raise UnknownProvider(
                f"Unknown provider '{name}'. Supported: {', '.join(SUPPORTED_PROVIDERS)}"
            )

        key_attr, model_attr = _REGISTRY[name]
        api_key = getattr(settings, key_attr, None)
        model = getattr(settings, model_attr)
        if not api_key:
            raise ProviderNotConfigured(
                f"Provider '{name}' is not configured. Set {key_attr.upper()} in .env."
            )

        if name == "gemini":
            from .gemini import GeminiProvider as Provider
        elif name == "groq":
            from .groq import GroqProvider as Provider
        elif name == "mistral":
            from .mistral import MistralProvider as Provider
        elif name == "claude":
            from .claude import ClaudeProvider as Provider
        else:  # openai
            from .openai import OpenAIProvider as Provider

        return Provider(api_key=api_key, model=model)
