from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import ActorType
from ai_platform.portal.contracts.strategy_closure import (
    CapabilityRequirement,
    ClosureRequestContext,
    PublicContractProvenance,
    SignalWizardFeatureSelection,
    SignalWizardPreviewCommand,
    SignalWizardPreviewResult,
    SignalWizardSubmitCommand,
    StrategyCapability,
    StrategyDeploymentCommand,
    StrategyDeploymentMode,
    StrategyRollbackCommand,
)
from ai_platform.portal.product.schema import (
    StrategyCatalogEntry,
    StrategyKind,
    StrategyLifecycleState,
    StrategyRuntimeStatus,
)


NOW = datetime(2026, 7, 30, 10, 0, tzinfo=UTC)
HASH = "a" * 64


def _provenance(**updates: object) -> PublicContractProvenance:
    values: dict[str, object] = {
        "producer": "portal-bff",
        "artifact_id": "artifact-1",
        "created_at": NOW,
        "source_refs": ("strategy:v1",),
    }
    values.update(updates)
    return PublicContractProvenance.model_validate(values)


def _context() -> ClosureRequestContext:
    return ClosureRequestContext(
        tenant_id="tenant-1",
        actor_id="actor-1",
        actor_type=ActorType.USER,
        resource_type="strategy",
        resource_id="strategy-1",
        environment=Environment.RESEARCH,
        execution_mode=ExecutionMode.SIMULATED,
        correlation=CorrelationContext(
            request_id=UUID("00000000-0000-0000-0000-000000000001"),
            correlation_id=UUID("00000000-0000-0000-0000-000000000002"),
        ),
        provenance=_provenance(),
    )


def _capability(capability: StrategyCapability) -> CapabilityRequirement:
    return CapabilityRequirement(
        capability=capability,
        authorization_decision_ref=f"decision:{capability.value}",
    )


def test_existing_catalog_payload_remains_readable_with_additive_defaults() -> None:
    entry = StrategyCatalogEntry(
        strategy_version="strategy:v1",
        display_name="Baseline",
        description="Existing v1 summary payload",
        kind=StrategyKind.DIRECTIONAL,
        allowed_execution_modes=(ExecutionMode.DRY_RUN,),
        runtime_status=StrategyRuntimeStatus.PORTAL_CONFIG_ONLY,
    )

    assert entry.lifecycle_state == StrategyLifecycleState.DRAFT
    assert entry.current_revision == 1
    assert entry.required_capabilities == ()
    assert entry.immutable is True


def test_context_fails_closed_without_actor_or_target() -> None:
    payload = _context().model_dump(mode="python")
    payload.pop("actor_id")

    with pytest.raises(ValidationError):
        ClosureRequestContext.model_validate(payload)


def test_public_provenance_rejects_secret_bearing_metadata() -> None:
    with pytest.raises(ValidationError, match="sensitive metadata key"):
        _provenance(metadata={"api_token": "must-not-serialize"})


def test_signal_wizard_preview_is_idempotent_research_only_contract() -> None:
    command = SignalWizardPreviewCommand(
        context=_context(),
        idempotency_key="preview:tenant-1:1",
        strategy_id="strategy-1",
        feature_selections=(SignalWizardFeatureSelection(feature_id="rsi.v1", timeframe="5m"),),
        condition_ast={"all": [{"feature": "rsi.v1", "op": "gt", "value": 50}]},
        capability=_capability(StrategyCapability.STRATEGY_RESEARCH),
    )

    assert command.context.authority == "research_only"
    assert command.canonical_json() == command.model_copy().canonical_json()

    with pytest.raises(ValidationError, match=r"strategy\.research"):
        SignalWizardPreviewCommand.model_validate(
            {
                **command.model_dump(mode="python"),
                "capability": _capability(StrategyCapability.STRATEGY_APPROVE),
            }
        )


def test_preview_and_submit_cannot_grant_execution_or_promotion() -> None:
    result = SignalWizardPreviewResult(
        context=_context(),
        idempotency_key="preview:tenant-1:1",
        strategy_definition={"schema_version": "2.0.0", "strategy_id": "strategy-1"},
        preview_hash=HASH,
    )
    assert result.execution_authority is False
    assert result.promotion_authority is False

    with pytest.raises(ValidationError):
        SignalWizardPreviewResult.model_validate(
            {**result.model_dump(mode="python"), "execution_authority": True}
        )

    submit = SignalWizardSubmitCommand(
        context=_context(),
        idempotency_key="submit:tenant-1:1",
        preview_hash=HASH,
        experiment_name="research experiment",
        expected_strategy_version="strategy:v2",
        capability=_capability(StrategyCapability.EXPERIMENT_SUBMIT),
    )
    assert submit.capability.enforced is True


def test_catalog_commands_require_explicit_capability_and_exclude_live_mode() -> None:
    deployment = StrategyDeploymentCommand(
        context=_context(),
        idempotency_key="deploy:tenant-1:1",
        strategy_version="strategy:v2",
        mode=StrategyDeploymentMode.SHADOW,
        capability=_capability(StrategyCapability.STRATEGY_DEPLOY_DRY_RUN),
        approval_evidence_ref="approval:1",
    )
    assert deployment.mode == StrategyDeploymentMode.SHADOW

    with pytest.raises(ValidationError):
        StrategyDeploymentCommand.model_validate(
            {**deployment.model_dump(mode="python"), "mode": "LIVE"}
        )

    with pytest.raises(ValidationError, match="rollback target"):
        StrategyRollbackCommand(
            context=_context(),
            idempotency_key="rollback:tenant-1:1",
            from_strategy_version="strategy:v2",
            to_strategy_version="strategy:v2",
            reason="test",
            capability=_capability(StrategyCapability.STRATEGY_ROLLBACK_DRY_RUN),
        )
