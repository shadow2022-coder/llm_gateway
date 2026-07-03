from __future__ import annotations

from app.providers.base import BaseProvider, ProviderError, ProviderResult


class FakeProvider(BaseProvider):
    def __init__(self, provider_name: str, response_prefix: str, force_failure: bool = False) -> None:
        self.provider_name = provider_name
        self.response_prefix = response_prefix
        self.force_failure = force_failure

    def complete(self, prompt: str, model: str, timeout_seconds: int) -> ProviderResult:
        if self.force_failure:
            raise ProviderError(f"{self.provider_name} forced failure")

        tokens_in = max(1, len(prompt.split()))
        content = f"{self.response_prefix} ({self.provider_name}): {prompt}"
        tokens_out = max(1, len(content.split()))
        return ProviderResult(
            model_used=model,
            content=content,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            provider_name=self.provider_name,
        )
