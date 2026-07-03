from __future__ import annotations

import hashlib
import hmac
import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import APIKey


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return f"sk-{secrets.token_urlsafe(32)}"


def create_api_key_record(session: Session, owner: str) -> tuple[str, APIKey]:
    raw_key = generate_api_key()
    api_key = APIKey(key_hash=hash_api_key(raw_key), owner=owner, active=True)
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return raw_key, api_key


def validate_api_key(session: Session, raw_key: str | None) -> APIKey:
    if not raw_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-API-Key header")

    key_hash = hash_api_key(raw_key)
    api_key = session.scalar(select(APIKey).where(APIKey.key_hash == key_hash))

    if api_key is None or not hmac.compare_digest(api_key.key_hash, key_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    if not api_key.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key is inactive")

    return api_key
