from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import func, select

from ai_platform.portal.control_plane import wh09_bootstrap
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.control_plane.models import (
    BotConfigRevisionRow,
    BotRolloutRow,
    BotRow,
    RuntimeGenerationObservationRow,
    RuntimeGenerationRow,
)
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.control_plane.wh09_bootstrap import (
    WH09_BOT_NAME,
    WH09_COMPOSE_PROJECT,
    WH09_COMPOSE_SERVICE,
    WH09_RUNTIME_USER,
    Wh09BootstrapError,
    Wh09HostRuntimeDescriptor,
    bootstrap_wh09,
)
from ai_platform.portal.control_plane.wh09_runtime import (
    WH09_BOT_ID,
    WH09_EXPECTED_MANIFEST_SHA256,
    WH09_EXPECTED_MODEL_ARTIFACT_SHA256,
    WH09_EXPECTED_MODEL_HASH,
    WH09_EXPECTED_PACKAGE_ID,
    WH09_EXPECTED_PARAMETER_HASH,
    Wh09RuntimeEvidence,
)
from ai_platform.wickhunter.contracts import BotMode


NOW = datetime(2026, 8, 10, 7, 30, tzinfo=UTC)
OPERATOR_COMMIT = "3" * 40
RUNTIME_ID = "4" * 64
IMAGE_DIGEST = "5" * 64


class _EvidenceSource:
    def __init__(self, evidence: Wh09RuntimeEvidence) -> None:
        self._evidence = evidence

    def read(self) -> Wh09RuntimeEvidence:
        return self._evidence


def _evidence() -> Wh09RuntimeEvidence:
    return Wh09RuntimeEvidence(
        run_id="1" * 64,
        mode=BotMode.SHADOW,
        health="HEALTHY",
        source_checked_at=NOW,
        source_runtime_generation=7,
        package_id=WH09_EXPECTED_PACKAGE_ID,
        package_manifest_sha256=WH09_EXPECTED_MANIFEST_SHA256,
        model_version="wh09-h900-v1",
        model_hash=WH09_EXPECTED_MODEL_HASH,
        model_artifact_sha256=WH09_EXPECTED_MODEL_ARTIFACT_SHA256,
        parameter_version="wh09-parameters-v1",
        parameter_hash=WH09_EXPECTED_PARAMETER_HASH,
        dataset_hash="2" * 64,
        operator_commit=OPERATOR_COMMIT,
        no_trade_confidence=Decimal("0.60"),
        outcome_horizon_ms=900000,
        decision_count=11,
        no_trade_count=11,
        latest_decision=None,
        health_sha256="6" * 64,
        telemetry_sha256="7" * 64,
        identity_sha256="8" * 64,
    )


def _descriptor(**updates: object) -> Wh09HostRuntimeDescriptor:
    payload: dict[str, object] = {
        "runtime_instance_id": RUNTIME_ID,
        "runtime_image_digest": IMAGE_DIGEST,
        "image_revision": OPERATOR_COMMIT,
        "compose_project": WH09_COMPOSE_PROJECT,
        "compose_service": WH09_COMPOSE_SERVICE,
        "runtime_user": WH09_RUNTIME_USER,
        "matching_container_count": 1,
        "running": True,
        "docker_health": "healthy",
        "read_only_rootfs": True,
        "privileged": False,
        "cap_drop_all": True,
        "no_new_privileges": True,
    }
    payload.update(updates)
    return Wh09HostRuntimeDescriptor.model_validate(payload)


def _count(engine, model: Any) -> int:
    with engine.connect() as connection:
        value = connection.scalar(select(func.count()).select_from(model))
    return int(value or 0)


