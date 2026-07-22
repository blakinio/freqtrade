from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform.portal.learning.models import (
    LearningCandidateRow,
    LearningExperimentRow,
    LearningHypothesisRow,
)
from ai_platform.portal.learning.schema import (
    LearningCandidate,
    LearningExperiment,
    LearningHypothesis,
)


class LearningRepository:
    def add_hypothesis(self, session: Session, hypothesis: LearningHypothesis) -> None:
        session.add(
            LearningHypothesisRow(
                tenant_id=hypothesis.tenant_id,
                hypothesis_id=str(hypothesis.hypothesis_id),
                source_insight_id=str(hypothesis.source_insight_id),
                created_at=hypothesis.created_at,
                hypothesis_json=hypothesis.canonical_json(),
            )
        )

    def get_hypothesis(
        self,
        session: Session,
        tenant_id: str,
        hypothesis_id: str,
    ) -> LearningHypothesis | None:
        row = session.get(LearningHypothesisRow, (tenant_id, hypothesis_id))
        return LearningHypothesis.model_validate_json(row.hypothesis_json) if row else None

    def add_experiment(self, session: Session, experiment: LearningExperiment) -> None:
        session.add(
            LearningExperimentRow(
                tenant_id=experiment.tenant_id,
                experiment_id=str(experiment.experiment_id),
                hypothesis_id=str(experiment.hypothesis_id),
                outcome=experiment.outcome.value,
                created_at=experiment.created_at,
                experiment_json=experiment.canonical_json(),
            )
        )

    def get_experiment(
        self,
        session: Session,
        tenant_id: str,
        experiment_id: str,
    ) -> LearningExperiment | None:
        row = session.get(LearningExperimentRow, (tenant_id, experiment_id))
        return LearningExperiment.model_validate_json(row.experiment_json) if row else None

    def list_experiments(
        self,
        session: Session,
        tenant_id: str,
        hypothesis_id: str,
    ) -> tuple[LearningExperiment, ...]:
        rows = session.scalars(
            select(LearningExperimentRow)
            .where(
                LearningExperimentRow.tenant_id == tenant_id,
                LearningExperimentRow.hypothesis_id == hypothesis_id,
            )
            .order_by(LearningExperimentRow.created_at, LearningExperimentRow.experiment_id)
        ).all()
        return tuple(LearningExperiment.model_validate_json(row.experiment_json) for row in rows)

    def add_candidate(self, session: Session, candidate: LearningCandidate) -> None:
        session.add(
            LearningCandidateRow(
                tenant_id=candidate.tenant_id,
                candidate_id=str(candidate.candidate_id),
                experiment_id=str(candidate.experiment_id),
                candidate_model_version_id=candidate.candidate_model_version_id,
                created_at=candidate.created_at,
                candidate_json=candidate.canonical_json(),
            )
        )

    def list_candidates(
        self,
        session: Session,
        tenant_id: str,
        experiment_id: str,
    ) -> tuple[LearningCandidate, ...]:
        rows = session.scalars(
            select(LearningCandidateRow)
            .where(
                LearningCandidateRow.tenant_id == tenant_id,
                LearningCandidateRow.experiment_id == experiment_id,
            )
            .order_by(LearningCandidateRow.created_at, LearningCandidateRow.candidate_id)
        ).all()
        return tuple(LearningCandidate.model_validate_json(row.candidate_json) for row in rows)
