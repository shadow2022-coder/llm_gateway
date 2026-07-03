from __future__ import annotations

import httpx

from app.providers.base import BaseProvider, ProviderError, ProviderResult


class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str | None, base_url: str, max_tokens: int) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens

    def complete(self, prompt: str, model: str, timeout_seconds: int) -> ProviderResult:
        if not self.api_key:
            raise ProviderError("ANTHROPIC_API_KEY is not configured")

        try:
            with httpx.Client(timeout=timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": model,
                        "max_tokens": self.max_tokens,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Anthropic request failed: {exc}") from exc

        payload = response.json()
        content_blocks = payload.get("content") or []
        text_parts: list[str] = []
        for block in content_blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(str(block.get("text", "")))

        content = "\n".join(part for part in text_parts if part).strip()
        if not content:
            raise ProviderError("Anthropic response did not include text content")

        usage = payload.get("usage") or {}
        return ProviderResult(
            model_used=payload.get("model", model),
            content=content,
            tokens_in=int(usage.get("input_tokens", 0)),
            tokens_out=int(usage.get("output_tokens", 0)),
            provider_name="anthropic",
        )
