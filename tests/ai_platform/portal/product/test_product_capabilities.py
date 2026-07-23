from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.bots import BotSpec
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.contracts.models import (
    ModelLifecycleState,
    ModelVersion,
    TrainingWindow,
)
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.model_control.service import ModelControlService


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    return build_session_factory(engine)


def _context(tenant_id: str, *permissions: Permission) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"actor-{tenant_id}",
        actor_type=ActorType.USER,
        permissions=permissions,
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _bot_payload(
    tenant_id: str,
    *,
    bot_id: str = "bot-1",
    strategy_version: str = "ai-directional-v1",
) -> dict[str, object]:
    spec = BotSpec(
        tenant_id=tenant_id,
        strategy_version=strategy_version,
        model_version="model-v1",
        risk_policy_version="risk-v1",
        exchange_connection_ref="exchange-opaque-1",
        pair_universe=("BTC/USDT",),
        timeframe="5m",
        capital_allocation="1000",
        capital_currency="USDT",
        runtime_version="freqtrade-2026.7",
        config_revision=1,
        environment=Environment.TEST,
        execution_mode=ExecutionMode.DRY_RUN,
    )
    return {
        "bot_id": bot_id,
        "name": "Portal bot",
        "spec": spec.model_dump(mode="json"),
    }


def test_signal_wizard_persists_advisory_evidence_with_tenant_isolation(
    session_factory: SessionFactory,
) -> None:
    holder = {"context": _context("tenant-a", Permission.BOT_CREATE)}
    client = TestClient(create_app(session_factory, lambda: holder["context"]))
    assert client.post("/v1/bots", json=_bot_payload("tenant-a")).status_code == 201

    holder["context"] = _context("tenant-a", Permission.TRADE_MANUAL_EXECUTE)
    created = client.post(
        "/v1/signals",
        json={
            "bot_id": "bot-1",
            "pair": "BTC/USDT",
            "side": "BUY",
            "timeframe": "5m",
            "confidence": "0.81",
            "rationale": "Reviewed advisory setup",
        },
    )
    assert created.status_code == 201
    assert created.json()["execution_authority"] is False

    holder["context"] = _context("tenant-a", Permission.BOT_READ)
    signals = client.get("/v1/signals").json()
    assert len(signals) == 1
    assert signals[0]["rationale"] == "Reviewed advisory setup"

    holder["context"] = _context("tenant-b", Permission.BOT_READ)
    assert client.get("/v1/signals").json() == []


def test_signal_validation_rejects_pair_outside_immutable_bot_config(
    session_factory: SessionFactory,
) -> None:
    holder = {"context": _context("tenant-a", Permission.BOT_CREATE)}
    client = TestClient(create_app(session_factory, lambda: holder["context"]))
    assert client.post("/v1/bots", json=_bot_payload("tenant-a")).status_code == 201
    holder["context"] = _context("tenant-a", Permission.TRADE_MANUAL_EXECUTE)

    response = client.post(
        "/v1/signals",
        json={
            "bot_id": "bot-1",
            "pair": "ETH/USDT",
            "side": "BUY",
            "timeframe": "5m",
            "confidence": "0.5",
            "rationale": "Should fail",
        },
    )
    assert response.status_code == 422
    assert "pair universe" in response.json()["detail"]


def test_strategy_catalog_and_grid_configs_remain_dry_run_only(
    session_factory: SessionFactory,
) -> None:
    holder = {
        "context": _context(
            "tenant-a",
            Permission.BOT_CREATE,
            Permission.BOT_READ,
        )
    }
    client = TestClient(create_app(session_factory, lambda: holder["context"]))

    strategies = client.get("/v1/strategies")
    assert strategies.status_code == 200
    grid_strategy = next(
        item for item in strategies.json() if item["strategy_version"] == "grid-dry-run-v1"
    )
    assert grid_strategy["allowed_execution_modes"] == ["dry_run"]
    assert grid_strategy["runtime_status"] == "PORTAL_CONFIG_ONLY"

    bot_payload = _bot_payload(
        "tenant-a",
        bot_id="grid-1",
        strategy_version="grid-dry-run-v1",
    )
    assert client.post("/v1/bots", json=bot_payload).status_code == 201
    config = client.post(
        "/v1/grid-bots",
        json={
            "bot_id": "grid-1",
            "pair": "BTC/USDT",
            "lower_price": "90000",
            "upper_price": "110000",
            "levels": 10,
            "quote_allocation": "1000",
        },
    )
    assert config.status_code == 201
    assert config.json()["execution_mode"] == "dry_run"
    assert client.get("/v1/grid-bots").json()[0]["bot_id"] == "grid-1"


