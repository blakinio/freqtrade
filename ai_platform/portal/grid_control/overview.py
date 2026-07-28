from __future__ import annotations

from enum import StrEnum

from pydantic import model_validator

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.common import ContractModel
from ai_platform.portal.grid_control.schema import GridControlReasonCode
from ai_platform.portal.grid_control.service import GridControlServiceError


class GridEvidenceProviderStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class GridControlOverview(ContractModel):
    capability_evidence_provider_status: GridEvidenceProviderStatus
    canonical_preview_enabled: bool
    policy_persistence_enabled: bool
    browser_supplied_capability_evidence_accepted: bool = False
    execution_submission_enabled: bool = False

    @model_validator(mode="after")
    def validate_overview(self) -> GridControlOverview:
        if self.capability_evidence_provider_status == GridEvidenceProviderStatus.UNAVAILABLE:
            if self.canonical_preview_enabled or self.policy_persistence_enabled:
                raise ValueError("unavailable grid evidence provider must block preview and persistence")
        if self.browser_supplied_capability_evidence_accepted:
            raise ValueError("browser must not supply authoritative grid capability evidence")
        if self.execution_submission_enabled:
            raise ValueError("BM-05 grid overview must not enable execution submission")
        return self


class GridControlOverviewService:
    def __init__(self, *, capability_evidence_provider_available: bool) -> None:
        self._capability_evidence_provider_available = capability_evidence_provider_available

    def overview(
        self,
        capabilities: tuple[BotManagementCapability, ...],
    ) -> GridControlOverview:
        if BotManagementCapability.GRID_CONFIGURE not in capabilities:
            raise GridControlServiceError((GridControlReasonCode.CAPABILITY_MISSING,))
        available = self._capability_evidence_provider_available
        return GridControlOverview(
            capability_evidence_provider_status=(
                GridEvidenceProviderStatus.AVAILABLE
                if available
                else GridEvidenceProviderStatus.UNAVAILABLE
            ),
            canonical_preview_enabled=available,
            policy_persistence_enabled=available,
        )
