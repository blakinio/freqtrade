from __future__ import annotations

from enum import StrEnum

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr


class Environment(StrEnum):
    RESEARCH = "research"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class ExecutionMode(StrEnum):
    SIMULATED = "simulated"
    DRY_RUN = "dry_run"


class WorkloadPlane(StrEnum):
    PORTAL = "portal"
    CONTROL = "control"
    EXECUTION = "execution"
    RESEARCH = "research"
    MODEL_TRAINING = "model_training"
    TEST_E2E = "test_e2e"
    OBSERVABILITY = "observability"


class EnvironmentContext(ContractModel):
    tenant_id: NonEmptyStr
    environment: Environment
    workload_plane: WorkloadPlane
    execution_mode: ExecutionMode
