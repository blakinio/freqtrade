from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import cast
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ai_platform.portal.contracts.identity import ActorType, Permission, RoleName
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.control_plane.api_core import create_app
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    build_engine,
    build_session_factory,
    create_schema,
)
from ai_platform.portal.intelligence.schema import (
    DecisionSnapshot,
    InsightSeverity,
    ReconciliationStatus,
    TradeInsight,
    TradeOutcome,
)
from ai_platform.portal.intelligence.service import TradeIntelligenceService
from ai_platform.portal.learning.schema import AutonomyLevel, EvidenceWindow, ExperimentOutcome
from ai_platform.portal.learning.service import LearningService
from ai_platform.portal.security.authorization import (
    PermissionDeniedError,
    builtin_role,
)


def context(
    *,
    actor_type: ActorType = ActorType.USER,
    permissions: tuple[Permission, ...] = (),
    tenant_id: str = "tenant-a",
) -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"{actor_type.value}-a",
        actor_type=actor_type,
        permissions=permissions,
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def in_memory_services() -> tuple[TradeIntelligenceService, LearningService]:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = build_session_factory(engine)
    return TradeIntelligenceService(session_factory), LearningService(session_factory)


def never_session():
    raise AssertionError("authorization must run before repository access")


@pytest.mark.parametrize(
    "role_name,expected_read,expected_train",
    [
        (RoleName.USER, True, False),
        (RoleName.TRADER, True, False),
        (RoleName.ANALYST, True, True),
        (RoleName.MODEL_REVIEWER, True, False),
        (RoleName.ADMIN, True, True),
        (RoleName.SERVICE, False, False),
    ],
)
def test_builtin_role_matrix_matches_ai_learning_policy(
    role_name: RoleName,
    expected_read: bool,
    expected_train: bool,
) -> None:
    permissions = set(builtin_role("tenant-a", role_name).permissions)
    assert (Permission.MODEL_READ in permissions) is expected_read
    assert (Permission.MODEL_TRAIN in permissions) is expected_train


def test_read_methods_deny_before_repository_access() -> None:
    denied = context(permissions=(Permission.BOT_READ,))
    intelligence = TradeIntelligenceService(never_session)
    learning = LearningService(never_session)

    with pytest.raises(PermissionDeniedError, match=r"model\.read"):
        intelligence.get_analysis(denied, "analysis-secret")
    with pytest.raises(PermissionDeniedError, match=r"model\.read"):
        intelligence.list_analyses(denied)
    with pytest.raises(PermissionDeniedError, match=r"model\.read"):
        learning.history(denied, "hypothesis-secret")
    with pytest.raises(PermissionDeniedError, match=r"model\.read"):
        learning.history_all(denied)


def test_learning_writes_deny_before_argument_or_repository_inspection() -> None:
    denied = context(permissions=(Permission.MODEL_READ,))
    service = LearningService(never_session)

    with pytest.raises(PermissionDeniedError, match=r"model\.train"):
        service.create_hypothesis(denied, cast(TradeInsight, object()), "statement")
    with pytest.raises(PermissionDeniedError, match=r"model\.train"):
        service.record_experiment(
            denied,
            hypothesis_id="hypothesis-secret",
            evidence_window=cast(EvidenceWindow, object()),
            autonomy_level=AutonomyLevel.L3_EXECUTE_RESEARCH,
            outcome=ExperimentOutcome.POSITIVE,
            result_summary="result",
        )
    with pytest.raises(PermissionDeniedError, match=r"model\.train"):
        service.register_candidate(
            denied,
            experiment_id="experiment-secret",
            model_family_id="family-a",
            candidate_model_version_id="candidate-a",
            dataset_version_id="dataset-a",
            feature_schema_version_id="feature-a",
        )


def test_trade_intelligence_producer_requires_service_actor_and_model_train() -> None:
    service = TradeIntelligenceService(never_session)
    user_trainer = context(permissions=(Permission.MODEL_TRAIN,))
    unscoped_service = context(actor_type=ActorType.SERVICE, permissions=(Permission.BOT_READ,))

    for producer in (user_trainer, unscoped_service):
        with pytest.raises(PermissionDeniedError):
            service.record_decision_snapshot(producer, cast(DecisionSnapshot, object()))
        with pytest.raises(PermissionDeniedError):
            service.analyze_outcome(
                producer,
                snapshot_id="snapshot-secret",
                outcome=cast(TradeOutcome, object()),
            )


