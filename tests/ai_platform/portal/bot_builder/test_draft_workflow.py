from __future__ import annotations

import pytest

from ai_platform.portal.bot_builder.schema import (
    BotBuilderReasonCode,
    BotConfigurationDraftPayload,
    CreateBotConfigurationDraft,
    DraftReadinessStatus,
    DraftRevisionRef,
    ReviseBotConfigurationDraft,
)
from ai_platform.portal.bot_builder.service import BotBuilderServiceError
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from tests.ai_platform.portal.bot_builder.support import (
    NOW,
    build_service,
    builder_access,
    complete_payload,
)


def test_create_draft_requires_create_capability() -> None:
    service, _ = build_service()
    access = builder_access(BotManagementCapability.CATALOG_READ)

    with pytest.raises(BotBuilderServiceError) as exc_info:
        service.create_draft(
            access,
            CreateBotConfigurationDraft(
                draft_id="draft-a",
                bot_id="bot-a",
                payload=BotConfigurationDraftPayload(),
            ),
            NOW,
        )

    assert exc_info.value.reason_code == BotBuilderReasonCode.CAPABILITY_MISSING


def test_create_and_revise_draft_are_immutable_and_contiguous() -> None:
    service, repository = build_service()
    access = builder_access()
    first = service.create_draft(
        access,
        CreateBotConfigurationDraft(
            draft_id="draft-a",
            bot_id="bot-a",
            payload=BotConfigurationDraftPayload(),
        ),
        NOW,
    )
    second = service.revise_draft(
        access,
        ReviseBotConfigurationDraft(
            draft_id="draft-a",
            expected_revision=1,
            payload=complete_payload(),
        ),
        NOW,
    )

    assert first.revision == 1
    assert second.revision == 2
    assert second.supersedes_revision == 1
    assert repository.get_draft("tenant-a", "draft-a", 1) == first
    assert repository.get_latest_draft("tenant-a", "draft-a") == second


def test_duplicate_create_and_stale_revision_fail_closed() -> None:
    service, _ = build_service()
    access = builder_access()
    request = CreateBotConfigurationDraft(
        draft_id="draft-a",
        bot_id="bot-a",
        payload=BotConfigurationDraftPayload(),
    )
    service.create_draft(access, request, NOW)

    with pytest.raises(BotBuilderServiceError) as duplicate:
        service.create_draft(access, request, NOW)
    assert duplicate.value.reason_code == BotBuilderReasonCode.DRAFT_ALREADY_EXISTS

    with pytest.raises(BotBuilderServiceError) as stale:
        service.revise_draft(
            access,
            ReviseBotConfigurationDraft(
                draft_id="draft-a",
                expected_revision=2,
                payload=complete_payload(),
            ),
            NOW,
        )
    assert stale.value.reason_code == BotBuilderReasonCode.DRAFT_REVISION_CONFLICT


def test_preview_reports_sorted_missing_fields() -> None:
    service, _ = build_service()
    access = builder_access()
    draft = service.create_draft(
        access,
        CreateBotConfigurationDraft(
            draft_id="draft-a",
            bot_id="bot-a",
            payload=BotConfigurationDraftPayload(),
        ),
        NOW,
    )

    preview = service.preview_draft(access, draft.draft_ref, NOW)

    assert preview.status == DraftReadinessStatus.INCOMPLETE
    values = [item.value for item in preview.missing_fields]
    assert values == sorted(values)
    assert "model_version" not in values


def test_preview_rejects_cross_tenant_access() -> None:
    service, _ = build_service()
    draft = service.create_draft(
        builder_access(),
        CreateBotConfigurationDraft(
            draft_id="draft-a",
            bot_id="bot-a",
            payload=complete_payload(),
        ),
        NOW,
    )
    other_tenant = builder_access().model_copy(update={"tenant_id": "tenant-b"})
    foreign_ref = DraftRevisionRef(
        tenant_id="tenant-a",
        draft_id=draft.draft_id,
        revision=draft.revision,
    )

    with pytest.raises(BotBuilderServiceError) as exc_info:
        service.preview_draft(other_tenant, foreign_ref, NOW)

    assert exc_info.value.reason_code == BotBuilderReasonCode.TENANT_MISMATCH


def test_preview_requires_catalog_read_capability() -> None:
    service, _ = build_service()
    creator = builder_access()
    draft = service.create_draft(
        creator,
        CreateBotConfigurationDraft(
            draft_id="draft-a",
            bot_id="bot-a",
            payload=complete_payload(),
        ),
        NOW,
    )
    no_catalog = builder_access(BotManagementCapability.BOT_CREATE)

    with pytest.raises(BotBuilderServiceError) as exc_info:
        service.preview_draft(no_catalog, draft.draft_ref, NOW)

    assert exc_info.value.reason_code == BotBuilderReasonCode.CAPABILITY_MISSING
