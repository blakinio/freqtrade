from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import NonNegativeInt, PositiveInt, StrictBool

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, Sha256Hex, UtcDateTime
from ai_platform.portal.contracts.environment import ExecutionMode
from ai_platform.wickhunter.contracts import BotMode


class BotRolloutStatus(StrEnum):
    REQUESTED = "REQUESTED"
    PRECHECK = "PRECHECK"
    BLOCKED = "BLOCKED"
    STOPPING_PREVIOUS = "STOPPING_PREVIOUS"
    PREVIOUS_STOPPED = "PREVIOUS_STOPPED"
    PROVISIONING = "PROVISIONING"
    STARTING = "STARTING"
    VERIFYING = "VERIFYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class RuntimeIdentityStatus(StrEnum):
    MATCHED = "MATCHED"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"


class ReconciliationFreshnessStatus(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class ReconciliationCompletenessStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


class RuntimeGeneration(ContractModel):
    generation_id: NonEmptyStr
    generation_ordinal: PositiveInt
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr

    config_revision_id: NonEmptyStr
    config_revision_number: PositiveInt
    config_revision_digest: Sha256Hex
    normalized_runtime_config_digest: Sha256Hex

    runtime_image_digest: Sha256Hex
    strategy_version: NonEmptyStr
    strategy_artifact_digest: Sha256Hex
    model_version: NonEmptyStr | None = None
    model_artifact_digest: Sha256Hex | None = None
    feature_schema_version: NonEmptyStr | None = None

    risk_policy_version: NonEmptyStr
    risk_policy_digest: Sha256Hex
    execution_mode: ExecutionMode
    managed_mode: BotMode
    managed_mode_request_digest: Sha256Hex
    managed_mode_resolution_digest: Sha256Hex
    paper_authorization_digest: Sha256Hex | None = None
    exchange_mode: NonEmptyStr
    exchange_connection_revision: NonEmptyStr | None = None

    isolation_profile_version: NonEmptyStr
    isolation_profile_digest: Sha256Hex
    isolation_plan_digest: Sha256Hex
    gateway_artifact_digest: Sha256Hex
    gateway_contract_version: NonEmptyStr
    gateway_contract_digest: Sha256Hex
    market_data_egress_policy_version: NonEmptyStr
    market_data_egress_policy_digest: Sha256Hex

    generation_spec_version: NonEmptyStr
    generation_spec_digest: Sha256Hex

    created_by_actor_id: NonEmptyStr
    created_at: UtcDateTime
    request_id: UUID
    correlation_id: UUID
    causation_id: UUID | None = None


class BotRollout(ContractModel):
    rollout_id: NonEmptyStr
    tenant_id: NonEmptyStr
    bot_id: NonEmptyStr
    from_generation_id: NonEmptyStr | None = None
    to_generation_id: NonEmptyStr
    status: BotRolloutStatus
    reason_code: NonEmptyStr | None = None
    requested_by_actor_id: NonEmptyStr
    idempotency_key: NonEmptyStr
    attempt: PositiveInt = 1
    created_at: UtcDateTime
    updated_at: UtcDateTime
    completed_at: UtcDateTime | None = None


class RuntimeGenerationObservation(ContractModel):
    observation_id: NonEmptyStr
    generation_id: NonEmptyStr
    runtime_instance_id: NonEmptyStr
    reconciliation_epoch: NonNegativeInt
    reconciliation_attempt: PositiveInt
    observed_state: NonEmptyStr
    observed_generation_spec_digest: Sha256Hex
    observed_image_digest: Sha256Hex
    observed_config_digest: Sha256Hex
    source_sequence: NonNegativeInt | None = None
    source_version: NonEmptyStr | None = None
    source_observed_at: UtcDateTime | None = None
    reconciled_at: UtcDateTime
    identity_status: RuntimeIdentityStatus
    freshness_status: ReconciliationFreshnessStatus
    completeness_status: ReconciliationCompletenessStatus
    evidence_hash: Sha256Hex
    reason_code: NonEmptyStr | None = None


class RuntimeGenerationMaterial(ContractModel):
    """Trusted, immutable material resolved before a generation can be created.

    PAPER authorization evidence is supplied only by the server-side material resolver.
    It is never accepted from the browser activation request.
    """

    normalized_runtime_config_digest: Sha256Hex
    runtime_image_digest: Sha256Hex
    strategy_artifact_digest: Sha256Hex
    model_artifact_digest: Sha256Hex | None = None
    feature_schema_version: NonEmptyStr | None = None
    risk_policy_digest: Sha256Hex
    exchange_mode: NonEmptyStr
    exchange_connection_revision: NonEmptyStr | None = None
    isolation_profile_version: NonEmptyStr
    isolation_profile_digest: Sha256Hex
    isolation_plan_digest: Sha256Hex
    gateway_artifact_digest: Sha256Hex
    gateway_contract_version: NonEmptyStr
    gateway_contract_digest: Sha256Hex
    market_data_egress_policy_version: NonEmptyStr
    market_data_egress_policy_digest: Sha256Hex
    paper_activation_authorized: StrictBool = False
    paper_authorization_id: NonEmptyStr | None = None
    paper_authorization_digest: Sha256Hex | None = None
    paper_candidate_package_id: NonEmptyStr | None = None
    paper_candidate_manifest_sha256: Sha256Hex | None = None
    generation_spec_version: NonEmptyStr = "v1"
