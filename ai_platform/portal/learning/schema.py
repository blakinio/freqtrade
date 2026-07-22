from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime


class AutonomyLevel(StrEnum):
    L0_MANUAL = "L0"
    L1_ASSISTED = "L1"
    L2_PROPOSE = "L2"
    L3_EXECUTE_RESEARCH = "L3"
    L4_BOUNDED_CANDIDATE = "L4"


class ExperimentOutcome(StrEnum):
    PENDING = "PENDING"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    INCONCLUSIVE = "INCONCLUSIVE"


class EvidenceWindow(ContractModel):
    start_at: UtcDateTime
    end_at: UtcDateTime


class LearningHypothesis(ContractModel):
    hypothesis_id: UUID
    tenant_id: NonEmptyStr
    source_insight_id: UUID
    statement: NonEmptyStr
    evidence_links: tuple[NonEmptyStr, ...]
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime


class LearningExperiment(ContractModel):
    experiment_id: UUID
    tenant_id: NonEmptyStr
    hypothesis_id: UUID
    evidence_window: EvidenceWindow
    autonomy_level: AutonomyLevel
    outcome: ExperimentOutcome
    result_summary: NonEmptyStr
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime


class LearningCandidate(ContractModel):
    candidate_id: UUID
    tenant_id: NonEmptyStr
    experiment_id: UUID
    model_family_id: NonEmptyStr
    candidate_model_version_id: NonEmptyStr
    dataset_version_id: NonEmptyStr
    feature_schema_version_id: NonEmptyStr
    autonomy_level: AutonomyLevel
    promoted: bool = False
    assigned_to_bot: bool = False
    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime


class LearningHistoryEntry(ContractModel):
    hypothesis: LearningHypothesis
    experiments: tuple[LearningExperiment, ...]
    candidates: tuple[LearningCandidate, ...]
