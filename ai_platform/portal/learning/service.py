from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.intelligence.schema import TradeInsight
from ai_platform.portal.learning.repository import LearningRepository
from ai_platform.portal.learning.schema import (
    AutonomyLevel,
    EvidenceWindow,
    ExperimentOutcome,
    LearningCandidate,
    LearningExperiment,
    LearningHistoryEntry,
    LearningHypothesis,
)
from ai_platform.portal.security.authorization import PermissionDeniedError


FINAL_HOLDOUT_START = datetime(2026, 8, 1, tzinfo=UTC)
FINAL_HOLDOUT_END = datetime(2026, 10, 1, tzinfo=UTC)


class LearningWorkflowConflictError(RuntimeError):
    pass


class LearningWorkflowNotFoundError(LookupError):
    pass


Clock = Callable[[], datetime]


class LearningService:
    def __init__(
        self,
        session_factory: SessionFactory,
        repository: LearningRepository | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or LearningRepository()
        self._clock = clock or (lambda: datetime.now(UTC))

    def create_hypothesis(
        self,
        context: RequestContext,
        insight: TradeInsight,
        statement: str,
    ) -> LearningHypothesis:
        self._require_tenant(context, insight.tenant_id)
        hypothesis = LearningHypothesis(
            hypothesis_id=uuid4(),
            tenant_id=context.tenant_id,
            source_insight_id=insight.insight_id,
            statement=statement,
            evidence_links=insight.evidence_links,
            created_by_actor_id=context.actor_id,
            created_at=self._clock(),
        )
        with self._session_factory() as session, session.begin():
            self._repository.add_hypothesis(session, hypothesis)
        return hypothesis

    def record_experiment(
        self,
        context: RequestContext,
        *,
        hypothesis_id: str,
        evidence_window: EvidenceWindow,
        autonomy_level: AutonomyLevel,
        outcome: ExperimentOutcome,
        result_summary: str,
    ) -> LearningExperiment:
        self._validate_evidence_window(evidence_window)
        with self._session_factory() as session, session.begin():
            hypothesis = self._repository.get_hypothesis(
                session,
                context.tenant_id,
                hypothesis_id,
            )
            if hypothesis is None:
                raise LearningWorkflowNotFoundError("learning hypothesis not found")
            experiment = LearningExperiment(
                experiment_id=uuid4(),
                tenant_id=context.tenant_id,
                hypothesis_id=hypothesis.hypothesis_id,
                evidence_window=evidence_window,
                autonomy_level=autonomy_level,
                outcome=outcome,
                result_summary=result_summary,
                created_by_actor_id=context.actor_id,
                created_at=self._clock(),
            )
            self._repository.add_experiment(session, experiment)
        return experiment

    def register_candidate(
        self,
        context: RequestContext,
        *,
        experiment_id: str,
        model_family_id: str,
        candidate_model_version_id: str,
        dataset_version_id: str,
        feature_schema_version_id: str,
        autonomy_level: AutonomyLevel = AutonomyLevel.L4_BOUNDED_CANDIDATE,
    ) -> LearningCandidate:
        if autonomy_level is not AutonomyLevel.L4_BOUNDED_CANDIDATE:
            raise LearningWorkflowConflictError(
                "candidate registration requires bounded L4 autonomy authority"
            )
        with self._session_factory() as session, session.begin():
            experiment = self._repository.get_experiment(
                session,
                context.tenant_id,
                experiment_id,
            )
            if experiment is None:
                raise LearningWorkflowNotFoundError("learning experiment not found")
            if experiment.outcome is not ExperimentOutcome.POSITIVE:
                raise LearningWorkflowConflictError(
                    "only a positive experiment may register a learning candidate"
                )
            candidate = LearningCandidate(
                candidate_id=uuid4(),
                tenant_id=context.tenant_id,
                experiment_id=experiment.experiment_id,
                model_family_id=model_family_id,
                candidate_model_version_id=candidate_model_version_id,
                dataset_version_id=dataset_version_id,
                feature_schema_version_id=feature_schema_version_id,
                autonomy_level=autonomy_level,
                promoted=False,
                assigned_to_bot=False,
                created_by_actor_id=context.actor_id,
                created_at=self._clock(),
            )
            self._repository.add_candidate(session, candidate)
        return candidate

    def history(self, context: RequestContext, hypothesis_id: str) -> LearningHistoryEntry:
        with self._session_factory() as session:
            hypothesis = self._repository.get_hypothesis(
                session,
                context.tenant_id,
                hypothesis_id,
            )
            if hypothesis is None:
                raise LearningWorkflowNotFoundError("learning hypothesis not found")
            experiments = self._repository.list_experiments(
                session,
                context.tenant_id,
                hypothesis_id,
            )
            candidates = tuple(
                candidate
                for experiment in experiments
                for candidate in self._repository.list_candidates(
                    session,
                    context.tenant_id,
                    str(experiment.experiment_id),
                )
            )
        return LearningHistoryEntry(
            hypothesis=hypothesis,
            experiments=experiments,
            candidates=candidates,
        )

    @staticmethod
    def _validate_evidence_window(window: EvidenceWindow) -> None:
        if window.end_at <= window.start_at:
            raise LearningWorkflowConflictError("evidence window end must be after start")
        if window.start_at < FINAL_HOLDOUT_END and window.end_at > FINAL_HOLDOUT_START:
            raise LearningWorkflowConflictError(
                "iterative learning evidence window overlaps protected final holdout v2"
            )

    @staticmethod
    def _require_tenant(context: RequestContext, tenant_id: str) -> None:
        if context.tenant_id != tenant_id:
            raise PermissionDeniedError("tenant scope mismatch")
