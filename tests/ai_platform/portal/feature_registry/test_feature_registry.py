from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.feature_registry.router import build_router
from ai_platform.portal.feature_registry.schema import FeatureRegistrySnapshot
from ai_platform.portal.feature_registry.service import FeatureRegistryService


def _context(*, can_read: bool = True) -> RequestContext:
    return RequestContext(
        tenant_id="tenant-a",
        actor_id="analyst-1",
        actor_type=ActorType.USER,
        permissions=(Permission.MODEL_READ,) if can_read else (),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def test_snapshot_and_replay_are_deterministic_and_execution_inert() -> None:
    service = FeatureRegistryService()
    context = _context()

    first = service.snapshot(context)
    second = service.snapshot(context)
    first_replay = service.replay(context)
    second_replay = service.replay(context)

    assert first == second
    assert first.feature_count == 21
    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.execution_authority is False
    assert first_replay == second_replay
    assert first_replay.record_count == first.feature_count
    assert first_replay.append_only is True
    assert first_replay.execution_authority is False
    assert tuple(record.sequence for record in first_replay.records) == tuple(range(21))
    with pytest.raises(ValidationError):
        FeatureRegistrySnapshot.model_validate(
            {
                **first.model_dump(mode="json"),
                "execution_authority": True,
            }
        )


def test_listing_filters_and_feature_detail_use_read_models() -> None:
    service = FeatureRegistryService()
    context = _context()

    approved = service.list_features(context, approved_for_ai=True)
    validated_triggers = service.list_features(
        context,
        status="validated",
        role="trigger",
    )
    feature = service.get_feature(context, "atr.v1")

    assert approved
    assert all(item.approved_for_ai for item in approved)
    assert {item.feature_id for item in validated_triggers} == {
        "macd.v1",
        "roc.v1",
    }
    assert feature.feature_id == "atr.v1"
    assert feature.parameters[0].name == "period"
    assert feature.definition_sha256


def test_dependency_resolution_deduplicates_and_preserves_topology() -> None:
    service = FeatureRegistryService()
    resolution = service.resolve_dependencies(
        _context(),
        ["bos_choch.v1", "supertrend_direction.v1", "bos_choch.v1"],
    )

    assert resolution.requested_feature_ids == (
        "bos_choch.v1",
        "supertrend_direction.v1",
    )
    assert resolution.resolved_feature_ids == (
        "confirmed_pivot.v1",
        "bos_choch.v1",
        "supertrend_direction.v1",
    )
    assert resolution.execution_authority is False


def test_read_permission_is_required() -> None:
    service = FeatureRegistryService()

    with pytest.raises(PermissionError):
        service.snapshot(_context(can_read=False))


def test_router_is_get_only_and_returns_stable_errors() -> None:
    service = FeatureRegistryService()
    app = FastAPI()
    app.include_router(build_router(service, lambda: _context()))
    client = TestClient(app)

    snapshot = client.get("/v1/feature-registry/snapshot")
    resolved = client.get(
        "/v1/feature-registry/resolve",
        params=[
            ("feature_id", "bos_choch.v1"),
            ("feature_id", "supertrend_direction.v1"),
        ],
    )
    missing = client.get("/v1/feature-registry/features/not_registered.v1")
    write_attempt = client.post("/v1/feature-registry/snapshot")

    assert snapshot.status_code == 200
    assert snapshot.json()["feature_count"] == 21
    assert resolved.status_code == 200
    assert resolved.json()["resolved_feature_ids"][0] == "confirmed_pivot.v1"
    assert missing.status_code == 404
    assert missing.json()["detail"]["reason_code"] == "FEATURE_REGISTRY_UNKNOWN_FEATURE"
    assert write_attempt.status_code == 405

    schema = client.get("/openapi.json").json()
    paths = {
        path: methods
        for path, methods in schema["paths"].items()
        if path.startswith("/v1/feature-registry")
    }
    assert paths
    assert all(set(methods) == {"get"} for methods in paths.values())