def test_notifications_profile_and_admin_obey_identity_and_permission_boundaries(
    session_factory: SessionFactory,
) -> None:
    holder = {"context": _context("tenant-a", Permission.BOT_READ)}
    client = TestClient(create_app(session_factory, lambda: holder["context"]))

    profile = client.get("/v1/profile")
    assert profile.status_code == 200
    assert profile.json()["tenant_id"] == "tenant-a"
    assert profile.json()["secrets_exposed"] is False
    serialized_profile = str(profile.json()).lower()
    for forbidden in ("password", "api_key", "api_secret", "token"):
        assert forbidden not in serialized_profile

    preference = client.get("/v1/notifications/preferences")
    assert preference.status_code == 200
    updated = client.put(
        "/v1/notifications/preferences",
        json={
            "in_app_enabled": True,
            "signal_events": False,
            "risk_events": True,
            "execution_events": False,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["signal_events"] is False

    assert client.get("/v1/admin/overview").status_code == 403
    holder["context"] = _context("tenant-a", Permission.ADMIN_MANAGE)
    admin = client.get("/v1/admin/overview")
    assert admin.status_code == 200
    assert admin.json()["membership_source"] == "external-identity-provider"
    assert any(role["name"] == "admin" for role in admin.json()["builtin_roles"])


def test_model_health_reports_drift_unavailable_without_inventing_telemetry(
    session_factory: SessionFactory,
) -> None:
    model_control = ModelControlService(session_factory)
    now = datetime(2026, 7, 23, 20, 0, tzinfo=UTC)
    model_control.register_model(
        _context("tenant-a", Permission.MODEL_TRAIN),
        ModelVersion(
            model_version_id="model-v1",
            tenant_id="tenant-a",
            model_family_id="family-v1",
            artifact_id="artifact-v1",
            artifact_sha256="1" * 64,
            feature_schema_version_id="features-v1",
            dataset_version_id="dataset-v1",
            training_window=TrainingWindow(
                start_at=now - timedelta(days=90),
                end_at=now - timedelta(days=30),
            ),
            training_pipeline_version_id="pipeline-v1",
            parameters=(),
            git_revision="revision-v1",
            created_at=now - timedelta(days=3),
            lifecycle_state=ModelLifecycleState.DRY_RUN,
        ),
    )
    context = _context("tenant-a", Permission.MODEL_READ)
    client = TestClient(
        create_app(
            session_factory,
            lambda: context,
            model_control_service=model_control,
        )
    )

    health = client.get("/v1/model-health")
    assert health.status_code == 200
    assert health.json()[0]["drift_status"] == "UNAVAILABLE"
    assert health.json()[0]["drift_reason"] == ("CANONICAL_DRIFT_TELEMETRY_SOURCE_NOT_CONFIGURED")


def test_runtime_log_availability_is_permission_gated_and_truthful(
    session_factory: SessionFactory,
) -> None:
    holder = {"context": _context("tenant-a", Permission.BOT_READ)}
    client = TestClient(create_app(session_factory, lambda: holder["context"]))
    assert client.get("/v1/runtime-log-availability").status_code == 403

    holder["context"] = _context("tenant-a", Permission.AUDIT_READ)
    availability = client.get("/v1/runtime-log-availability")
    assert availability.status_code == 200
    assert availability.json()["available"] is False
    assert availability.json()["reason_code"] == (
        "CENTRALIZED_RUNTIME_STDOUT_STDERR_SOURCE_NOT_CONFIGURED"
    )
