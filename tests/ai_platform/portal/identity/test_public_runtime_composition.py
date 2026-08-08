from __future__ import annotations

import base64
import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.control_plane.database import build_engine
from ai_platform.portal.database.schema import EXPECTED_SCHEMA_REVISION, migrate_database


PUBLIC_RUNTIME_MODULE = "ai_platform.portal.identity.public_runtime"


def _secret() -> str:
    return base64.urlsafe_b64encode(b"x" * 32).decode("ascii").rstrip("=")


def _configure_public_runtime(monkeypatch: pytest.MonkeyPatch, database_url: str) -> None:
    monkeypatch.setenv("PORTAL_ENVIRONMENT", "staging")
    monkeypatch.setenv("PORTAL_DATABASE_URL", database_url)
    monkeypatch.setenv("PORTAL_IDENTITY_ISSUER", "https://auth.example.test/application/o/portal/")
    monkeypatch.setenv("PORTAL_IDENTITY_CLIENT_ID", "portal-test")
    monkeypatch.setenv("PORTAL_IDENTITY_CLIENT_SECRET", "synthetic-test-secret")
    monkeypatch.setenv("PORTAL_IDENTITY_REDIRECT_URI", "https://portal.example.test/api/identity/callback")
    monkeypatch.setenv("PORTAL_IDENTITY_SESSION_HMAC_KEY_B64", _secret())
    monkeypatch.setenv("PORTAL_IDENTITY_FLOW_ENCRYPTION_KEY_B64", _secret())
    monkeypatch.setenv("PORTAL_IDENTITY_TRANSPORT_MODE", "secure_https")


def _migrated_sqlite(tmp_path: Path) -> str:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'portal.db'}"
    engine = build_engine(database_url)
    try:
        report = migrate_database(engine)
        assert report["status"] == "ready"
    finally:
        engine.dispose()
    return database_url


def _load_public_runtime():
    previous = sys.modules.pop(PUBLIC_RUNTIME_MODULE, None)
    if previous is not None:
        engine = getattr(getattr(previous, "app", None), "state", None)
        database_engine = getattr(engine, "database_engine", None)
        if database_engine is not None:
            database_engine.dispose()
    return importlib.import_module(PUBLIC_RUNTIME_MODULE)


def test_public_runtime_composes_identity_and_canonical_product_routes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_url = _migrated_sqlite(tmp_path)
    _configure_public_runtime(monkeypatch, database_url)

    runtime = _load_public_runtime()
    app = runtime.app
    client = TestClient(app)
    try:
        paths = {route.path for route in app.routes}
        assert runtime._REQUIRED_COMPOSED_ROUTES <= paths
        assert app.state.public_runtime_unprivileged is True

        liveness = client.get("/healthz")
        assert liveness.status_code == 200
        assert liveness.json() == {
            "status": "ok",
            "role": "portal-api",
            "identity_fixture": False,
            "live_capital_authorized": False,
        }

        readiness = client.get("/readyz")
        assert readiness.status_code == 200
        ready = readiness.json()
        assert ready["status"] == "ready"
        assert ready["database_dialect"] == "sqlite"
        assert ready["canonical_schema_revision"] == EXPECTED_SCHEMA_REVISION
        assert ready["required_router_inventory_complete"] is True
        assert ready["runtime_authority"] == "unprivileged"
        assert ready["live_capital_authorized"] is False

        assert client.get("/v1/bots").status_code == 401
        assert client.get("/v1/positions").status_code == 401
    finally:
        app.state.database_engine.dispose()


def test_public_production_runtime_rejects_sqlite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_url = _migrated_sqlite(tmp_path)
    _configure_public_runtime(monkeypatch, database_url)

    runtime = _load_public_runtime()
    runtime.app.state.database_engine.dispose()

    monkeypatch.setenv("PORTAL_ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="requires PostgreSQL"):
        runtime.build_public_app()
