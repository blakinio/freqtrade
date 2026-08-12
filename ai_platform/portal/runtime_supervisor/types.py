from __future__ import annotations

from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    NonNegativeInt,
    PositiveInt,
    StringConstraints,
)

from ai_platform.portal.contracts.common import NonEmptyStr, Sha256Hex
from ai_platform.portal.execution.runtime import DriverRuntimeState


DriverReasonCode = Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]{0,63}$")]


class SupervisorOperation(StrEnum):
    ENSURE_PROVISIONED = "EnsureProvisioned"
    ENSURE_RUNNING = "EnsureRunning"
    ENSURE_PAUSED = "EnsurePaused"
    ENSURE_STOPPED = "EnsureStopped"
    ENSURE_RETIRED = "EnsureRetired"
    INSPECT_GENERATION = "InspectGeneration"


class SupervisorRequest(BaseModel):
    """The complete caller-controlled Supervisor request surface."""

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    generation_id: NonEmptyStr
    generation_spec_digest: Sha256Hex
    operation: SupervisorOperation
    command_id: UUID
    expected_generation_ordinal: PositiveInt
    expected_state_version: NonNegativeInt
    correlation_id: UUID
    causation_id: UUID | None = None


class SupervisorOutcomeCode(StrEnum):
    APPLIED = "APPLIED"
    ALREADY_SATISFIED = "ALREADY_SATISFIED"
    OBSERVED = "OBSERVED"
    INVALID_REQUEST = "INVALID_REQUEST"
    GENERATION_NOT_FOUND = "GENERATION_NOT_FOUND"
    GENERATION_SPEC_CONFLICT = "GENERATION_SPEC_CONFLICT"
    STALE_OR_RETIRED_GENERATION = "STALE_OR_RETIRED_GENERATION"
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    PAPER_AUTHORIZATION_REQUIRED = "PAPER_AUTHORIZATION_REQUIRED"
    RETIREMENT_NOT_AUTHORIZED = "RETIREMENT_NOT_AUTHORIZED"
    CONFLICTING_GENERATION_ACTIVE = "CONFLICTING_GENERATION_ACTIVE"
    COMMAND_REPLAY_CONFLICT = "COMMAND_REPLAY_CONFLICT"
    ENGINE_OPERATION_FAILED = "ENGINE_OPERATION_FAILED"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"


class SupervisorOutcome(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    accepted: bool
    code: SupervisorOutcomeCode
    operation: SupervisorOperation
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    generation_id: NonEmptyStr
    generation_spec_digest: Sha256Hex
    command_id: UUID
    correlation_id: UUID
    state: DriverRuntimeState | None = None
    state_version: NonNegativeInt
    driver_reason_code: DriverReasonCode | None = None
    evidence_digest: Sha256Hex
