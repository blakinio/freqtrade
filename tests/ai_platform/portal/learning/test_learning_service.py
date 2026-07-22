from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from ai_platform.portal.contracts.identity import ActorType
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory, build_engine, build_session_factory
from ai_platform.portal.intelligence.schema import InsightSeverity, TradeInsight
from ai_platform.portal.learning.database import create_learning_schema
from ai_platform.portal.learning.schema import AutonomyLevel, EvidenceWindow, ExperimentOutcome
from ai_platform.portal.learning.service import LearningService, LearningWorkflowConflictError
from ai_platform.portal.security.authorization import PermissionDeniedError


NOW = datetime(2026, 7, 22, 20, 0, tzinfo=UTC)


@pytest.fixture
def session_factory() -> SessionFactory:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    create_learning_schema(engine)
    return build_session_factory(engine)


def _context(tenant_id: str = "tenant-a") -> RequestContext:
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=f"agent-{tenant_id}",
        actor_type=ActorType.AGENT,
        permissions=(),
        request_id=uuid4(),
        correlation_id=uuid4(),
    )


def _insight(tenant_id: str = "tenant-a") -> TradeInsight:
    return TradeInsight(
        insight_id=uuid4(),
        tenant_id=tenant_id,
        diagnosis_id=uuid4(),
        severity=InsightSeverity.ATTENTION,
        summary="Review loss cluster under current volatility regime.",
        synthesis_source="DETERMINISTIC",
        evidence_links=("decision-snapshot:1", "trade:1"),
        created_at=NOW,
    )


def test_insight_to_hypothesis_to_positive_experiment_to_candidate(
    session_factory: SessionFactory,
) -> None:
    service = LearningService(session_factory, clock=lambda: NOW)
    context = _context()
    hypothesis = service.create_hypothesis(context, _insight(), "Test volatility-aware feature set")
    experiment = service.record_experiment(
        context,
        hypothesis_id=str(hypothesis.hypothesis_id),
        evidence_window=EvidenceWindow(
            start_at=datetime(2026, 5, 1, tzinfo=UTC),
            end_at=datetime(2026, 6, 1, tzinfo=UTC),
        ),
        autonomy_level=AutonomyLevel.L3_EXECUTE_RESEARCH,
        outcome=ExperimentOutcome.POSITIVE,
        result_summary="Candidate improved declared offline metric on the allowed evidence window.",
    )
    candidate = service.register_candidate(
        context,
        experiment_id=str(experiment.experiment_id),
        model_family_id="family-1",
        candidate_model_version_id="candidate-v2",
        dataset_version_id="dataset-v2",
        feature_schema_version_id="features-v2",
    )

    history = service.history(context, str(hypothesis.hypothesis_id))
    assert history.hypothesis.source_insight_id == hypothesis.source_insight_id
    assert history.experiments == (experiment,)
    assert history.candidates == (candidate,)
    assert candidate.promoted is False
    assert candidate.assigned_to_bot is False


def test_protected_final_holdout_cannot_be_used_iteratively(
    session_factory: SessionFactory,
) -> None:
    service = LearningService(session_factory)
    context = _context()
    hypothesis = service.create_hypothesis(context, _insight(), "Do not touch holdout")

    with pytest.raises(LearningWorkflowConflictError, match="protected final holdout v2"):
        service.record_experiment(
            context,
            hypothesis_id=str(hypothesis.hypothesis_id),
            evidence_window=EvidenceWindow(
                start_at=datetime(2026, 8, 15, tzinfo=UTC),
                end_at=datetime(2026, 9, 15, tzinfo=UTC),
            ),
            autonomy_level=AutonomyLevel.L3_EXECUTE_RESEARCH,
            outcome=ExperimentOutcome.PENDING,
            result_summary="Forbidden iterative window.",
        )


def test_negative_experiment_remains_durable_and_cannot_create_candidate(
    session_factory: SessionFactory,
) -> None:
    service = LearningService(session_factory)
    context = _context()
    hypothesis = service.create_hypothesis(context, _insight(), "Negative evidence matters")
    experiment = service.record_experiment(
        context,
        hypothesis_id=str(hypothesis.hypothesis_id),
        evidence_window=EvidenceWindow(
            start_at=datetime(2026, 4, 1, tzinfo=UTC),
            end_at=datetime(2026, 5, 1, tzinfo=UTC),
        ),
        autonomy_level=AutonomyLevel.L3_EXECUTE_RESEARCH,
        outcome=ExperimentOutcome.NEGATIVE,
        result_summary="No improvement; retain negative result.",
    )

    with pytest.raises(LearningWorkflowConflictError, match="positive experiment"):
        service.register_candidate(
            context,
            experiment_id=str(experiment.experiment_id),
            model_family_id="family-1",
            candidate_model_version_id="candidate-bad",
            dataset_version_id="dataset-v2",
            feature_schema_version_id="features-v2",
        )
    history = service.history(context, str(hypothesis.hypothesis_id))
    assert history.experiments[0].outcome is ExperimentOutcome.NEGATIVE
    assert history.candidates == ()


def test_candidate_registration_cannot_escalate_beyond_bounded_l4(
    session_factory: SessionFactory,
) -> None:
    service = LearningService(session_factory)
    context = _context()
    hypothesis = service.create_hypothesis(context, _insight(), "Bound autonomy")
    experiment = service.record_experiment(
        context,
        hypothesis_id=str(hypothesis.hypothesis_id),
        evidence_window=EvidenceWindow(
            start_at=datetime(2026, 1, 1, tzinfo=UTC),
            end_at=datetime(2026, 2, 1, tzinfo=UTC),
        ),
        autonomy_level=AutonomyLevel.L3_EXECUTE_RESEARCH,
        outcome=ExperimentOutcome.POSITIVE,
        result_summary="Positive research result.",
    )

    with pytest.raises(LearningWorkflowConflictError, match="bounded L4"):
        service.register_candidate(
            context,
            experiment_id=str(experiment.experiment_id),
            model_family_id="family-1",
            candidate_model_version_id="candidate-v2",
            dataset_version_id="dataset-v2",
            feature_schema_version_id="features-v2",
            autonomy_level=AutonomyLevel.L3_EXECUTE_RESEARCH,
        )


def test_cross_tenant_insight_cannot_seed_learning_workflow(
    session_factory: SessionFactory,
) -> None:
    service = LearningService(session_factory)

    with pytest.raises(PermissionDeniedError, match="tenant scope mismatch"):
        service.create_hypothesis(_context("tenant-b"), _insight("tenant-a"), "Cross tenant")
