from __future__ import annotations

from ai_platform.portal.bot_catalog.default_catalog import approved_dry_run_catalog
from ai_platform.portal.bot_catalog.repository import InMemoryBotCatalogRepository
from ai_platform.portal.bot_catalog.schema import (
    CatalogAccessContext,
    CatalogPageRequest,
    CatalogTemplateFilters,
)
from ai_platform.portal.bot_catalog.service import BotCatalogService
from ai_platform.portal.contracts.bot_management.capabilities import (
    BotManagementCapability,
)
from ai_platform.portal.contracts.bot_management.templates import CatalogVersionRef
from ai_platform.portal.contracts.environment import ExecutionMode


def _access() -> CatalogAccessContext:
    return CatalogAccessContext(
        tenant_id="tenant-a",
        capabilities=(
            BotManagementCapability.CATALOG_READ,
            BotManagementCapability.TEMPLATE_READ,
        ),
    )


def test_default_catalog_is_immutable_dry_run_only_and_secret_free() -> None:
    snapshot = approved_dry_run_catalog()
    payload = snapshot.canonical_json()

    assert snapshot.catalog_ref == CatalogVersionRef(
        catalog_id="portal-approved-dry-run",
        version="1",
    )
    assert snapshot.templates[0].template.supported_execution_modes == (
        ExecutionMode.DRY_RUN,
    )
    assert snapshot.strategies[0].supported_execution_modes == (
        ExecutionMode.DRY_RUN,
    )
    assert snapshot.runtimes[0].supported_execution_modes == (
        ExecutionMode.DRY_RUN,
    )
    assert snapshot.risk_policies[0].supported_execution_modes == (
        ExecutionMode.DRY_RUN,
    )
    assert snapshot.exchange_profiles[0].profile.exchange_id == "simulated"
    assert all(len(entry.sha256) == 64 for entry in snapshot.templates)
    assert all(len(entry.sha256) == 64 for entry in snapshot.strategies)
    assert all(len(entry.sha256) == 64 for entry in snapshot.models)
    assert all(len(entry.sha256) == 64 for entry in snapshot.exchange_profiles)
    assert all(len(entry.sha256) == 64 for entry in snapshot.runtimes)
    assert all(len(entry.sha256) == 64 for entry in snapshot.risk_policies)
    assert "credential" not in payload.lower()
    assert "api_key" not in payload.lower()
    assert "secret" not in payload.lower()


def test_default_catalog_is_available_through_read_only_service() -> None:
    snapshot = approved_dry_run_catalog()
    service = BotCatalogService(InMemoryBotCatalogRepository((snapshot,)))

    latest = service.latest_catalog_ref(_access(), snapshot.catalog_id)
    page = service.list_templates(
        _access(),
        latest,
        CatalogTemplateFilters(execution_modes=(ExecutionMode.DRY_RUN,)),
        CatalogPageRequest(page_size=10),
    )

    assert latest == snapshot.catalog_ref
    assert page.catalog_ref == snapshot.catalog_ref
    assert [item.template.template_id for item in page.items] == [
        "ai-directional-dry-run"
    ]
    assert page.page_info.result_count == 1
