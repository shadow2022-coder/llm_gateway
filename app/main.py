from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import create_api_key_record
from app.auth import validate_api_key
from app.cache import build_cache_key, get_cache_backend
from app.config import get_settings
from app.db import db_ready, get_db, init_db
from app.models import RequestLog
from app.rate_limit import get_rate_limiter
from app.router import route_completion
from app.schemas import ChatChoice, ChatCompletionRequest, ChatCompletionResponse, ChatMessage, CreateAPIKeyRequest, CreateAPIKeyResponse, Usage
from app.ui import render_ui


def _build_response(model: str, content: str, prompt_tokens: int, completion_tokens: int) -> ChatCompletionResponse:
    return ChatCompletionResponse(
        id=f"chatcmpl_{uuid.uuid4().hex[:12]}",
        object="chat.completion",
        model=model,
        choices=[
            ChatChoice(
                index=0,
                message=ChatMessage(role="assistant", content=content),
                finish_reason="stop",
            )
        ],
        usage=Usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


def _write_request_log(
    db: Session,
    *,
    api_key_id: Optional[int],
    model_requested: str,
    model_used: Optional[str],
    tokens_in: int,
    tokens_out: int,
    latency_ms: int,
    status_text: str,
    fallback_used: bool,
    cached: bool,
) -> None:
    log_entry = RequestLog(
        api_key_id=api_key_id,
        model_requested=model_requested,
        model_used=model_used,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        status=status_text,
        fallback_used=fallback_used,
        cached=cached,
    )
    db.add(log_entry)
    db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="FastAPI Chat Service", version="0.1.0", lifespan=lifespan)

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return render_ui()

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/readyz")
    def readyz() -> dict[str, str]:
        if db_ready():
            return {"status": "ready"}
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database not ready")

    @app.post("/ui/api-keys", response_model=CreateAPIKeyResponse)
    def create_ui_api_key(payload: CreateAPIKeyRequest, db: Session = Depends(get_db)) -> CreateAPIKeyResponse:
        settings = get_settings()
        if settings.app_env.lower() != "development":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="UI key creation is only enabled in development")

        raw_key, api_key = create_api_key_record(db, owner=payload.owner)
        return CreateAPIKeyResponse(id=api_key.id, owner=api_key.owner, raw_key=raw_key)

    @app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
    def chat_completions(
        payload: ChatCompletionRequest,
        db: Session = Depends(get_db),
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    ) -> ChatCompletionResponse:
        settings = get_settings()
        cache_backend = get_cache_backend(settings)
        rate_limiter = get_rate_limiter(settings)

        started_at = time.perf_counter()
        api_key = None
        model_used: Optional[str] = None
        tokens_in = max(1, len(payload.prompt.split()))
        tokens_out = 0
        cached = False
        fallback_used = False
        status_text = "error"

        try:
            api_key = validate_api_key(db, x_api_key)

            allowed, retry_after = rate_limiter.allow(str(api_key.id), settings.rate_limit_per_minute)
            if not allowed:
                status_text = "rate_limited"
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(retry_after)},
                )

            cache_key = build_cache_key(payload.model, payload.prompt)
            cached_payload = cache_backend.get(cache_key)
            if cached_payload is not None:
                response = ChatCompletionResponse.model_validate(cached_payload["response"])
                model_used = cached_payload["model_used"]
                tokens_in = response.usage.prompt_tokens
                tokens_out = response.usage.completion_tokens
                cached = True
                status_text = "success"
                return response

            routed = route_completion(prompt=payload.prompt, model=payload.model, settings=settings)
            model_used = routed.result.model_used
            tokens_in = routed.result.tokens_in
            tokens_out = routed.result.tokens_out
            fallback_used = routed.fallback_used

            response = _build_response(
                model=model_used,
                content=routed.result.content,
                prompt_tokens=tokens_in,
                completion_tokens=tokens_out,
            )
            cache_backend.set(
                cache_key,
                {
                    "response": response.model_dump(mode="json"),
                    "model_used": model_used,
                },
                settings.cache_ttl_seconds,
            )
            status_text = "success"
            return response
        except HTTPException as exc:
            if status_text == "error":
                status_text = "auth_error" if exc.status_code in {401, 403} else "http_error"
            raise
        except Exception as exc:
            status_text = "provider_error"
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
        finally:
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            _write_request_log(
                db,
                api_key_id=None if api_key is None else api_key.id,
                model_requested=payload.model,
                model_used=model_used,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
                status_text=status_text,
                fallback_used=fallback_used,
                cached=cached,
            )

    return app


app = create_app()
