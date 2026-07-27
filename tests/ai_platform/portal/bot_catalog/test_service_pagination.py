from __future__ import annotations

import pytest
from ai_platform.portal.bot_catalog.repository import InMemoryBotCatalogRepository
from ai_platform.portal.bot_catalog.schema import (
    CatalogAccessContext,
    CatalogAccessReasonCode,
    CatalogEntryState,
    CatalogPageRequest,
    CatalogTemplateFilters,
)
from ai_platform.portal.bot_catalog.service import (
    BotCatalogService,
    BotCatalogServiceError,
)
from ai_platform.portal.contracts.bot_management.capabilities import (
    BotManagementCapability,
)
from ai_platform.portal.contracts.bot_management.templates import (
    BotFamily,
    CatalogVersionRef,
)
from bm01_test_support import build_access, snapshot_with_templates, template_entry
from pydantic import ValidationError


def _service_with_three_templates() -> BotCatalogService:
    snapshot = snapshot_with_templates(
        (
            template_entry("alpha", display_name="Alpha"),
            template_entry("beta", display_name="Beta", state=CatalogEntryState.DEPRECATED),
            template_entry("gamma", display_name="Gamma", bot_family=BotFamily.GRID),
        )
    )
    return BotCatalogService(InMemoryBotCatalogRepository((snapshot,)))


def test_template_listing_is_bounded_and_cursor_stable() -> None:
    access = build_access()
    service = _service_with_three_templates()
    catalog_ref = CatalogVersionRef(catalog_id="approved-bots", version="1")
    filters = CatalogTemplateFilters(
        states=(CatalogEntryState.ACTIVE, CatalogEntryState.DEPRECATED)
    )

    first = service.list_templates(access, catalog_ref, filters, CatalogPageRequest(page_size=2))
    second = service.list_templates(
        access,
        catalog_ref,
        filters,
        CatalogPageRequest(page_size=2, cursor=first.page_info.next_cursor),
    )

    assert [item.template.template_id for item in first.items] == ["alpha", "beta"]
    assert [item.template.template_id for item in second.items] == ["gamma"]
    assert first.page_info.has_more is True
    assert second.page_info.has_more is False


def test_template_listing_defaults_to_active_entries() -> None:
    page = _service_with_three_templates().list_templates(
        build_access(),
        CatalogVersionRef(catalog_id="approved-bots", version="1"),
        CatalogTemplateFilters(),
        CatalogPageRequest(page_size=10),
    )

    assert [item.template.template_id for item in page.items] == ["alpha", "gamma"]


def test_template_filters_are_applied_deterministically() -> None:
    page = _service_with_three_templates().list_templates(
        build_access(),
        CatalogVersionRef(catalog_id="approved-bots", version="1"),
        CatalogTemplateFilters(query="gAm", bot_families=(BotFamily.GRID,)),
        CatalogPageRequest(page_size=10),
    )

    assert [item.template.template_id for item in page.items] == ["gamma"]


def test_cursor_is_bound_to_filters() -> None:
    access = build_access()
    service = _service_with_three_templates()
    catalog_ref = CatalogVersionRef(catalog_id="approved-bots", version="1")
    broad = CatalogTemplateFilters(states=(CatalogEntryState.ACTIVE, CatalogEntryState.DEPRECATED))
    first = service.list_templates(access, catalog_ref, broad, CatalogPageRequest(page_size=1))

    with pytest.raises(BotCatalogServiceError) as exc_info:
        service.list_templates(
            access,
            catalog_ref,
            CatalogTemplateFilters(),
            CatalogPageRequest(page_size=1, cursor=first.page_info.next_cursor),
        )

    assert exc_info.value.reason_code == CatalogAccessReasonCode.CURSOR_INVALID


def test_invalid_cursor_is_rejected() -> None:
    with pytest.raises(BotCatalogServiceError) as exc_info:
        _service_with_three_templates().list_templates(
            build_access(),
            CatalogVersionRef(catalog_id="approved-bots", version="1"),
            CatalogTemplateFilters(),
            CatalogPageRequest(page_size=1, cursor="not-valid-base64!"),
        )

    assert exc_info.value.reason_code == CatalogAccessReasonCode.CURSOR_INVALID


def test_page_size_is_capped_at_shared_maximum() -> None:
    with pytest.raises(ValidationError):
        CatalogPageRequest(page_size=101)


def test_template_listing_requires_both_read_capabilities() -> None:
    access = CatalogAccessContext(
        tenant_id="tenant-a",
        capabilities=(BotManagementCapability.CATALOG_READ,),
    )

    with pytest.raises(BotCatalogServiceError) as exc_info:
        _service_with_three_templates().list_templates(
            access,
            CatalogVersionRef(catalog_id="approved-bots", version="1"),
            CatalogTemplateFilters(),
            CatalogPageRequest(),
        )

    assert exc_info.value.reason_code == CatalogAccessReasonCode.CAPABILITY_MISSING


def test_missing_catalog_revision_fails_closed() -> None:
    with pytest.raises(BotCatalogServiceError) as exc_info:
        _service_with_three_templates().list_templates(
            build_access(),
            CatalogVersionRef(catalog_id="approved-bots", version="999"),
            CatalogTemplateFilters(),
            CatalogPageRequest(),
        )

    assert exc_info.value.reason_code == CatalogAccessReasonCode.CATALOG_NOT_FOUND
