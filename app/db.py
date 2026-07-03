from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None
_engine_url: str | None = None


def _build_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, future=True, pool_pre_ping=True, connect_args=connect_args)


def init_db() -> None:
    global _engine, _session_factory, _engine_url

    settings = get_settings()
    if _engine is None or _engine_url != settings.database_url:
        if _engine is not None:
            _engine.dispose()
        _engine = _build_engine(settings.database_url)
        _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
        _engine_url = settings.database_url

    Base.metadata.create_all(bind=_engine)


def get_engine() -> Engine:
    init_db()
    assert _engine is not None
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    init_db()
    assert _session_factory is not None
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def db_ready() -> bool:
    try:
        with get_session_factory()() as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def reset_db_state() -> None:
    global _engine, _session_factory, _engine_url

    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
    _engine_url = None
