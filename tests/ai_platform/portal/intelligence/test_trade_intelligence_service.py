from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.identity import ActorType
from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import (
    SessionFactory,
    build_engine,
    build_session_factory,
)
from ai_platform.portal.intelligence.database import create_intelligence_schema
from ai_platform.portal.intelligence.schema import (
    DecisionSnapshot,
    DiagnosisCode,
    ReconciliationStatus,
    TradeOutcome,
)
from ai_platform.portal.intelligence.service import (
    TradeIntelligenceConflictError,
    TradeIntelligenceService,
)
from ai_platform.portal.security.authorization import PermissionDeniedError


NOW = datetime(2026, 7, 22, 20, 0, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_intelligence_schema(engine)
    return build_session_factory(engine)


def _context(tenant_id: str = "tenant-a") -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"service-{tenant_id}",
        actor_type=ActorType.SERVICE,
        permissions=(),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _snapshot(tenant_id: str = "tenant-a") -> DecisionSnapshot:
    return DecisionSnapshot(
        snapshot_id=uuid4(),
        tenant_id=tenant_id,
        bot_id="bot-1",
        trade_intent_id=uuid4(),
        risk_decision_id=uuid4(),
        config_revision=1,
        strategy_version="strategy-v1",
        model_version="model-v1",
        risk_policy_version="risk-v1",
        source_runtime_id="runtime-1",
        pair="BTC/USDT",
        side=TradeSide.BUY,
        amount="0.01",
        decision_at=NOW,
        evidence_ref="decision-snapshots/tenant-a/snapshot-1.json",
        evidence_sha256="a" * 64,
    )


def _outcome(
    *,
    pnl: str = "-10",
    reconciled: ReconciliationStatus = ReconciliationStatus.SYNCED,
    exceeded: bool = False,
    tenant_id: str = "tenant-a",
) -> TradeOutcome:
    return TradeOutcome(
        outcome_id=uuid4(),
        tenant_id=tenant_id,
        trade_id="trade-1",
        bot_id="bot-1",
        source_runtime_id="runtime-1",
        pair="BTC/USDT",
        realized_pnl=pnl,
        fees="1",
        exit_reason="signal_exit",
        opened_at=NOW + timedelta(minutes=1),
        closed_at=NOW + timedelta(minutes=6),
        reconciliation_status=reconciled,
        loss_exceeded_risk_budget=exceeded,
    )


def test_loss_is_not_automatically_classified_as_model_error(
    session_factory: SessionFactory,
) -> None:
    service = TradeIntelligenceService(session_factory, clock=lambda: NOW + timedelta(minutes=10))
    context = _context()
    snapshot = service.record_decision_snapshot(context, _snapshot())

    analysis = service.analyze_outcome(
        context,
        snapshot_id=str(snapshot.snapshot_id),
        outcome=_outcome(pnl="-10", exceeded=False),
    )

    assert analysis.diagnosis.code is DiagnosisCode.LOSS_WITHIN_EXPECTED_RISK
    assert "not classified as a model error" in analysis.insight.summary
    assert analysis.insight.synthesis_source == "DETERMINISTIC"
    assert analysis.snapshot.decision_at < analysis.outcome.opened_at


def test_risk_budget_breach_requires_review_without_claiming_model_causality(
    session_factory: SessionFactory,
) -> None:
    service = TradeIntelligenceService(session_factory, clock=lambda: NOW + timedelta(minutes=10))
    context = _context()
    snapshot = service.record_decision_snapshot(context, _snapshot())

    analysis = service.analyze_outcome(
        context,
        snapshot_id=str(snapshot.snapshot_id),
        outcome=_outcome(pnl="-100", exceeded=True),
    )

    assert analysis.diagnosis.code is DiagnosisCode.LOSS_REQUIRES_REVIEW
    assert analysis.diagnosis.reason_codes == ("LOSS_EXCEEDED_RISK_BUDGET",)


def test_unreconciled_outcome_defers_causal_diagnosis(session_factory: SessionFactory) -> None:
    service = TradeIntelligenceService(session_factory, clock=lambda: NOW + timedelta(minutes=10))
    context = _context()
    snapshot = service.record_decision_snapshot(context, _snapshot())

    analysis = service.analyze_outcome(
        context,
        snapshot_id=str(snapshot.snapshot_id),
        outcome=_outcome(reconciled=ReconciliationStatus.MISMATCH),
    )

    assert analysis.diagnosis.code is DiagnosisCode.DATA_GAP
    assert analysis.insight.summary.startswith("Trade outcome is not fully reconciled")


class FailingSynthesizer:
    def synthesize(self, snapshot, outcome, diagnosis) -> str:
        del snapshot, outcome, diagnosis
        raise RuntimeError("external synthesis unavailable")


def test_ai_synthesis_failure_cannot_erase_deterministic_analysis(
    session_factory: SessionFactory,
) -> None:
    service = TradeIntelligenceService(session_factory, clock=lambda: NOW + timedelta(minutes=10))
    context = _context()
    snapshot = service.record_decision_snapshot(context, _snapshot())

    analysis = service.analyze_outcome(
        context,
        snapshot_id=str(snapshot.snapshot_id),
        outcome=_outcome(pnl="5"),
        synthesizer=FailingSynthesizer(),
    )

    assert analysis.diagnosis.code is DiagnosisCode.PROFITABLE
    assert analysis.insight.synthesis_source == "DETERMINISTIC_FALLBACK"
    assert service.get_analysis(context, str(analysis.analysis_id)) == analysis


def test_snapshot_identity_is_immutable_and_tenant_scoped(session_factory: SessionFactory) -> None:
    service = TradeIntelligenceService(session_factory)
    context = _context()
    snapshot = _snapshot()
    service.record_decision_snapshot(context, snapshot)

    with pytest.raises(TradeIntelligenceConflictError, match="already exists"):
        service.record_decision_snapshot(context, snapshot)
    with pytest.raises(PermissionDeniedError, match="tenant scope mismatch"):
        service.record_decision_snapshot(_context("tenant-b"), _snapshot("tenant-a"))
    assert service.list_analyses(_context("tenant-b")) == ()


def test_outcome_attribution_must_match_decision_snapshot(session_factory: SessionFactory) -> None:
    service = TradeIntelligenceService(session_factory)
    context = _context()
    snapshot = service.record_decision_snapshot(context, _snapshot())
    outcome = _outcome().model_copy(update={"bot_id": "other-bot"})

    with pytest.raises(TradeIntelligenceConflictError, match="outcome bot"):
        service.analyze_outcome(
            context,
            snapshot_id=str(snapshot.snapshot_id),
            outcome=outcome,
        )
