from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.intelligence.repository import TradeIntelligenceRepository
from ai_platform.portal.intelligence.schema import (
    DecisionSnapshot,
    DeterministicDiagnosis,
    DiagnosisCode,
    InsightSeverity,
    ReconciliationStatus,
    TradeAnalysis,
    TradeInsight,
    TradeOutcome,
)
from ai_platform.portal.security.authorization import PermissionDeniedError


class DecisionSnapshotNotFoundError(LookupError):
    pass


class TradeIntelligenceConflictError(RuntimeError):
    pass


class InsightSynthesizer(Protocol):
    def synthesize(
        self,
        snapshot: DecisionSnapshot,
        outcome: TradeOutcome,
        diagnosis: DeterministicDiagnosis,
    ) -> str: ...


Clock = Callable[[], datetime]


class TradeIntelligenceService:
    def __init__(
        self,
        session_factory: SessionFactory,
        repository: TradeIntelligenceRepository | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or TradeIntelligenceRepository()
        self._clock = clock or (lambda: datetime.now(UTC))

    def record_decision_snapshot(
        self,
        context: RequestContext,
        snapshot: DecisionSnapshot,
    ) -> DecisionSnapshot:
        self._require_tenant(context, snapshot.tenant_id)
        try:
            with self._session_factory() as session, session.begin():
                if (
                    self._repository.get_snapshot(
                        session,
                        context.tenant_id,
                        str(snapshot.snapshot_id),
                    )
                    is not None
                ):
                    raise TradeIntelligenceConflictError("decision snapshot identity already exists")
                self._repository.add_snapshot(session, snapshot)
        except IntegrityError as exc:
            raise TradeIntelligenceConflictError("decision snapshot identity already exists") from exc
        return snapshot

    def analyze_outcome(
        self,
        context: RequestContext,
        *,
        snapshot_id: str,
        outcome: TradeOutcome,
        synthesizer: InsightSynthesizer | None = None,
    ) -> TradeAnalysis:
        self._require_tenant(context, outcome.tenant_id)
        occurred_at = self._clock()
        try:
            with self._session_factory() as session, session.begin():
                snapshot = self._repository.get_snapshot(session, context.tenant_id, snapshot_id)
                if snapshot is None:
                    raise DecisionSnapshotNotFoundError("decision snapshot not found")
                self._validate_attribution(snapshot, outcome)
                diagnosis = self._diagnose(snapshot, outcome, occurred_at)
                summary, source = self._synthesize(snapshot, outcome, diagnosis, synthesizer)
                insight = TradeInsight(
                    insight_id=uuid4(),
                    tenant_id=context.tenant_id,
                    diagnosis_id=diagnosis.diagnosis_id,
                    severity=self._severity(diagnosis.code),
                    summary=summary,
                    synthesis_source=source,
                    evidence_links=diagnosis.evidence_links,
                    created_at=occurred_at,
                )
                analysis = TradeAnalysis(
                    analysis_id=uuid4(),
                    tenant_id=context.tenant_id,
                    snapshot=snapshot,
                    outcome=outcome,
                    diagnosis=diagnosis,
                    insight=insight,
                    created_at=occurred_at,
                )
                self._repository.add_outcome(session, outcome)
                self._repository.add_analysis(session, analysis)
        except IntegrityError as exc:
            raise TradeIntelligenceConflictError("trade outcome or analysis identity already exists") from exc
        return analysis

    def get_analysis(self, context: RequestContext, analysis_id: str) -> TradeAnalysis:
        with self._session_factory() as session:
            analysis = self._repository.get_analysis(session, context.tenant_id, analysis_id)
        if analysis is None:
            raise DecisionSnapshotNotFoundError("trade analysis not found")
        return analysis

    def list_analyses(self, context: RequestContext) -> tuple[TradeAnalysis, ...]:
        with self._session_factory() as session:
            return self._repository.list_analyses(session, context.tenant_id)

    @staticmethod
    def _require_tenant(context: RequestContext, tenant_id: str) -> None:
        if tenant_id != context.tenant_id:
            raise PermissionDeniedError("tenant scope mismatch")

    @staticmethod
    def _validate_attribution(snapshot: DecisionSnapshot, outcome: TradeOutcome) -> None:
        if snapshot.bot_id != outcome.bot_id:
            raise TradeIntelligenceConflictError("outcome bot does not match decision snapshot")
        if snapshot.pair != outcome.pair:
            raise TradeIntelligenceConflictError("outcome pair does not match decision snapshot")
        if snapshot.source_runtime_id != outcome.source_runtime_id:
            raise TradeIntelligenceConflictError("outcome runtime does not match decision snapshot")
        if outcome.closed_at < outcome.opened_at:
            raise TradeIntelligenceConflictError("outcome closed_at precedes opened_at")

    @staticmethod
    def _diagnose(
        snapshot: DecisionSnapshot,
        outcome: TradeOutcome,
        occurred_at: datetime,
    ) -> DeterministicDiagnosis:
        if outcome.reconciliation_status is not ReconciliationStatus.SYNCED:
            code = DiagnosisCode.DATA_GAP
            reason_codes = (f"RECONCILIATION_{outcome.reconciliation_status.value}",)
        elif outcome.realized_pnl >= 0:
            code = DiagnosisCode.PROFITABLE
            reason_codes = ("REALIZED_PNL_NON_NEGATIVE",)
        elif outcome.loss_exceeded_risk_budget:
            code = DiagnosisCode.LOSS_REQUIRES_REVIEW
            reason_codes = ("LOSS_EXCEEDED_RISK_BUDGET",)
        else:
            code = DiagnosisCode.LOSS_WITHIN_EXPECTED_RISK
            reason_codes = ("LOSS_WITHIN_DECLARED_RISK",)
        return DeterministicDiagnosis(
            diagnosis_id=uuid4(),
            tenant_id=snapshot.tenant_id,
            snapshot_id=snapshot.snapshot_id,
            outcome_id=outcome.outcome_id,
            code=code,
            reason_codes=reason_codes,
            evidence_links=(snapshot.evidence_ref, f"trade:{outcome.trade_id}"),
            created_at=occurred_at,
        )

    @classmethod
    def _synthesize(
        cls,
        snapshot: DecisionSnapshot,
        outcome: TradeOutcome,
        diagnosis: DeterministicDiagnosis,
        synthesizer: InsightSynthesizer | None,
    ) -> tuple[str, str]:
        deterministic = cls._deterministic_summary(diagnosis)
        if synthesizer is None:
            return deterministic, "DETERMINISTIC"
        try:
            synthesized = synthesizer.synthesize(snapshot, outcome, diagnosis).strip()
        except Exception:
            return deterministic, "DETERMINISTIC_FALLBACK"
        if not synthesized:
            return deterministic, "DETERMINISTIC_FALLBACK"
        return f"{deterministic} {synthesized}", "AI_ASSISTED"

    @staticmethod
    def _deterministic_summary(diagnosis: DeterministicDiagnosis) -> str:
        summaries = {
            DiagnosisCode.PROFITABLE: "Trade closed with non-negative realized PNL.",
            DiagnosisCode.LOSS_WITHIN_EXPECTED_RISK: (
                "Trade closed at a loss without evidence that the declared risk budget was exceeded; "
                "this is not classified as a model error."
            ),
            DiagnosisCode.LOSS_REQUIRES_REVIEW: (
                "Trade loss exceeded the declared risk budget and requires evidence review."
            ),
            DiagnosisCode.DATA_GAP: (
                "Trade outcome is not fully reconciled; causal diagnosis is deferred until evidence is complete."
            ),
        }
        return summaries[diagnosis.code]

    @staticmethod
    def _severity(code: DiagnosisCode) -> InsightSeverity:
        if code in {DiagnosisCode.DATA_GAP, DiagnosisCode.LOSS_REQUIRES_REVIEW}:
            return InsightSeverity.ATTENTION
        return InsightSeverity.INFO
