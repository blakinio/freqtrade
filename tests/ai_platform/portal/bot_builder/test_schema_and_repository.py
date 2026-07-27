from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_platform.portal.bot_builder.repository import InMemoryBotConfigurationRepository
from ai_platform.portal.bot_builder.schema import (
    BotBuilderAccessContext,
    BotConfigurationDraftPayload,
    BotConfigurationDraftRevision,
)
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from tests.ai_platform.portal.bot_builder.support import NOW, complete_payload


def test_access_capabilities_require_deterministic_unique_order() -> None:
    with pytest.raises(ValidationError, match="deterministic sorted order"):
        BotBuilderAccessContext(
            tenant_id="tenant-a",
            actor_id="actor-a",
            capabilities=(
                BotManagementCapability.CATALOG_READ,
                BotManagementCapability.BOT_CREATE,
            ),
        )

    with pytest.raises(ValidationError, match="duplicates"):
        BotBuilderAccessContext(
            tenant_id="tenant-a",
            actor_id="actor-a",
            capabilities=(
                BotManagementCapability.BOT_CREATE,
                BotManagementCapability.BOT_CREATE,
            ),
        )


def test_draft_revision_lineage_is_contiguous() -> None:
    with pytest.raises(ValidationError, match="first draft revision"):
        BotConfigurationDraftRevision(
            draft_id="draft-a",
            tenant_id="tenant-a",
            bot_id="bot-a",
            revision=1,
            supersedes_revision=1,
            payload=BotConfigurationDraftPayload(),
            created_by_actor_id="actor-a",
            created_at=NOW,
        )

    with pytest.raises(ValidationError, match="immediately preceding"):
        BotConfigurationDraftRevision(
            draft_id="draft-a",
            tenant_id="tenant-a",
            bot_id="bot-a",
            revision=3,
            supersedes_revision=1,
            payload=BotConfigurationDraftPayload(),
            created_by_actor_id="actor-a",
            created_at=NOW,
        )


def test_repository_enforces_draft_identity_and_contiguous_revisions() -> None:
    repository = InMemoryBotConfigurationRepository()
    first = BotConfigurationDraftRevision(
        draft_id="draft-a",
        tenant_id="tenant-a",
        bot_id="bot-a",
        revision=1,
        payload=complete_payload(),
        created_by_actor_id="actor-a",
        created_at=NOW,
    )
    repository.save_draft(first)

    with pytest.raises(ValueError, match="already exists"):
        repository.save_draft(first)

    changed_bot = first.model_copy(
        update={"revision": 2, "supersedes_revision": 1, "bot_id": "bot-b"}
    )
    with pytest.raises(ValueError, match="bot identity"):
        repository.save_draft(changed_bot)


def test_repository_is_tenant_scoped() -> None:
    repository = InMemoryBotConfigurationRepository()
    draft = BotConfigurationDraftRevision(
        draft_id="draft-a",
        tenant_id="tenant-a",
        bot_id="bot-a",
        revision=1,
        payload=complete_payload(),
        created_by_actor_id="actor-a",
        created_at=NOW,
    )
    repository.save_draft(draft)

    assert repository.get_draft("tenant-a", "draft-a", 1) == draft
    assert repository.get_draft("tenant-b", "draft-a", 1) is None


def test_draft_payload_rejects_secret_fields() -> None:
    payload = complete_payload().model_dump()
    payload["api_secret"] = "do-not-store"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        BotConfigurationDraftPayload.model_validate(payload)


def test_draft_payload_canonical_serialization_is_stable() -> None:
    payload = complete_payload()
    reparsed = BotConfigurationDraftPayload.model_validate(payload.model_dump(mode="json"))

    assert reparsed.canonical_json() == payload.canonical_json()
    assert "api_secret" not in payload.canonical_json()
    assert "secret_store" not in payload.canonical_json()
