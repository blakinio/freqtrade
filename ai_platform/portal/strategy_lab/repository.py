from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.strategy_lab.models import StrategyLabExperimentRow
from ai_platform.portal.strategy_lab.schema import ExperimentResult, ExperimentSummary


class CorruptExperimentResultError(RuntimeError):
    pass


class StrategyLabRepository:
    def add(
        self,
        session: Session,
        result: ExperimentResult,
        *,
        idempotency_key: str,
        request_digest: str,
    ) -> None:
        session.add(
            StrategyLabExperimentRow(
                tenant_id=result.tenant_id,
                experiment_id=str(result.experiment_id),
                idempotency_key=idempotency_key,
                request_digest=request_digest,
                status=result.status.value,
                created_at=result.started_at,
                experiment_json=result.canonical_json(),
            )
        )

    def get(self, session: Session, tenant_id: str, experiment_id: str) -> ExperimentResult | None:
        row = session.get(StrategyLabExperimentRow, (tenant_id, experiment_id))
        return self._parse(row) if row else None

    def get_by_idempotency(
        self, session: Session, tenant_id: str, idempotency_key: str
    ) -> tuple[ExperimentResult, str] | None:
        row = session.scalar(
            select(StrategyLabExperimentRow).where(
                StrategyLabExperimentRow.tenant_id == tenant_id,
                StrategyLabExperimentRow.idempotency_key == idempotency_key,
            )
        )
        return (self._parse(row), row.request_digest) if row else None

    def list(
        self,
        session: Session,
        tenant_id: str,
        *,
        offset: int,
        limit: int,
    ) -> tuple[ExperimentSummary, ...]:
        rows = session.scalars(
            select(StrategyLabExperimentRow)
            .where(StrategyLabExperimentRow.tenant_id == tenant_id)
            .order_by(
                StrategyLabExperimentRow.created_at.desc(),
                StrategyLabExperimentRow.experiment_id.desc(),
            )
            .offset(offset)
            .limit(limit)
        ).all()
        return tuple(_summary(self._parse(row)) for row in rows)

    @staticmethod
    def _parse(row: StrategyLabExperimentRow) -> ExperimentResult:
        try:
            return ExperimentResult.model_validate_json(row.experiment_json)
        except (ValidationError, ValueError) as exc:
            raise CorruptExperimentResultError(
                f"corrupt experiment result: {row.experiment_id}"
            ) from exc


def _summary(result: ExperimentResult) -> ExperimentSummary:
    return ExperimentSummary(
        experiment_id=result.experiment_id,
        status=result.status,
        strategy_id=result.strategy_id,
        strategy_version=result.strategy_version,
        pair=result.pair,
        timeframe=result.timeframe,
        started_at=result.started_at,
        trade_count=result.trade_count,
        profit_abs=result.profit_abs,
        profit_pct=result.profit_pct,
        max_drawdown=result.max_drawdown,
    )
