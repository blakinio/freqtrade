from __future__ import annotations

from datetime import UTC, datetime
from typing import get_type_hints
from uuid import uuid4

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts import (
    Actor,
    ApprovedExecutionIntent,
    AuditAction,
    AuditEvent,
    AuditResult,
    BotConfigRevision,
    BotInstance,
    BotSpec,
    DatasetVersion,
    Environment,
    EventEnvelope,
    EventType,
    ExchangeConnection,
    ExecutionAdapter,
    ExecutionHealth,
    ExperimentReference,
    FeatureSchemaVersion,
    ModelFamily,
    ModelLifecycleState,
    ModelParameter,
    ModelVersion,
    OpenPosition,
    OrderRecord,
    Organization,
    Prediction,
    RejectedExecutionIntent,
    RiskDecision,
    RiskDecisionOutcome,
    RiskLimitEvaluation,
    RiskPolicyVersion,
    Role,
    RuntimeStatus,
    SecretKind,
    SecretRef,
    ServiceIdentity,
    Tenant,
    TradeIntent,
    TradeRecord,
    TradeSide,
    TrainingPipelineVersion,
    TrainingWindow,
    User,
)
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.identity import ActorType


NOW = datetime(2026, 7, 22, 8, 0, tzinfo=UTC)
HASH_A = "a" * 64


def _context() -> CorrelationContext:
    return CorrelationContext(
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
    )


def _bot_spec(**overrides: object) -> BotSpec:
    values: dict[str, object] = {
        "tenant_id": "tenant-1",
        "strategy_version": "strategy-v1",
        "model_version": "model-v1",
        "risk_policy_version": "risk-v1",
        "exchange_connection_ref": "exchange-1",
        "pair_universe": ("BTC/USDT",),
        "timeframe": "5m",
        "capital_allocation": "1000",
        "capital_currency": "USDT",
        "runtime_version": "freqtrade-2026.7",
        "config_revision": 1,
        "environment": Environment.TEST,
    }
    values.update(overrides)
    return BotSpec.model_validate(values)


def _model_version(**overrides: object) -> ModelVersion:
    values: dict[str, object] = {
        "model_version_id": "model-v1",
        "tenant_id": "tenant-1",
        "model_family_id": "family-1",
        "artifact_id": "artifact-1",
        "artifact_sha256": HASH_A,
        "feature_schema_version_id": "features-v1",
        "dataset_version_id": "dataset-v1",
        "training_window": TrainingWindow(
            start_at=datetime(2026, 1, 1, tzinfo=UTC),
            end_at=datetime(2026, 2, 1, tzinfo=UTC),
        ),
        "training_pipeline_version_id": "pipeline-v1",
        "parameters": (ModelParameter(name="learning_rate", value_json="0.05"),),
        "git_revision": "abc123",
        "created_at": NOW,
        "lifecycle_state": ModelLifecycleState.CANDIDATE,
    }
    values.update(overrides)
    return ModelVersion.model_validate(values)


def _trade_intent(context: CorrelationContext) -> TradeIntent:
    return TradeIntent(
        trade_intent_id=uuid4(),
        tenant_id="tenant-1",
        bot_id="bot-1",
        source_actor_id="actor-1",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount="0.01",
        environment=Environment.TEST,
        created_at=NOW,
        context=context,
    )


def _risk_decision(
    trade_intent: TradeIntent,
    context: CorrelationContext,
    outcome: RiskDecisionOutcome,
) -> RiskDecision:
    reason_code = "within_limits" if outcome is RiskDecisionOutcome.APPROVED else "limit_exceeded"
    return RiskDecision(
        risk_decision_id=uuid4(),
        tenant_id=trade_intent.tenant_id,
        trade_intent_id=trade_intent.trade_intent_id,
        risk_policy_version="risk-v1",
        decision=outcome,
        reason_codes=(reason_code,),
        evaluated_limits=(
            RiskLimitEvaluation(
                limit_name="max_exposure",
                configured_value="1000",
                observed_value="100",
                passed=outcome is RiskDecisionOutcome.APPROVED,
            ),
        ),
        occurred_at=NOW,
        context=context,
    )


