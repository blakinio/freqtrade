from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts.bots import BotConfigRevision, BotConfigRevisionState
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.runtime_generation import RuntimeGenerationMaterial
from ai_platform.portal.control_plane.runtime_generation_api import ActivateRevisionRequest
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.wickhunter.contracts import BotMode
from ai_platform.wickhunter.runtime_mode import (
    ManagedRuntimeModeRequest,
    resolve_managed_runtime_mode,
)


_REQUIRED_BINDING_FIELDS = (
    "isolation_plan_digest",
    "gateway_artifact_digest",
    "gateway_contract_digest",
    "market_data_egress_policy_version",
    "market_data_egress_policy_digest",
)


def _material_payload() -> dict[str, object]:
    return {
        "normalized_runtime_config_digest": "1" * 64,
        "runtime_image_digest": "2" * 64,
        "strategy_artifact_digest": "3" * 64,
        "model_artifact_digest": "4" * 64,
        "feature_schema_version": "features-v1",
        "risk_policy_digest": "5" * 64,
        "exchange_mode": "dry-run-public-market-data",
        "exchange_connection_revision": "exchange-revision-1",
        "isolation_profile_version": "isolation-v1",
        "isolation_profile_digest": "6" * 64,
        "isolation_plan_digest": "7" * 64,
        "gateway_artifact_digest": "8" * 64,
        "gateway_contract_version": "gateway-v1",
        "gateway_contract_digest": "9" * 64,
        "market_data_egress_policy_version": "market-egress-v1",
        "market_data_egress_policy_digest": "a" * 64,
    }


def _revision() -> BotConfigRevision:
    return BotConfigRevision(
        revision_id="revision-1",
        tenant_id="tenant-a",
        bot_id="bot-1",
        revision=1,
        strategy_version="strategy-v1",
        model_version="model-v1",
        risk_policy_version="risk-v1",
        exchange_connection_ref="exchange-connection-1",
        pair_universe=("BTC/USDT",),
        timeframe="5m",
        capital_allocation="1000",
        capital_currency="USDT",
        runtime_version="freqtrade-2026.7",
        environment=Environment.TEST,
        execution_mode=ExecutionMode.DRY_RUN,
        managed_mode=BotMode.SHADOW,
        state=BotConfigRevisionState.PROMOTED,
        revision_content_digest="b" * 64,
        created_by_actor_id="actor-a",
        created_at=datetime(2026, 8, 9, tzinfo=UTC),
    )


@pytest.mark.parametrize("field", _REQUIRED_BINDING_FIELDS)
def test_trusted_generation_material_requires_each_isolation_binding(field: str) -> None:
    payload = _material_payload()
    payload.pop(field)

    with pytest.raises(ValidationError):
        RuntimeGenerationMaterial.model_validate(payload)


@pytest.mark.parametrize("field", _REQUIRED_BINDING_FIELDS)
def test_activation_request_rejects_client_supplied_isolation_binding(field: str) -> None:
    payload: dict[str, object] = {
        "revision_id": "revision-1",
        "expected_state_version": 1,
        "idempotency_key": "apply-1",
        field: "client-controlled-value",
    }

    with pytest.raises(ValidationError):
        ActivateRevisionRequest.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("isolation_plan_digest", "c" * 64),
        ("gateway_artifact_digest", "d" * 64),
        ("gateway_contract_digest", "e" * 64),
        ("market_data_egress_policy_version", "market-egress-v2"),
        ("market_data_egress_policy_digest", "f" * 64),
    ],
)
def test_generation_spec_digest_changes_with_each_isolation_binding(
    field: str,
    replacement: str,
) -> None:
    revision = _revision()
    material = RuntimeGenerationMaterial.model_validate(_material_payload())
    resolution = resolve_managed_runtime_mode(ManagedRuntimeModeRequest(mode=BotMode.SHADOW))
    baseline = ControlPlaneService._managed_generation_spec_digest(
        revision,
        material,
        resolution,
    )

    changed = material.model_copy(update={field: replacement})
    candidate = ControlPlaneService._managed_generation_spec_digest(
        revision,
        changed,
        resolution,
    )

    assert candidate != baseline