def test_trusted_service_can_produce_and_model_reader_can_read() -> None:
    intelligence, _learning = in_memory_services()
    produced_at = datetime(2026, 1, 2, 12, tzinfo=UTC)
    service_context = context(
        actor_type=ActorType.SERVICE,
        permissions=(Permission.MODEL_TRAIN,),
    )
    reader_context = context(permissions=(Permission.MODEL_READ,))
    snapshot = DecisionSnapshot(
        snapshot_id=uuid4(),
        tenant_id="tenant-a",
        bot_id="bot-a",
        trade_intent_id=uuid4(),
        risk_decision_id=uuid4(),
        config_revision=1,
        strategy_version="strategy-v1",
        model_version="model-v1",
        risk_policy_version="risk-v1",
        source_runtime_id="runtime-a",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount=Decimal("0.1"),
        decision_at=produced_at,
        evidence_ref="evidence://decision-a",
        evidence_sha256="a" * 64,
    )
    outcome = TradeOutcome(
        outcome_id=uuid4(),
        tenant_id="tenant-a",
        trade_id="trade-a",
        bot_id="bot-a",
        source_runtime_id="runtime-a",
        pair="BTC/USDT",
        realized_pnl=Decimal("1.25"),
        fees=Decimal("0.01"),
        exit_reason="take-profit",
        opened_at=produced_at,
        closed_at=datetime(2026, 1, 2, 13, tzinfo=UTC),
        reconciliation_status=ReconciliationStatus.SYNCED,
    )

    intelligence.record_decision_snapshot(service_context, snapshot)
    analysis = intelligence.analyze_outcome(
        service_context,
        snapshot_id=str(snapshot.snapshot_id),
        outcome=outcome,
    )

    assert intelligence.get_analysis(reader_context, str(analysis.analysis_id)) == analysis
    assert intelligence.list_analyses(reader_context) == (analysis,)


def test_bounded_learning_actions_use_train_without_promotion() -> None:
    _intelligence, learning = in_memory_services()
    analyst = context(permissions=(Permission.MODEL_READ, Permission.MODEL_TRAIN))
    insight = TradeInsight(
        insight_id=uuid4(),
        tenant_id="tenant-a",
        diagnosis_id=uuid4(),
        severity=InsightSeverity.INFO,
        summary="bounded evidence",
        synthesis_source="DETERMINISTIC",
        evidence_links=("evidence://decision-a",),
        created_at=datetime(2026, 1, 2, 14, tzinfo=UTC),
    )
    hypothesis = learning.create_hypothesis(analyst, insight, "test bounded adjustment")
    experiment = learning.record_experiment(
        analyst,
        hypothesis_id=str(hypothesis.hypothesis_id),
        evidence_window=EvidenceWindow(
            start_at=datetime(2026, 1, 3, tzinfo=UTC),
            end_at=datetime(2026, 1, 10, tzinfo=UTC),
        ),
        autonomy_level=AutonomyLevel.L3_EXECUTE_RESEARCH,
        outcome=ExperimentOutcome.POSITIVE,
        result_summary="bounded evidence improved",
    )
    candidate = learning.register_candidate(
        analyst,
        experiment_id=str(experiment.experiment_id),
        model_family_id="family-a",
        candidate_model_version_id="candidate-a",
        dataset_version_id="dataset-a",
        feature_schema_version_id="feature-a",
    )

    assert candidate.promoted is False
    assert candidate.assigned_to_bot is False
    assert learning.history(analyst, str(hypothesis.hypothesis_id)).candidates == (candidate,)


@pytest.mark.parametrize(
    "path",
    ["/v1/trade-analysis", "/v1/insights", "/v1/learning/history"],
)
def test_public_ai_learning_routes_enforce_same_read_permission(path: str) -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_schema(engine)
    session_factory = build_session_factory(engine)

    denied_app = create_app(
        session_factory,
        identity_context_provider=lambda: context(
            actor_type=ActorType.SERVICE,
            permissions=(Permission.BOT_READ,),
        ),
    )
    denied = TestClient(denied_app).get(path)
    assert denied.status_code == 403
    assert denied.json() == {"detail": "permission denied: model.read"}

    allowed_app = create_app(
        session_factory,
        identity_context_provider=lambda: context(permissions=(Permission.MODEL_READ,)),
    )
    allowed = TestClient(allowed_app).get(path)
    assert allowed.status_code == 200
    assert allowed.json() == []
