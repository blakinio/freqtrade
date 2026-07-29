from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from ai_platform.portal.contracts.identity import ActorType, Permission
from ai_platform.portal.control_plane.api import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import build_engine, build_session_factory
from ai_platform.portal.feature_registry.service import FeatureRegistryService


def test_feature_registry_read_only_vertical_slice() -> None:
    context = RequestContext(
        tenant_id="tenant-a",
        actor_id="analyst-1",
        actor_type=ActorType.USER,
        permissions=(Permission.MODEL_READ,),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )
    engine = build_engine("sqlite+pysqlite:///:memory:")
    factory = build_session_factory(engine)
    client = TestClient(
        create_app(
            factory,
            lambda: context,
            feature_registry_service=FeatureRegistryService(),
        )
    )

    snapshot = client.get("/v1/feature-registry/snapshot")
    listing = client.get(
        "/v1/feature-registry/features",
        params={"approved_for_ai": "true"},
    )
    resolution = client.get(
        "/v1/feature-registry/resolve",
        params=[
            ("feature_id", "bos_choch.v1"),
            ("feature_id", "supertrend_direction.v1"),
        ],
    )
    replay = client.get("/v1/feature-registry/replay")

    assert snapshot.status_code == 200
    assert snapshot.json()["registry_version"] == "1.0.0"
    assert snapshot.json()["feature_count"] == 21
    assert listing.status_code == 200
    assert listing.json()
    assert all(item["approved_for_ai"] for item in listing.json())
    assert resolution.status_code == 200
    assert resolution.json()["resolved_feature_ids"] == [
        "confirmed_pivot.v1",
        "bos_choch.v1",
        "supertrend_direction.v1",
    ]
    assert replay.status_code == 200
    assert replay.json()["append_only"] is True
    assert replay.json()["record_count"] == snapshot.json()["feature_count"]
    assert client.post("/v1/feature-registry/replay").status_code == 405
