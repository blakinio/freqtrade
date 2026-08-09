from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import (
    BotLifecycleCommand,
    CommandConfirmationRequirement,
    CommandOutcome,
    CommandOutcomeStatus,
    CommandReasonCode,
    CommandTarget,
    LifecycleAction,
)
from ai_platform.portal.contracts.bot_management.execution import (
    AcknowledgementStatus,
    ExecutionAcknowledgement,
    ExecutionBinding,
    ExecutionEvidenceRef,
    ExecutionEvidenceSource,
    ExecutionEvidenceType,
    ExecutionReasonCode,
    ReconciliationRecord,
    ReconciliationState,
)
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment, ExecutionMode
from ai_platform.portal.contracts.identity import Actor, ActorType


NOW = datetime(2026, 7, 27, 9, 0, tzinfo=UTC)
LATER = datetime(2026, 7, 27, 9, 1, tzinfo=UTC)
DIGEST = "a" * 64
GENERATION_ID = "generation-1"


def correlation() -> CorrelationContext:
    return CorrelationContext(
        request_id=UUID("00000000-0000-0000-0000-000000000001"),
        correlation_id=UUID("00000000-0000-0000-0000-000000000002"),
        causation_id=UUID("00000000-0000-0000-0000-000000000003"),
    )


def actor(tenant_id: str = "tenant-a") -> Actor:
    return Actor(actor_id="actor-1", tenant_id=tenant_id, actor_type=ActorType.USER)


def target(
    tenant_id: str = "tenant-a",
    config_revision: int = 7,
    runtime_generation_id: str = GENERATION_ID,
) -> CommandTarget:
    return CommandTarget(
        tenant_id=tenant_id,
        bot_id="bot-1",
        config_revision=config_revision,
        runtime_generation_id=runtime_generation_id,
        runtime_id="runtime-1",
        runtime_revision=3,
    )


def lifecycle_command(**overrides: object) -> BotLifecycleCommand:
    values: dict[str, object] = {
        "command_id": "command-1",
        "tenant_id": "tenant-a",
        "actor": actor(),
        "environment": Environment.STAGING,
        "correlation": correlation(),
        "idempotency_key": "idem-command-1",
        "target": target(),
        "capability": BotManagementCapability.BOT_START,
        "confirmation": CommandConfirmationRequirement(required=False),
        "submitted_at": NOW,
        "action": LifecycleAction.START,
    }
    values.update(overrides)
    return BotLifecycleCommand(**values)


def binding() -> ExecutionBinding:
    return ExecutionBinding(
        tenant_id="tenant-a",
        bot_id="bot-1",
        config_revision=7,
        runtime_id="runtime-1",
        runtime_revision=3,
        environment=Environment.STAGING,
        execution_mode=ExecutionMode.DRY_RUN,
        idempotency_key="idem-command-1",
        correlation=correlation(),
    )


def evidence(*, authoritative: bool, tenant_id: str = "tenant-a") -> ExecutionEvidenceRef:
    return ExecutionEvidenceRef(
        evidence_id="evidence-order-1",
        evidence_type=ExecutionEvidenceType.ORDER,
        source=(
            ExecutionEvidenceSource.RUNTIME_DATABASE
            if authoritative
            else ExecutionEvidenceSource.OPERATIONAL_MIRROR
        ),
        authoritative=authoritative,
        tenant_id=tenant_id,
        bot_id="bot-1",
        config_revision=7,
        runtime_id="runtime-1",
        runtime_revision=3,
        observed_at=LATER,
        sha256=DIGEST,
    )


def test_commands_require_idempotency_and_exact_tenant_scope() -> None:
    with pytest.raises(ValidationError):
        lifecycle_command(idempotency_key="")

    with pytest.raises(ValidationError, match="actor"):
        lifecycle_command(actor=actor("tenant-b"))

    with pytest.raises(ValidationError, match="target"):
        lifecycle_command(target=target("tenant-b"))


def test_command_requires_matching_capability() -> None:
    with pytest.raises(ValidationError, match="capability"):
        lifecycle_command(capability=BotManagementCapability.BOT_STOP)


def test_accepted_is_not_execution_success() -> None:
    accepted = CommandOutcome(
        command_id="command-1",
        tenant_id="tenant-a",
        target=target(),
        status=CommandOutcomeStatus.ACCEPTED,
        decided_at=NOW,
    )
    assert accepted.status == CommandOutcomeStatus.ACCEPTED
    assert accepted.reconciliation_ref is None

    with pytest.raises(ValidationError, match="not execution success"):
        CommandOutcome(
            command_id="command-1",
            tenant_id="tenant-a",
            target=target(),
            status=CommandOutcomeStatus.ACCEPTED,
            reconciliation_ref="reconciliation-1",
            decided_at=NOW,
        )


