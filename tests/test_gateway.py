from __future__ import annotations

from sqlalchemy import select

from app.db import get_session_factory
from app.models import APIKey, RequestLog


def _all_logs() -> list[RequestLog]:
    session_factory = get_session_factory()
    with session_factory() as session:
        return list(session.scalars(select(RequestLog).order_by(RequestLog.id)))


def test_auth_rejection(client) -> None:
    response = client.post("/v1/chat/completions", json={"prompt": "hello", "model": "fake-model"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing X-API-Key header"

    logs = _all_logs()
    assert len(logs) == 1
    assert logs[0].status == "auth_error"


def test_inactive_api_key_rejection(client, raw_api_key) -> None:
    session_factory = get_session_factory()
    with session_factory() as session:
        api_key = session.scalar(select(APIKey))
        assert api_key is not None
        api_key.active = False
        session.commit()

    response = client.post(
        "/v1/chat/completions",
        headers={"X-API-Key": raw_api_key},
        json={"prompt": "hello", "model": "fake-model"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "API key is inactive"


def test_successful_request(client, raw_api_key) -> None:
    response = client.post(
        "/v1/chat/completions",
        headers={"X-API-Key": raw_api_key},
        json={"prompt": "hello world", "model": "fake-model"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "fake-model"
    assert body["choices"][0]["message"]["content"].startswith("Test response")

    logs = _all_logs()
    assert logs[-1].status == "success"
    assert logs[-1].cached is False
    assert logs[-1].fallback_used is False


def test_rate_limit_trigger(client, raw_api_key) -> None:
    headers = {"X-API-Key": raw_api_key}

    first = client.post("/v1/chat/completions", headers=headers, json={"prompt": "one", "model": "fake-model"})
    second = client.post("/v1/chat/completions", headers=headers, json={"prompt": "two", "model": "fake-model"})
    third = client.post("/v1/chat/completions", headers=headers, json={"prompt": "three", "model": "fake-model"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.headers["Retry-After"]

    logs = _all_logs()
    assert logs[-1].status == "rate_limited"


def test_fallback_trigger(client, raw_api_key, monkeypatch) -> None:
    monkeypatch.setenv("FAKE_PRIMARY_FORCE_FAILURE", "true")
    monkeypatch.setenv("FAKE_SECONDARY_FORCE_FAILURE", "false")

    response = client.post(
        "/v1/chat/completions",
        headers={"X-API-Key": raw_api_key},
        json={"prompt": "needs fallback", "model": "fake-model"},
    )

    assert response.status_code == 200
    assert "fake-secondary" in response.json()["choices"][0]["message"]["content"]

    logs = _all_logs()
    assert logs[-1].fallback_used is True


def test_cache_hit(client, raw_api_key) -> None:
    headers = {"X-API-Key": raw_api_key}
    payload = {"prompt": "cache me", "model": "fake-model"}

    first = client.post("/v1/chat/completions", headers=headers, json=payload)
    second = client.post("/v1/chat/completions", headers=headers, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["choices"][0]["message"]["content"] == second.json()["choices"][0]["message"]["content"]

    logs = _all_logs()
    assert logs[-2].cached is False
    assert logs[-1].cached is True


def test_readyz(client) -> None:
    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