def test_tenant_owned_contracts_require_explicit_tenant_id() -> None:
    tenant_owned_models = (
        Tenant,
        Organization,
        User,
        Actor,
        ServiceIdentity,
        Role,
        SecretRef,
        ExchangeConnection,
        BotSpec,
        BotConfigRevision,
        BotInstance,
        ModelFamily,
        FeatureSchemaVersion,
        DatasetVersion,
        TrainingPipelineVersion,
        ExperimentReference,
        ModelVersion,
        RiskPolicyVersion,
        Prediction,
        TradeIntent,
        RiskDecision,
        ApprovedExecutionIntent,
        RejectedExecutionIntent,
        EventEnvelope,
        AuditEvent,
        RuntimeStatus,
        ExecutionHealth,
        OpenPosition,
        OrderRecord,
        TradeRecord,
    )

    for model in tenant_owned_models:
        assert "tenant_id" in model.model_fields, model.__name__
        assert model.model_fields["tenant_id"].is_required(), model.__name__


def test_unknown_model_lifecycle_state_is_rejected() -> None:
    with pytest.raises(ValidationError):
        _model_version(lifecycle_state="UNKNOWN")


def test_version_identity_is_immutable() -> None:
    model = _model_version()

    with pytest.raises(ValidationError):
        model.model_version_id = "model-v2"


def test_bot_spec_requires_nonempty_version_references_and_positive_revision() -> None:
    with pytest.raises(ValidationError):
        _bot_spec(model_version="")
    with pytest.raises(ValidationError):
        _bot_spec(config_revision=0)


def test_production_exchange_connection_rejects_research_secret_reference() -> None:
    secret_ref = SecretRef(
        provider="vault",
        reference_id="ref-1",
        version="1",
        environment=Environment.RESEARCH,
        tenant_id="tenant-1",
        kind=SecretKind.EXCHANGE_CREDENTIAL,
    )

    with pytest.raises(ValidationError, match="environment"):
        ExchangeConnection(
            exchange_connection_id="exchange-1",
            tenant_id="tenant-1",
            name="prod-exchange",
            environment=Environment.PRODUCTION,
            exchange_id="kraken",
            secret_ref=secret_ref,
        )


@pytest.mark.parametrize(
    "field_name",
    ("api" + "_key", "api" + "_secret", "pass" + "phrase"),
)
def test_exchange_connection_rejects_raw_secret_fields(field_name: str) -> None:
    secret_ref = SecretRef(
        provider="vault",
        reference_id="ref-1",
        version="1",
        environment=Environment.TEST,
        tenant_id="tenant-1",
        kind=SecretKind.EXCHANGE_CREDENTIAL,
    )
    payload = {
        "exchange_connection_id": "exchange-1",
        "tenant_id": "tenant-1",
        "name": "test-exchange",
        "environment": Environment.TEST,
        "exchange_id": "kraken",
        "secret_ref": secret_ref,
        field_name: "redacted",
    }

    with pytest.raises(ValidationError, match="extra_forbidden"):
        ExchangeConnection.model_validate(payload)


def test_exchange_connection_forbids_withdrawal_enabled_credentials() -> None:
    secret_ref = SecretRef(
        provider="vault",
        reference_id="ref-1",
        version="1",
        environment=Environment.TEST,
        tenant_id="tenant-1",
        kind=SecretKind.EXCHANGE_CREDENTIAL,
    )

    with pytest.raises(ValidationError):
        ExchangeConnection(
            exchange_connection_id="exchange-1",
            tenant_id="tenant-1",
            name="test-exchange",
            environment=Environment.TEST,
            exchange_id="kraken",
            secret_ref=secret_ref,
            withdrawal_enabled=True,
        )


def test_execution_adapter_accepts_only_approved_execution_intent() -> None:
    hints = get_type_hints(ExecutionAdapter.submit_approved_intent)
    assert hints["intent"] is ApprovedExecutionIntent


def test_trade_intent_cannot_become_execution_intent_without_risk_decision() -> None:
    context = _context()
    trade_intent = _trade_intent(context)

    with pytest.raises(ValidationError):
        ApprovedExecutionIntent(
            execution_intent_id=uuid4(),
            tenant_id="tenant-1",
            trade_intent=trade_intent,
            created_at=NOW,
            context=context,
        )


def test_risk_decision_requires_policy_version() -> None:
    context = _context()
    trade_intent = _trade_intent(context)
    payload = _risk_decision(trade_intent, context, RiskDecisionOutcome.APPROVED).model_dump()
    del payload["risk_policy_version"]

    with pytest.raises(ValidationError):
        RiskDecision.model_validate(payload)


def test_rejected_risk_decision_cannot_construct_approved_execution_intent() -> None:
    context = _context()
    trade_intent = _trade_intent(context)
    risk_decision = _risk_decision(trade_intent, context, RiskDecisionOutcome.REJECTED)

    with pytest.raises(ValidationError, match="approved risk decision"):
        ApprovedExecutionIntent(
            execution_intent_id=uuid4(),
            tenant_id="tenant-1",
            trade_intent=trade_intent,
            risk_decision=risk_decision,
            created_at=NOW,
            context=context,
        )


