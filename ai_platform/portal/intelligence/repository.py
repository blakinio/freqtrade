from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.intelligence.models import (
    DecisionSnapshotRow,
    TradeAnalysisRow,
    TradeOutcomeRow,
)
from ai_platform.portal.intelligence.schema import DecisionSnapshot, TradeAnalysis, TradeOutcome


class TradeIntelligenceRepository:
    def add_snapshot(self, session: Session, snapshot: DecisionSnapshot) -> None:
        session.add(
            DecisionSnapshotRow(
                tenant_id=snapshot.tenant_id,
                snapshot_id=str(snapshot.snapshot_id),
                bot_id=snapshot.bot_id,
                trade_intent_id=str(snapshot.trade_intent_id),
                decision_at=snapshot.decision_at,
                snapshot_json=snapshot.canonical_json(),
            )
        )

    def get_snapshot(
        self,
        session: Session,
        tenant_id: str,
        snapshot_id: str,
    ) -> DecisionSnapshot | None:
        row = session.get(DecisionSnapshotRow, (tenant_id, snapshot_id))
        return DecisionSnapshot.model_validate_json(row.snapshot_json) if row is not None else None

    def add_outcome(self, session: Session, outcome: TradeOutcome) -> None:
        session.add(
            TradeOutcomeRow(
                tenant_id=outcome.tenant_id,
                outcome_id=str(outcome.outcome_id),
                trade_id=outcome.trade_id,
                bot_id=outcome.bot_id,
                closed_at=outcome.closed_at,
                outcome_json=outcome.canonical_json(),
            )
        )

    def get_outcome(
        self,
        session: Session,
        tenant_id: str,
        outcome_id: str,
    ) -> TradeOutcome | None:
        row = session.get(TradeOutcomeRow, (tenant_id, outcome_id))
        return TradeOutcome.model_validate_json(row.outcome_json) if row is not None else None

    def add_analysis(self, session: Session, analysis: TradeAnalysis) -> None:
        session.add(
            TradeAnalysisRow(
                tenant_id=analysis.tenant_id,
                analysis_id=str(analysis.analysis_id),
                snapshot_id=str(analysis.snapshot.snapshot_id),
                outcome_id=str(analysis.outcome.outcome_id),
                diagnosis_code=analysis.diagnosis.code.value,
                created_at=analysis.created_at,
                analysis_json=analysis.canonical_json(),
            )
        )

    def get_analysis(
        self,
        session: Session,
        tenant_id: str,
        analysis_id: str,
    ) -> TradeAnalysis | None:
        row = session.get(TradeAnalysisRow, (tenant_id, analysis_id))
        return TradeAnalysis.model_validate_json(row.analysis_json) if row is not None else None

    def list_analyses(self, session: Session, tenant_id: str) -> tuple[TradeAnalysis, ...]:
        rows = session.scalars(
            select(TradeAnalysisRow)
            .where(TradeAnalysisRow.tenant_id == tenant_id)
            .order_by(TradeAnalysisRow.created_at, TradeAnalysisRow.analysis_id)
        ).all()
        return tuple(TradeAnalysis.model_validate_json(row.analysis_json) for row in rows)
