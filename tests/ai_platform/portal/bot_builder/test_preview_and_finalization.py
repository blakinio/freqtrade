from __future__ import annotations

import pytest

from ai_platform.portal.bot_builder.schema import (
    BotBuilderReasonCode,
    BotConfigurationDraftPayload,
    CreateBotConfigurationDraft,
    DraftReadinessStatus,
    FinalizeBotConfigurationDraft,
    ReviseBotConfigurationDraft,
)
from ai_platform.portal.bot_builder.service import BotBuilderServiceError
from ai_platform.portal.bot_catalog.schema import ModelRequirement
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.compatibility import (
    CompatibilityReasonCode,
    CompatibilityStatus,
)
from ai_platform.portal.contracts.bot_management.templates import PolicyFamily
from ai_platform.portal.contracts.environment import ExecutionMode
from tests.ai_platform.portal.bot_builder.support import (
    NOW,
    build_service,
    builder_access,
    complete_payload,
    dca_policy,
    entry_policy,
    grid_policy,
    market_policy,
    runtime_policy,
    signal_policy,
)


def _create_complete_draft(service, *, draft_id: str = "draft-a", bot_id: str = "bot-a"):
    return service.create_draft(
        builder_access(),
        CreateBotConfigurationDraft(
            draft_id=draft_id,
            bot_id=bot_id,
            payload=complete_payload(),
        ),
        NOW,
    )


def test_complete_compatible_draft_is_ready() -> None:
    service, _ = build_service()
    draft = _create_complete_draft(service)

    preview = service.preview_draft(builder_access(), draft.draft_ref, NOW)

    assert preview.status == DraftReadinessStatus.READY
    assert preview.compatibility_decision is not None
    assert preview.compatibility_decision.status == CompatibilityStatus.COMPATIBLE


def test_policy_families_are_derived_and_sorted() -> None:
    service, _ = build_service()
    draft = service.create_draft(
        builder_access(),
        CreateBotConfigurationDraft(
            draft_id="draft-a",
            bot_id="bot-a",
            payload=complete_payload(dca=dca_policy(), signal=signal_policy()),
        ),
        NOW,
    )

    preview = service.preview_draft(builder_access(), draft.draft_ref, NOW)
    decision = preview.compatibility_decision

    assert decision is not None
    assert decision.selection.policy_families == tuple(
        sorted(
            (
                PolicyFamily.DCA,
                PolicyFamily.ENTRY,
                PolicyFamily.EXIT,
                PolicyFamily.MARKET,
                PolicyFamily.POSITION_SIZING,
                PolicyFamily.RISK_REFERENCE,
                PolicyFamily.RUNTIME,
                PolicyFamily.SIGNAL,
            ),
            key=lambda item: item.value,
        )
    )


def test_required_model_is_incompatible_when_omitted() -> None:
    service, _ = build_service(model_requirement=ModelRequirement.REQUIRED)
    draft = service.create_draft(
        builder_access(),
        CreateBotConfigurationDraft(
            draft_id="draft-a",
            bot_id="bot-a",
            payload=complete_payload(model_version=None),
        ),
        NOW,
    )

    preview = service.preview_draft(builder_access(), draft.draft_ref, NOW)

    assert preview.status == DraftReadinessStatus.INCOMPATIBLE
    assert preview.compatibility_decision is not None
    assert CompatibilityReasonCode.MODEL_REQUIRED in preview.compatibility_decision.reason_codes


def test_cross_policy_validation_is_reported_without_finalizing() -> None:
    service, repository = build_service()
    draft = service.create_draft(
        builder_access(),
        CreateBotConfigurationDraft(
            draft_id="draft-a",
            bot_id="bot-a",
            payload=complete_payload(
                market=market_policy("shared-policy-id"),
                entry=entry_policy("shared-policy-id"),
            ),
        ),
        NOW,
    )

    preview = service.preview_draft(builder_access(), draft.draft_ref, NOW)

    assert preview.status == DraftReadinessStatus.INVALID
    assert any("policy identifiers" in item for item in preview.validation_errors)
    assert repository.get_latest_configuration("tenant-a", "bot-a") is None


def test_grid_and_dca_conflict_is_invalid() -> None:
    service, _ = build_service()
    draft = service.create_draft(
        builder_access(),
        CreateBotConfigurationDraft(
            draft_id="draft-a",
            bot_id="bot-a",
            payload=complete_payload(dca=dca_policy(), grid=grid_policy()),
        ),
        NOW,
    )

    preview = service.preview_draft(builder_access(), draft.draft_ref, NOW)

    assert preview.status == DraftReadinessStatus.INVALID
    assert any("grid and DCA" in item for item in preview.validation_errors)


def test_runtime_mode_mismatch_is_invalid() -> None:
    service, _ = build_service()
    draft = service.create_draft(
        builder_access(),
        CreateBotConfigurationDraft(
            draft_id="draft-a",
            bot_id="bot-a",
            payload=complete_payload(
                runtime=runtime_policy(execution_mode=ExecutionMode.SIMULATED),
                execution_mode=ExecutionMode.DRY_RUN,
            ),
        ),
        NOW,
    )

    preview = service.preview_draft(builder_access(), draft.draft_ref, NOW)

    assert preview.status == DraftReadinessStatus.INVALID
    assert any("runtime policy execution mode" in item for item in preview.validation_errors)