def test_stale_revision_requires_exact_mismatch_evidence() -> None:
    with pytest.raises(ValidationError, match="observed revision"):
        CommandOutcome(
            command_id="command-1",
            tenant_id="tenant-a",
            target=target(),
            status=CommandOutcomeStatus.BLOCKED,
            reason_codes=(CommandReasonCode.STALE_REVISION,),
            decided_at=NOW,
        )

    stale = CommandOutcome(
        command_id="command-1",
        tenant_id="tenant-a",
        target=target(),
        status=CommandOutcomeStatus.BLOCKED,
        reason_codes=(CommandReasonCode.STALE_REVISION,),
        observed_config_revision=8,
        decided_at=NOW,
    )
    assert stale.observed_config_revision == 8

    with pytest.raises(ValidationError, match="must use STALE_REVISION"):
        CommandOutcome(
            command_id="command-1",
            tenant_id="tenant-a",
            target=target(),
            status=CommandOutcomeStatus.BLOCKED,
            reason_codes=(CommandReasonCode.RUNTIME_UNAVAILABLE,),
            observed_config_revision=8,
            decided_at=NOW,
        )


def test_stale_generation_requires_exact_mismatch_evidence() -> None:
    with pytest.raises(ValidationError, match="observed generation"):
        CommandOutcome(
            command_id="command-1",
            tenant_id="tenant-a",
            target=target(),
            status=CommandOutcomeStatus.BLOCKED,
            reason_codes=(CommandReasonCode.STALE_GENERATION,),
            decided_at=NOW,
        )

    stale = CommandOutcome(
        command_id="command-1",
        tenant_id="tenant-a",
        target=target(),
        status=CommandOutcomeStatus.BLOCKED,
        reason_codes=(CommandReasonCode.STALE_GENERATION,),
        observed_runtime_generation_id="generation-2",
        decided_at=NOW,
    )
    assert stale.observed_runtime_generation_id == "generation-2"

    with pytest.raises(ValidationError, match="must use STALE_GENERATION"):
        CommandOutcome(
            command_id="command-1",
            tenant_id="tenant-a",
            target=target(),
            status=CommandOutcomeStatus.BLOCKED,
            reason_codes=(CommandReasonCode.RUNTIME_UNAVAILABLE,),
            observed_runtime_generation_id="generation-2",
            decided_at=NOW,
        )


def test_accepted_acknowledgement_explicitly_does_not_prove_execution() -> None:
    acknowledgement = ExecutionAcknowledgement(
        acknowledgement_id="ack-1",
        attempt_id="attempt-1",
        binding=binding(),
        status=AcknowledgementStatus.ACCEPTED,
        reason_codes=(ExecutionReasonCode.ACKNOWLEDGED_NOT_EXECUTED,),
        runtime_request_ref="runtime-request-1",
        received_at=NOW,
    )
    assert acknowledgement.execution_proven is False

    with pytest.raises(ValidationError, match="not proven"):
        ExecutionAcknowledgement(
            acknowledgement_id="ack-1",
            attempt_id="attempt-1",
            binding=binding(),
            status=AcknowledgementStatus.ACCEPTED,
            runtime_request_ref="runtime-request-1",
            received_at=NOW,
        )


def test_successful_reconciliation_requires_authoritative_evidence() -> None:
    with pytest.raises(ValidationError, match="requires execution evidence"):
        ReconciliationRecord(
            reconciliation_id="reconciliation-1",
            attempt_id="attempt-1",
            command_id="command-1",
            binding=binding(),
            state=ReconciliationState.SUCCEEDED,
            started_at=NOW,
            reconciled_at=LATER,
        )

    with pytest.raises(ValidationError, match="authoritative evidence"):
        ReconciliationRecord(
            reconciliation_id="reconciliation-1",
            attempt_id="attempt-1",
            command_id="command-1",
            binding=binding(),
            state=ReconciliationState.SUCCEEDED,
            evidence_refs=(evidence(authoritative=False),),
            started_at=NOW,
            reconciled_at=LATER,
        )

    reconciled = ReconciliationRecord(
        reconciliation_id="reconciliation-1",
        attempt_id="attempt-1",
        command_id="command-1",
        binding=binding(),
        state=ReconciliationState.SUCCEEDED,
        evidence_refs=(evidence(authoritative=True),),
        started_at=NOW,
        reconciled_at=LATER,
    )
    assert reconciled.state == ReconciliationState.SUCCEEDED


def test_reconciliation_rejects_cross_tenant_evidence() -> None:
    with pytest.raises(ValidationError, match="tenant mismatch"):
        ReconciliationRecord(
            reconciliation_id="reconciliation-1",
            attempt_id="attempt-1",
            command_id="command-1",
            binding=binding(),
            state=ReconciliationState.SUCCEEDED,
            evidence_refs=(evidence(authoritative=True, tenant_id="tenant-b"),),
            started_at=NOW,
            reconciled_at=LATER,
        )
