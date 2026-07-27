from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import PositiveInt, model_validator

from ai_platform.portal.contracts.common import (
    ContractModel,
    CorrelationContext,
    NonEmptyStr,
    Sha256Hex,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import Environment, ExecutionMode


class ExecutionAttemptState(StrEnum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    AMBIGUOUS = "AMBIGUOUS"
    REJECTED = "REJECTED"
    PENDING_RECONCILIATION = "PENDING_RECONCILIATION"


class AcknowledgementStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"


class ExecutionReasonCode(StrEnum):
    ACKNOWLEDGED_NOT_EXECUTED = "ACKNOWLEDGED_NOT_EXECUTED"
    ATTEMPT_DUPLICATE = "ATTEMPT_DUPLICATE"
    CONFIG_REVISION_MISMATCH = "CONFIG_REVISION_MISMATCH"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    EVIDENCE_MISMATCH = "EVIDENCE_MISMATCH"
    EXECUTION_REJECTED = "EXECUTION_REJECTED"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    RECONCILIATION_TIMEOUT = "RECONCILIATION_TIMEOUT"
    RUNTIME_REVISION_MISMATCH = "RUNTIME_REVISION_MISMATCH"
    RUNTIME_UNAVAILABLE = "RUNTIME_UNAVAILABLE"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    TRANSPORT_AMBIGUOUS = "TRANSPORT_AMBIGUOUS"


class ReconciliationState(StrEnum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CONFLICT = "CONFLICT"


class ExecutionEvidenceType(StrEnum):
    RUNTIME_STATE = "runtime_state"
    ORDER = "order"
    POSITION = "position"
    TRADE = "trade"


class ExecutionEvidenceSource(StrEnum):
    RUNTIME_DATABASE = "runtime_database"
    EXCHANGE_SIMULATOR = "exchange_simulator"
    EXCHANGE_SANDBOX = "exchange_sandbox"
    OPERATIONAL_MIRROR = "operational_mirror"


class ExecutionBinding(ContractModel):
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    config_revision: PositiveInt
    runtime_id: NonEmptyStr
    runtime_revision: PositiveInt
    environment: Environment
    execution_mode: ExecutionMode
    idempotency_key: NonEmptyStr
    correlation: CorrelationContext


class ExecutionAttempt(ContractModel):
    attempt_id: NonEmptyStr
    command_id: NonEmptyStr
    binding: ExecutionBinding
    state: ExecutionAttemptState
    attempt_number: PositiveInt
    started_at: UtcDateTime
    completed_at: UtcDateTime | None = None
    acknowledgement_ref: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_attempt(self) -> Self:
        terminal_without_reconciliation = {
            ExecutionAttemptState.REJECTED,
            ExecutionAttemptState.AMBIGUOUS,
        }
        if self.state in terminal_without_reconciliation and self.completed_at is None:
            raise ValueError("terminal attempt state requires completed_at")
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must not be before started_at")
        if self.state == ExecutionAttemptState.ACKNOWLEDGED:
            if self.acknowledgement_ref is None:
                raise ValueError("acknowledged attempt requires acknowledgement reference")
        return self


class ExecutionAcknowledgement(ContractModel):
    acknowledgement_id: NonEmptyStr
    attempt_id: NonEmptyStr
    binding: ExecutionBinding
    status: AcknowledgementStatus
    reason_codes: tuple[ExecutionReasonCode, ...] = ()
    runtime_request_ref: NonEmptyStr
    received_at: UtcDateTime
    execution_proven: Literal[False] = False

    @model_validator(mode="after")
    def validate_acknowledgement(self) -> Self:
        reasons = [reason.value for reason in self.reason_codes]
        if len(reasons) != len(set(reasons)) or reasons != sorted(reasons):
            raise ValueError("acknowledgement reason codes must be unique and sorted")
        if self.status == AcknowledgementStatus.ACCEPTED:
            allowed = {ExecutionReasonCode.ACKNOWLEDGED_NOT_EXECUTED}
            if set(self.reason_codes) != allowed:
                raise ValueError(
                    "accepted acknowledgement must explicitly state execution is not proven"
                )
        elif not self.reason_codes:
            raise ValueError("rejected or ambiguous acknowledgement requires a reason code")
        return self


class AmbiguousExecutionResponse(ContractModel):
    ambiguity_id: NonEmptyStr
    attempt_id: NonEmptyStr
    binding: ExecutionBinding
    reason_code: ExecutionReasonCode
    response_digest: Sha256Hex | None = None
    observed_at: UtcDateTime

    @model_validator(mode="after")
    def validate_ambiguity(self) -> Self:
        if self.reason_code not in {
            ExecutionReasonCode.TRANSPORT_AMBIGUOUS,
            ExecutionReasonCode.RECONCILIATION_TIMEOUT,
        }:
            raise ValueError("ambiguous response must use an ambiguity reason code")
        return self


class ExecutionEvidenceRef(ContractModel):
    evidence_id: NonEmptyStr
    evidence_type: ExecutionEvidenceType
    source: ExecutionEvidenceSource
    authoritative: bool
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    config_revision: PositiveInt
    runtime_id: NonEmptyStr
    runtime_revision: PositiveInt
    observed_at: UtcDateTime
    sha256: Sha256Hex

    @model_validator(mode="after")
    def validate_authority(self) -> Self:
        if self.source == ExecutionEvidenceSource.OPERATIONAL_MIRROR and self.authoritative:
            raise ValueError("operational mirror evidence cannot be authoritative")
        return self


def _validate_reconciliation_reason_codes(record: ReconciliationRecord) -> None:
    reasons = [reason.value for reason in record.reason_codes]
    if len(reasons) != len(set(reasons)) or reasons != sorted(reasons):
        raise ValueError("reconciliation reason codes must be unique and sorted")


def _validate_reconciliation_evidence_order(record: ReconciliationRecord) -> None:
    evidence_keys = [(item.evidence_type.value, item.evidence_id) for item in record.evidence_refs]
    if len(evidence_keys) != len(set(evidence_keys)):
        raise ValueError("reconciliation evidence references must be unique")
    if evidence_keys != sorted(evidence_keys):
        raise ValueError("reconciliation evidence references must use sorted order")


def _validate_evidence_binding(binding: ExecutionBinding, evidence: ExecutionEvidenceRef) -> None:
    if evidence.tenant_id != binding.tenant_id:
        raise ValueError("reconciliation evidence tenant mismatch")
    if evidence.bot_id != binding.bot_id:
        raise ValueError("reconciliation evidence bot mismatch")
    if evidence.config_revision != binding.config_revision:
        raise ValueError("reconciliation evidence config revision mismatch")
    if evidence.runtime_id != binding.runtime_id:
        raise ValueError("reconciliation evidence runtime mismatch")
    if evidence.runtime_revision != binding.runtime_revision:
        raise ValueError("reconciliation evidence runtime revision mismatch")


def _validate_reconciliation_timestamps(record: ReconciliationRecord) -> None:
    terminal = record.state in {
        ReconciliationState.SUCCEEDED,
        ReconciliationState.FAILED,
        ReconciliationState.CONFLICT,
    }
    if terminal != (record.reconciled_at is not None):
        raise ValueError("terminal reconciliation state and reconciled_at must agree")
    if record.reconciled_at is not None and record.reconciled_at < record.started_at:
        raise ValueError("reconciled_at must not be before started_at")


def _validate_reconciliation_result(record: ReconciliationRecord) -> None:
    if record.state == ReconciliationState.SUCCEEDED:
        if record.reason_codes:
            raise ValueError("successful reconciliation must not contain failure reasons")
        if not record.evidence_refs:
            raise ValueError("successful reconciliation requires execution evidence")
        if not any(evidence.authoritative for evidence in record.evidence_refs):
            raise ValueError("successful reconciliation requires authoritative evidence")
    if record.state in {ReconciliationState.FAILED, ReconciliationState.CONFLICT}:
        if not record.reason_codes:
            raise ValueError("failed or conflicting reconciliation requires a reason code")


class ReconciliationRecord(ContractModel):
    reconciliation_id: NonEmptyStr
    attempt_id: NonEmptyStr
    command_id: NonEmptyStr
    binding: ExecutionBinding
    state: ReconciliationState
    evidence_refs: tuple[ExecutionEvidenceRef, ...] = ()
    reason_codes: tuple[ExecutionReasonCode, ...] = ()
    started_at: UtcDateTime
    reconciled_at: UtcDateTime | None = None

    @model_validator(mode="after")
    def validate_reconciliation(self) -> Self:
        _validate_reconciliation_reason_codes(self)
        _validate_reconciliation_evidence_order(self)
        for evidence in self.evidence_refs:
            _validate_evidence_binding(self.binding, evidence)
        _validate_reconciliation_timestamps(self)
        _validate_reconciliation_result(self)
        return self