def test_signal_dca_requires_dca_policy() -> None:
    service, _ = build_service()
    draft = service.create_draft(
        builder_access(),
        CreateBotConfigurationDraft(
            draft_id="draft-a",
            bot_id="bot-a",
            payload=complete_payload(signal=signal_policy()),
        ),
        NOW,
    )

    preview = service.preview_draft(builder_access(), draft.draft_ref, NOW)

    assert preview.status == DraftReadinessStatus.INVALID
    assert any("signal DCA command" in item for item in preview.validation_errors)


def test_finalization_binds_exact_decision_and_digest() -> None:
    service, repository = build_service()
    draft = _create_complete_draft(service)

    result = service.finalize_draft(
        builder_access(),
        FinalizeBotConfigurationDraft(draft_ref=draft.draft_ref),
        NOW,
    )

    assert result.configuration.revision == 1
    assert (
        result.configuration.compatibility_decision_ref == result.compatibility_decision.decision_id
    )
    assert result.configuration.template_ref == result.compatibility_decision.selection.template_ref
    assert len(result.configuration_sha256) == 64
    assert repository.get_latest_configuration("tenant-a", "bot-a") == result.configuration


def test_finalization_is_idempotent_for_the_same_draft_revision() -> None:
    service, _ = build_service()
    draft = _create_complete_draft(service)
    request = FinalizeBotConfigurationDraft(draft_ref=draft.draft_ref)

    first = service.finalize_draft(builder_access(), request, NOW)
    second = service.finalize_draft(builder_access(), request, NOW)

    assert second == first


def test_incomplete_and_incompatible_drafts_fail_closed() -> None:
    service, _ = build_service(model_requirement=ModelRequirement.REQUIRED)
    incomplete = service.create_draft(
        builder_access(),
        CreateBotConfigurationDraft(
            draft_id="draft-incomplete",
            bot_id="bot-incomplete",
            payload=BotConfigurationDraftPayload(),
        ),
        NOW,
    )
    incompatible = service.create_draft(
        builder_access(),
        CreateBotConfigurationDraft(
            draft_id="draft-incompatible",
            bot_id="bot-incompatible",
            payload=complete_payload(model_version=None),
        ),
        NOW,
    )

    with pytest.raises(BotBuilderServiceError) as incomplete_error:
        service.finalize_draft(
            builder_access(),
            FinalizeBotConfigurationDraft(draft_ref=incomplete.draft_ref),
            NOW,
        )
    assert incomplete_error.value.reason_code == BotBuilderReasonCode.CONFIGURATION_INVALID

    with pytest.raises(BotBuilderServiceError) as incompatible_error:
        service.finalize_draft(
            builder_access(),
            FinalizeBotConfigurationDraft(draft_ref=incompatible.draft_ref),
            NOW,
        )
    assert incompatible_error.value.reason_code == BotBuilderReasonCode.COMPATIBILITY_REJECTED
    assert CompatibilityReasonCode.MODEL_REQUIRED.value in incompatible_error.value.details


def test_only_latest_draft_revision_can_be_finalized() -> None:
    service, _ = build_service()
    access = builder_access()
    first = _create_complete_draft(service)
    service.revise_draft(
        access,
        ReviseBotConfigurationDraft(
            draft_id=first.draft_id,
            expected_revision=1,
            payload=complete_payload(),
        ),
        NOW,
    )

    with pytest.raises(BotBuilderServiceError) as exc_info:
        service.finalize_draft(
            access,
            FinalizeBotConfigurationDraft(draft_ref=first.draft_ref),
            NOW,
        )

    assert exc_info.value.reason_code == BotBuilderReasonCode.DRAFT_REVISION_CONFLICT


def test_configuration_revisions_require_optimistic_concurrency_and_revise_capability() -> None:
    service, repository = build_service()
    full_access = builder_access()
    first = _create_complete_draft(service, draft_id="draft-a", bot_id="bot-a")
    service.finalize_draft(
        full_access,
        FinalizeBotConfigurationDraft(draft_ref=first.draft_ref),
        NOW,
    )
    second = _create_complete_draft(service, draft_id="draft-b", bot_id="bot-a")
    create_only = builder_access(
        BotManagementCapability.BOT_CREATE,
        BotManagementCapability.CATALOG_READ,
    )

    with pytest.raises(BotBuilderServiceError) as capability_error:
        service.finalize_draft(
            create_only,
            FinalizeBotConfigurationDraft(
                draft_ref=second.draft_ref,
                expected_configuration_revision=1,
            ),
            NOW,
        )
    assert capability_error.value.reason_code == BotBuilderReasonCode.CAPABILITY_MISSING

    with pytest.raises(BotBuilderServiceError) as stale_error:
        service.finalize_draft(
            full_access,
            FinalizeBotConfigurationDraft(
                draft_ref=second.draft_ref,
                expected_configuration_revision=2,
            ),
            NOW,
        )
    assert stale_error.value.reason_code == BotBuilderReasonCode.CONFIGURATION_REVISION_CONFLICT

    revised = service.finalize_draft(
        full_access,
        FinalizeBotConfigurationDraft(
            draft_ref=second.draft_ref,
            expected_configuration_revision=1,
        ),
        NOW,
    )
    assert revised.configuration.revision == 2
    assert repository.get_latest_configuration("tenant-a", "bot-a") == revised.configuration


def test_first_configuration_rejects_non_null_expected_revision() -> None:
    service, _ = build_service()
    draft = _create_complete_draft(service)

    with pytest.raises(BotBuilderServiceError) as exc_info:
        service.finalize_draft(
            builder_access(),
            FinalizeBotConfigurationDraft(
                draft_ref=draft.draft_ref,
                expected_configuration_revision=1,
            ),
            NOW,
        )

    assert exc_info.value.reason_code == BotBuilderReasonCode.CONFIGURATION_REVISION_CONFLICT
