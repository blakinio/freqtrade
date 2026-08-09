from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest

from ai_platform.portal.execution.runtime import RuntimeRecord
from ai_platform.portal.execution.workspace import RuntimeWorkspaceStore


NOW = datetime(2026, 8, 9, 18, 30, tzinfo=UTC)
_IMAGE_DIGEST = "6" * 64


def _record(
    store: RuntimeWorkspaceStore,
    *,
    generation_id: str,
    revision: int = 1,
) -> RuntimeRecord:
    runtime_id = store.runtime_id_for("tenant-a", "bot-1", generation_id)
    return RuntimeRecord(
        tenant_id="tenant-a",
        bot_id="bot-1",
        generation_id=generation_id,
        generation_ordinal=revision,
        generation_spec_digest="1" * 64,
        config_revision_id=f"revision-{revision}",
        config_revision=revision,
        config_revision_digest="2" * 64,
        normalized_runtime_config_digest="3" * 64,
        runtime_image_digest=_IMAGE_DIGEST,
        strategy_artifact_digest="4" * 64,
        model_artifact_digest="5" * 64,
        runtime_id=runtime_id,
        image=f"freqtradeorg/freqtrade@sha256:{_IMAGE_DIGEST}",
        strategy_name="PortalStrategy",
        config_sha256="3" * 64,
        request_id=UUID("00000000-0000-0000-0000-000000000001"),
        correlation_id=UUID("00000000-0000-0000-0000-000000000002"),
        causation_id=None,
        updated_at=NOW,
        last_error_code=None,
    )


def test_storage_roots_are_disjoint_and_raw_identifiers_never_become_path_components(
    tmp_path: Path,
) -> None:
    store = RuntimeWorkspaceStore(tmp_path)
    runtime_id = store.runtime_id_for(
        "../../tenant",
        "../bot",
        "../../generation/../../../escape",
    )

    config_path = store.config_path_for(runtime_id)
    state_path = store.state_path_for(runtime_id)
    record_path = store.record_path_for(runtime_id)

    assert runtime_id.startswith("portal-ft-")
    assert ".." not in runtime_id
    assert config_path.is_relative_to(tmp_path / "runtime-inputs")
    assert state_path.is_relative_to(tmp_path / "runtime-state")
    assert record_path.is_relative_to(tmp_path / "control")
    assert config_path.parent != state_path
    assert config_path.parent != record_path.parent
    assert state_path != record_path.parent


def test_config_is_immutable_per_generation_and_control_manifest_is_separate(
    tmp_path: Path,
) -> None:
    store = RuntimeWorkspaceStore(tmp_path)
    record = _record(store, generation_id="generation-1")
    config = {"dry_run": True, "exchange": {"name": "binance"}}

    store.write_config(record.runtime_id, config)
    store.write_config(record.runtime_id, config)
    store.write_record(record)
    store.set_current_record(record)

    config_path = store.config_path_for(record.runtime_id)
    record_path = store.record_path_for(record.runtime_id)
    assert config_path.stat().st_mode & 0o222 == 0
    assert record_path.exists()
    assert record_path.parent != config_path.parent
    assert record_path.parent != store.state_path_for(record.runtime_id)

    with pytest.raises(ValueError, match="immutable runtime config"):
        store.write_config(
            record.runtime_id,
            {"dry_run": True, "exchange": {"name": "kraken"}},
        )


def test_control_identity_cannot_be_mutated_after_creation(tmp_path: Path) -> None:
    store = RuntimeWorkspaceStore(tmp_path)
    record = _record(store, generation_id="generation-1")
    store.write_record(record)
    store.set_current_record(record)

    with pytest.raises(ValueError, match="control identity cannot change"):
        store.write_record(record.model_copy(update={"runtime_image_digest": "a" * 64}))


def test_historical_record_update_cannot_repoint_current_generation(tmp_path: Path) -> None:
    store = RuntimeWorkspaceStore(tmp_path)
    old = _record(store, generation_id="generation-1")
    current = _record(store, generation_id="generation-2", revision=2)

    store.write_record(old)
    store.set_current_record(old)
    store.write_record(current)
    store.set_current_record(current)

    stale_update = old.model_copy(update={"last_error_code": "STALE_OPERATION"})
    store.write_record(stale_update)

    pointer = store.read_current_record("tenant-a", "bot-1")
    historical = store.read_record(old.runtime_id)
    assert pointer is not None
    assert pointer.generation_id == "generation-2"
    assert pointer.runtime_id == current.runtime_id
    assert historical is not None
    assert historical.last_error_code == "STALE_OPERATION"

    with pytest.raises(ValueError, match="cannot move backwards"):
        store.set_current_record(old)


def test_generation_state_survives_control_record_updates(tmp_path: Path) -> None:
    store = RuntimeWorkspaceStore(tmp_path)
    record = _record(store, generation_id="generation-1")
    state_path = store.ensure_state(record.runtime_id)
    database = state_path / "tradesv3.dryrun.sqlite"
    database.write_text("durable-state", encoding="utf-8")

    store.write_record(record)
    store.set_current_record(record)
    store.write_record(record.model_copy(update={"last_error_code": "TRANSIENT"}))

    assert store.ensure_state(record.runtime_id) == state_path
    assert database.read_text(encoding="utf-8") == "durable-state"
