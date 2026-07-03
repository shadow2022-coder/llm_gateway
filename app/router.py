from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.providers.anthropic_client import AnthropicProvider
from app.providers.base import BaseProvider, ProviderError, ProviderResult
from app.providers.fake_client import FakeProvider
from app.providers.openai_client import OpenAIProvider


@dataclass
class RoutedResult:
    result: ProviderResult
    fallback_used: bool


def _build_provider(settings: Settings, provider_name: str, force_failure: bool, provider_label: str) -> BaseProvider:
    provider_name = provider_name.lower()

    if provider_name == "fake":
        return FakeProvider(
            provider_name=provider_label,
            response_prefix=settings.fake_response_prefix,
            force_failure=force_failure,
        )
    if provider_name == "openai":
        return OpenAIProvider(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    if provider_name == "anthropic":
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_base_url,
            max_tokens=settings.anthropic_max_tokens,
        )
    raise ProviderError(f"Unsupported provider: {provider_name}")


def route_completion(prompt: str, model: str, settings: Settings) -> RoutedResult:
    primary_provider = _build_provider(
        settings=settings,
        provider_name=settings.primary_provider,
        force_failure=settings.fake_primary_force_failure,
        provider_label="fake-primary",
    )

    try:
        return RoutedResult(
            result=primary_provider.complete(prompt=prompt, model=model, timeout_seconds=settings.provider_timeout_seconds),
            fallback_used=False,
        )
    except ProviderError:
        if not settings.secondary_provider:
            raise

    secondary_provider = _build_provider(
        settings=settings,
        provider_name=settings.secondary_provider,
        force_failure=settings.fake_secondary_force_failure,
        provider_label="fake-secondary",
    )
    return RoutedResult(
        result=secondary_provider.complete(prompt=prompt, model=model, timeout_seconds=settings.provider_timeout_seconds),
        fallback_used=True,
    )
