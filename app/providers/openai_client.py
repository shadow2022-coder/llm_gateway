from __future__ import annotations

import httpx

from app.providers.base import BaseProvider, ProviderError, ProviderResult


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str | None, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def complete(self, prompt: str, model: str, timeout_seconds: int) -> ProviderResult:
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is not configured")

        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc

        payload = response.json()
        choices = payload.get("choices") or []
        if not choices:
            raise ProviderError("OpenAI response did not include any choices")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise ProviderError("OpenAI response did not include text content")

        usage = payload.get("usage") or {}
        return ProviderResult(
            model_used=payload.get("model", model),
            content=content,
            tokens_in=int(usage.get("prompt_tokens", 0)),
            tokens_out=int(usage.get("completion_tokens", 0)),
            provider_name="openai",
        )
