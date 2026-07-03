from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.auth import create_api_key_record
from app.cache import reset_cache_backend
from app.db import get_session_factory, reset_db_state
from app.main import app
from app.rate_limit import reset_rate_limiter


@pytest.fixture()
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("PRIMARY_PROVIDER", "fake")
    monkeypatch.setenv("SECONDARY_PROVIDER", "fake")
    monkeypatch.setenv("FAKE_RESPONSE_PREFIX", "Test response")
    monkeypatch.setenv("FAKE_PRIMARY_FORCE_FAILURE", "false")
    monkeypatch.setenv("FAKE_SECONDARY_FORCE_FAILURE", "false")
    monkeypatch.setenv("CACHE_TTL_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")
    monkeypatch.delenv("REDIS_URL", raising=False)

    reset_db_state()
    reset_cache_backend()
    reset_rate_limiter()

    with TestClient(app) as test_client:
        yield test_client

    reset_db_state()
    reset_cache_backend()
    reset_rate_limiter()


@pytest.fixture()
def raw_api_key(client) -> str:
    session_factory = get_session_factory()
    with session_factory() as session:
        raw_key, _ = create_api_key_record(session, owner="pytest")
    return raw_key
