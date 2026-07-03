from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    app_env: str
    host: str
    port: int
    database_url: str
    redis_url: str | None
    primary_provider: str
    secondary_provider: str | None
    provider_timeout_seconds: int
    fake_response_prefix: str
    fake_primary_force_failure: bool
    fake_secondary_force_failure: bool
    openai_api_key: str | None
    openai_base_url: str
    anthropic_api_key: str | None
    anthropic_base_url: str
    anthropic_max_tokens: int
    cache_ttl_seconds: int
    rate_limit_per_minute: int


def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./local.db"),
        redis_url=os.getenv("REDIS_URL"),
        primary_provider=os.getenv("PRIMARY_PROVIDER", "fake"),
        secondary_provider=os.getenv("SECONDARY_PROVIDER", "fake"),
        provider_timeout_seconds=int(os.getenv("PROVIDER_TIMEOUT_SECONDS", "5")),
        fake_response_prefix=os.getenv("FAKE_RESPONSE_PREFIX", "Fake response"),
        fake_primary_force_failure=_as_bool(os.getenv("FAKE_PRIMARY_FORCE_FAILURE")),
        fake_secondary_force_failure=_as_bool(os.getenv("FAKE_SECONDARY_FORCE_FAILURE")),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1"),
        anthropic_max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "256")),
        cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "60")),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")),
    )
