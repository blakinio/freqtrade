from __future__ import annotations

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.grid_control.overview import GridControlOverviewService


def test_grid_overview_blocks_preview_without_trusted_evidence_provider() -> None:
    overview = GridControlOverviewService(
        capability_evidence_provider_available=False
    ).overview((BotManagementCapability.GRID_CONFIGURE,))

    assert overview.capability_evidence_provider_status == "UNAVAILABLE"
    assert overview.canonical_preview_enabled is False
    assert overview.policy_persistence_enabled is False
    assert overview.browser_supplied_capability_evidence_accepted is False
    assert overview.execution_submission_enabled is False