def test_correlation_id_propagates_across_intent_risk_and_execution() -> None:
    context = _context()
    trade_intent = _trade_intent(context)
    risk_decision = _risk_decision(trade_intent, context, RiskDecisionOutcome.APPROVED)
    approved = ApprovedExecutionIntent(
        execution_intent_id=uuid4(),
        tenant_id="tenant-1",
        trade_intent=trade_intent,
        risk_decision=risk_decision,
        created_at=NOW,
        context=context,
    )

    assert approved.context.correlation_id == trade_intent.context.correlation_id
    assert approved.context.correlation_id == risk_decision.context.correlation_id


def test_event_envelope_requires_event_version() -> None:
    payload = {
        "event_id": uuid4(),
        "event_type": EventType.BOT_CREATED,
        "occurred_at": NOW,
        "tenant_id": "tenant-1",
        "actor_id": "actor-1",
        "request_id": uuid4(),
        "correlation_id": uuid4(),
        "aggregate_type": "bot",
        "aggregate_id": "bot-1",
        "payload": {},
    }

    with pytest.raises(ValidationError):
        EventEnvelope.model_validate(payload)


def test_event_payload_rejects_sensitive_value_fields() -> None:
    field_name = "api" + "_key"

    with pytest.raises(ValidationError, match="sensitive payload field"):
        EventEnvelope(
            event_id=uuid4(),
            event_type=EventType.BOT_CREATED,
            event_version=1,
            occurred_at=NOW,
            tenant_id="tenant-1",
            actor_id="actor-1",
            request_id=uuid4(),
            correlation_id=uuid4(),
            aggregate_type="bot",
            aggregate_id="bot-1",
            payload={field_name: "redacted"},
        )


def test_audit_event_contains_required_accountability_fields() -> None:
    event = AuditEvent(
        audit_id=uuid4(),
        occurred_at=NOW,
        actor_type=ActorType.USER,
        actor_id="actor-1",
        tenant_id="tenant-1",
        resource_type="bot",
        resource_id="bot-1",
        action=AuditAction.BOT_STARTED,
        result=AuditResult.SUCCEEDED,
        request_id=uuid4(),
        correlation_id=uuid4(),
    )

    assert event.actor_id == "actor-1"
    assert event.tenant_id == "tenant-1"
    assert event.resource_type == "bot"
    assert event.resource_id == "bot-1"
    assert event.action is AuditAction.BOT_STARTED
    assert event.result is AuditResult.SUCCEEDED
    assert event.correlation_id is not None


def test_audit_details_reject_sensitive_value_fields() -> None:
    field_name = "session" + "_token"

    with pytest.raises(ValidationError, match="sensitive payload field"):
        AuditEvent(
            audit_id=uuid4(),
            occurred_at=NOW,
            actor_type=ActorType.USER,
            actor_id="actor-1",
            tenant_id="tenant-1",
            resource_type="exchange_connection",
            resource_id="exchange-1",
            action=AuditAction.EXCHANGE_CONNECTION_CHANGED,
            result=AuditResult.SUCCEEDED,
            request_id=uuid4(),
            correlation_id=uuid4(),
            details={field_name: "redacted"},
        )


def test_serialization_roundtrip_is_deterministic() -> None:
    event = EventEnvelope(
        event_id=uuid4(),
        event_type=EventType.MODEL_REGISTERED,
        event_version=1,
        occurred_at=NOW,
        tenant_id="tenant-1",
        actor_id="actor-1",
        request_id=uuid4(),
        correlation_id=uuid4(),
        causation_id=uuid4(),
        aggregate_type="model",
        aggregate_id="model-v1",
        payload={"z": 1, "a": {"y": 2, "b": 3}},
    )

    first = event.canonical_json()
    second = event.canonical_json()
    restored = EventEnvelope.model_validate_json(first)

    assert first == second
    assert restored == event
    assert restored.canonical_json() == first


def test_representative_json_schema_keeps_version_fields() -> None:
    schema = EventEnvelope.model_json_schema()

    assert schema["properties"]["contract_version"]["default"] == "v1"
    assert "event_version" in schema["required"]
    assert "tenant_id" in schema["required"]
    assert "correlation_id" in schema["required"]


def test_naive_business_timestamp_is_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        TrainingWindow(
            start_at=datetime(2026, 1, 1),
            end_at=datetime(2026, 2, 1, tzinfo=UTC),
        )
