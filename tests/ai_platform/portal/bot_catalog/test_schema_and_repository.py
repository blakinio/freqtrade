from __future__ import annotations

import pytest
from ai_platform.portal.bot_catalog.repository import InMemoryBotCatalogRepository
from ai_platform.portal.bot_catalog.schema import (
    BotCatalogSnapshot,
    CatalogAccessContext,
    CatalogEntryState,
    CatalogTemplateEntry,
    ModelRequirement,
)
from ai_platform.portal.contracts.bot_management.capabilities import (
    BotManagementCapability,
)
from ai_platform.portal.contracts.bot_management.templates import CatalogVersionRef
from bm01_test_support import build_snapshot, snapshot_with_templates, template_entry
from pydantic import ValidationError


def test_catalog_snapshot_requires_deterministic_template_order() -> None:
    alpha = template_entry("alpha", display_name="Alpha")
    beta = template_entry("beta", display_name="Beta")

    with pytest.raises(ValidationError, match="deterministic sorted order"):
        snapshot_with_templates((beta, alpha))


def test_catalog_snapshot_rejects_duplicate_version_keys() -> None:
    first = template_entry("alpha", display_name="Alpha")
    duplicate = template_entry("alpha", display_name="Alpha duplicate")

    with pytest.raises(ValidationError, match="duplicate keys"):
        snapshot_with_templates((first, duplicate))


def test_model_requirement_is_consistent_with_template_versions() -> None:
    with pytest.raises(ValidationError, match="must not declare supported model versions"):
        CatalogTemplateEntry(
            **template_entry().model_dump(exclude={"model_requirement"}),
            model_requirement=ModelRequirement.FORBIDDEN,
        )


def test_catalog_models_are_frozen() -> None:
    snapshot = build_snapshot()
    field_name = "revision"

    with pytest.raises(ValidationError, match="frozen"):
        setattr(snapshot, field_name, 2)


def test_extra_secret_fields_are_rejected() -> None:
    payload = template_entry().model_dump()
    payload["api_secret"] = "forbidden"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CatalogTemplateEntry.model_validate(payload)


def test_canonical_serialization_is_deterministic() -> None:
    snapshot = build_snapshot()
    reparsed = BotCatalogSnapshot.model_validate(snapshot.model_dump(mode="json"))

    assert reparsed.canonical_json() == snapshot.canonical_json()
    assert "api_key" not in snapshot.canonical_json()
    assert "secret_store" not in snapshot.canonical_json()


def test_repository_resolves_exact_and_latest_revisions() -> None:
    first = snapshot_with_templates((template_entry(),), revision=1)
    second = snapshot_with_templates((template_entry(),), revision=2)
    repository = InMemoryBotCatalogRepository((second, first))

    assert (
        repository.get_snapshot(CatalogVersionRef(catalog_id="approved-bots", version="1")) == first
    )
    assert repository.get_latest_snapshot("approved-bots") == second
    assert (
        repository.get_snapshot(CatalogVersionRef(catalog_id="approved-bots", version="3")) is None
    )


def test_repository_rejects_duplicate_snapshot_revisions() -> None:
    snapshot = build_snapshot()

    with pytest.raises(ValueError, match="duplicate revisions"):
        InMemoryBotCatalogRepository((snapshot, snapshot))


def test_access_capabilities_require_sorted_unique_values() -> None:
    with pytest.raises(ValidationError, match="deterministic sorted order"):
        CatalogAccessContext(
            tenant_id="tenant-a",
            capabilities=(
                BotManagementCapability.TEMPLATE_READ,
                BotManagementCapability.CATALOG_READ,
            ),
        )

    with pytest.raises(ValidationError, match="duplicates"):
        CatalogAccessContext(
            tenant_id="tenant-a",
            capabilities=(
                BotManagementCapability.CATALOG_READ,
                BotManagementCapability.CATALOG_READ,
            ),
        )


def test_catalog_entry_state_round_trip() -> None:
    entry = template_entry(state=CatalogEntryState.DEPRECATED)

    assert CatalogTemplateEntry.model_validate(entry.model_dump(mode="json")) == entry