def test_bootstrap_adopts_existing_wh09_into_one_canonical_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "portal.sqlite"
    database_url = f"sqlite+pysqlite:///{database}"
    engine = build_engine(database_url)
    create_schema(engine)
    monkeypatch.setenv("PORTAL_DATABASE_URL", database_url)
    evidence = _evidence()
    monkeypatch.setattr(
        wh09_bootstrap,
        "configured_wh09_source",
        lambda: _EvidenceSource(evidence),
    )

    first = bootstrap_wh09(_descriptor())
    second = bootstrap_wh09(_descriptor())

    assert first["status"] == "adopted"
    assert first["bot_id"] == "wickhunter"
    assert first["bot_name"] == "WickHunter"
    assert first["managed_mode"] == "shadow"
    assert first["candidate_identity"] == "H900"
    assert first["no_trade_confidence"] == "0.60"
    assert first["health"] == "HEALTHY"
    assert first["desired_runtime_generation_id"] == first["observed_runtime_generation_id"]
    assert second["desired_runtime_generation_id"] == first["desired_runtime_generation_id"]
    assert second["observed_runtime_generation_id"] == first["observed_runtime_generation_id"]
    assert first["trading_credentials_present"] is False
    assert first["order_adapter_present"] is False
    assert first["execution_enabled"] is False
    assert type(first["orders_submitted"]) is int and first["orders_submitted"] == 0
    assert first["live_capital_authorized"] is False
    assert _count(engine, BotRow) == 1
    assert _count(engine, BotConfigRevisionRow) == 1
    assert _count(engine, RuntimeGenerationRow) == 1
    assert _count(engine, BotRolloutRow) == 1
    assert _count(engine, RuntimeGenerationObservationRow) == 1


def test_bootstrap_refuses_to_promote_preexisting_draft(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "portal.sqlite"
    database_url = f"sqlite+pysqlite:///{database}"
    engine = build_engine(database_url)
    create_schema(engine)
    session_factory = build_session_factory(engine)
    monkeypatch.setenv("PORTAL_DATABASE_URL", database_url)
    evidence = _evidence()
    monkeypatch.setattr(
        wh09_bootstrap,
        "configured_wh09_source",
        lambda: _EvidenceSource(evidence),
    )
    service = ControlPlaneService(session_factory)
    context = wh09_bootstrap._context("tenant-local")
    service.create_bot(
        context,
        WH09_BOT_ID,
        WH09_BOT_NAME,
        wh09_bootstrap._spec(evidence),
    )

    with pytest.raises(Wh09BootstrapError, match="DRAFT revision requires explicit promotion"):
        bootstrap_wh09(_descriptor())

    assert _count(engine, BotRow) == 1
    assert _count(engine, BotConfigRevisionRow) == 1
    assert _count(engine, RuntimeGenerationRow) == 0
    assert _count(engine, BotRolloutRow) == 0
    assert _count(engine, RuntimeGenerationObservationRow) == 0


def test_bootstrap_fails_closed_before_mutation_for_non_unique_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "portal.sqlite"
    database_url = f"sqlite+pysqlite:///{database}"
    engine = build_engine(database_url)
    create_schema(engine)
    monkeypatch.setenv("PORTAL_DATABASE_URL", database_url)
    monkeypatch.setattr(
        wh09_bootstrap,
        "configured_wh09_source",
        lambda: _EvidenceSource(_evidence()),
    )

    with pytest.raises(Wh09BootstrapError, match="matching_container_count"):
        bootstrap_wh09(_descriptor(matching_container_count=2))

    assert _count(engine, BotRow) == 0
    assert _count(engine, RuntimeGenerationRow) == 0


def test_bootstrap_rejects_stale_runtime_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "portal.sqlite"
    database_url = f"sqlite+pysqlite:///{database}"
    engine = build_engine(database_url)
    create_schema(engine)
    monkeypatch.setenv("PORTAL_DATABASE_URL", database_url)
    stale = _evidence().model_copy(update={"health": "STALE"})
    monkeypatch.setattr(
        wh09_bootstrap,
        "configured_wh09_source",
        lambda: _EvidenceSource(stale),
    )

    with pytest.raises(Wh09BootstrapError, match="not healthy/current"):
        bootstrap_wh09(_descriptor())

    assert _count(engine, BotRow) == 0
