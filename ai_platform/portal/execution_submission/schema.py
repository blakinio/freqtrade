from __future__ import annotations

from typing import Literal, Self

from pydantic import model_validator

from ai_platform.portal.bot_operations.schema import AuthoritativeBotRuntimeState
from ai_platform.portal.contracts.bot_management.exchange_connections import CredentialReference
from ai_platform.portal.contracts.bot_management.execution import (
    AmbiguousExecutionResponse,
    ExecutionAcknowledgement,
    ExecutionAttempt,
    ExecutionAttemptState,
    ExecutionBinding,
    ReconciliationRecord,
)
from ai_platform.portal.contracts.common import (
    ContractModel,
    NonEmptyStr,
    Sha256Hex,
    UtcDateTime,
)
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.contracts.risk import ApprovedExecutionIntent


class PrivateDryRunSubmission(ContractModel):
    command_id: NonEmptyStr
    intent: ApprovedExecutionIntent
    binding: ExecutionBinding
    runtime: AuthoritativeBotRuntimeState
    runtime_health: RuntimeHealthState
    connection_id: NonEmptyStr
    credential_ref: CredentialReference
    exchange_id: NonEmptyStr
    approved_until: UtcDateTime

    @model_validator(mode="after")
    def validate_exact_binding(self) -> Self:
        if self.binding.execution_mode != ExecutionMode.DRY_RUN:
            raise ValueError("private submission requires dry-run execution mode")
        if self.binding.environment == Environment.PRODUCTION:
            raise ValueError("private submission cannot target production")
        if self.intent.tenant_id != self.binding.tenant_id:
            raise ValueError("approved intent tenant must match execution binding")
        if self.intent.trade_intent.bot_id != self.binding.bot_id:
            raise ValueError("approved intent bot must match execution binding")
        if self.intent.trade_intent.environment != self.binding.environment:
            raise ValueError("approved intent environment must match execution binding")
        if self.intent.context.correlation_id != self.binding.correlation.correlation_id:
            raise ValueError("approved intent correlation must match execution binding")
        runtime_values = (
            self.runtime.tenant_id,
            self.runtime.bot_id,
            self.runtime.config_revision,
            self.runtime.runtime_id,
            self.runtime.runtime_revision,
            self.runtime.environment,
        )
        binding_values = (
            self.binding.tenant_id,
            self.binding.bot_id,
            self.binding.config_revision,
            self.binding.runtime_id,
            self.binding.runtime_revision,
            self.binding.environment,
        )
        if runtime_values != binding_values:
            raise ValueError("authoritative runtime state must match execution binding")
        if self.approved_until <= self.intent.created_at:
            raise ValueError("approval expiry must be after intent creation")
        return self


class RuntimeDryRunEvidence(ContractModel):
    runtime_id: NonEmptyStr
    verified_at: UtcDateTime
    dry_run: Literal[True] = True
    force_entry_enabled: Literal[True] = True
    config_digest: Sha256Hex


class PrivateSubmissionReceipt(ContractModel):
    attempt: ExecutionAttempt
    acknowledgement: ExecutionAcknowledgement | None = None
    ambiguity: AmbiguousExecutionResponse | None = None
    reconciliation: ReconciliationRecord
    runtime_config: RuntimeDryRunEvidence | None = None

    @model_validator(mode="after")
    def validate_receipt(self) -> Self:
        if self.acknowledgement is not None and self.ambiguity is not None:
            raise ValueError("receipt cannot contain acknowledgement and ambiguity")
        if self.attempt.attempt_id != self.reconciliation.attempt_id:
            raise ValueError("receipt reconciliation must reference the attempt")
        if self.acknowledgement is not None:
            if self.acknowledgement.attempt_id != self.attempt.attempt_id:
                raise ValueError("receipt acknowledgement must reference the attempt")
        if self.ambiguity is not None:
            if self.ambiguity.attempt_id != self.attempt.attempt_id:
                raise ValueError("receipt ambiguity must reference the attempt")

        if self.attempt.state == ExecutionAttemptState.ACKNOWLEDGED:
            if self.acknowledgement is None or self.runtime_config is None:
                raise ValueError(
                    "acknowledged receipt requires acknowledgement and dry-run evidence"
                )
        if self.attempt.state == ExecutionAttemptState.AMBIGUOUS and self.ambiguity is None:
            raise ValueError("ambiguous receipt requires ambiguity evidence")
        if self.attempt.state == ExecutionAttemptState.REJECTED and self.acknowledgement is None:
            raise ValueError("rejected receipt requires acknowledgement evidence")
        return self


class RuntimeSubmissionResponse(ContractModel):
    accepted: Literal[True] = True
    runtime_request_ref: NonEmptyStr
    response_digest: Sha256Hex
