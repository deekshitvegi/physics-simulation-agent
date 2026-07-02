"""Application settings loaded from environment / .env file.

Keeping all configuration in one typed object means the rest of the codebase
never reads ``os.environ`` directly and never references a specific provider.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Active provider when a request does not specify one.
    llm_provider: str = "gemini"

    # API keys (only the ones you use need to be filled in).
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    mistral_api_key: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    # Model overrides per provider. Sensible, broadly-available defaults;
    # change these in .env if you have access to newer models.
    gemini_model: str = "gemini-2.0-flash"
    groq_model: str = "llama-3.3-70b-versatile"
    mistral_model: str = "mistral-large-latest"
    anthropic_model: str = "claude-3-5-sonnet-latest"
    openai_model: str = "gpt-4o-mini"

    # Ollama — run an open-source model locally (free, unlimited, no API key).
    ollama_model: str = "llama3.1"
    ollama_base_url: str = "http://localhost:11434/v1"

    # Server
    port: int = 8000

    # Comma-separated extra CORS origins for production (local dev is always allowed).
    cors_origins: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
