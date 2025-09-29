"""Tests for database configuration."""
from __future__ import annotations

import importlib
import sys
from types import ModuleType

import sqlalchemy


def _cleanup_db_module() -> None:
    sys.modules.pop("app.db", None)
    app_module = sys.modules.get("app")
    if app_module is not None and hasattr(app_module, "db"):
        delattr(app_module, "db")


def _reload_db_module() -> ModuleType:
    _cleanup_db_module()
    settings_module_name = "app.settings"
    if settings_module_name in sys.modules:
        importlib.reload(sys.modules[settings_module_name])
    else:
        importlib.import_module(settings_module_name)

    from app import settings  # type: ignore  # Import after potential reload.

    settings.get_settings.cache_clear()  # type: ignore[attr-defined]

    return importlib.import_module("app.db")


def test_sqlite_engine_includes_connect_args(monkeypatch):
    recorded = {}

    def fake_create_engine(url, **kwargs):
        recorded["url"] = url
        recorded["kwargs"] = kwargs

        class DummyEngine:
            def __init__(self, url: str):
                self.url = sqlalchemy.engine.url.make_url(url)

        return DummyEngine(url)

    monkeypatch.setenv("DATABASE_URL", "sqlite:///./sqlite-test.db")
    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)

    _reload_db_module()

    assert recorded["url"] == "sqlite:///./sqlite-test.db"
    assert recorded["kwargs"].get("pool_pre_ping") is True
    assert recorded["kwargs"].get("connect_args") == {"check_same_thread": False}

    _cleanup_db_module()


def test_non_sqlite_engine_does_not_include_connect_args(monkeypatch):
    recorded = {}

    def fake_create_engine(url, **kwargs):
        recorded["url"] = url
        recorded["kwargs"] = kwargs

        class DummyEngine:
            def __init__(self, url: str):
                self.url = sqlalchemy.engine.url.make_url(url)

        return DummyEngine(url)

    monkeypatch.setenv("DATABASE_URL", "mysql://user:pass@localhost/db")
    monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)

    _reload_db_module()

    assert recorded["url"] == "mysql://user:pass@localhost/db"
    assert recorded["kwargs"].get("pool_pre_ping") is True
    assert "connect_args" not in recorded["kwargs"]

    _cleanup_db_module()


def test_engine_initializes_with_sqlite_fallback(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

    import builtins

    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[override]
        if name == "psycopg2":
            raise ModuleNotFoundError
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    db_module = _reload_db_module()

    session = db_module.SessionLocal()
    try:
        assert db_module.engine.url.get_backend_name() == "sqlite"
    finally:
        session.close()

    _cleanup_db_module()
