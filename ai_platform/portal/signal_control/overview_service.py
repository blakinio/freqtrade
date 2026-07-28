from __future__ import annotations

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.signal_control.public_schema import (
    SignalAuthenticationProviderStatus,
    SignalControlOverview,
    public_signal_endpoint_view,
)
from ai_platform.portal.signal_control.repository import SignalControlRepository
from ai_platform.portal.signal_control.schema import (
    SignalControlReasonCode,
)
from ai_platform.portal.signal_control.service import SignalControlServiceError


class SignalControlOverviewService:
    def __init__(
        self,
        repository: SignalControlRepository,
        *,
        authentication_provider_available: bool,
    ) -> None:
        self._repository = repository
        self._authentication_provider_available = authentication_provider_available

    def overview(
        self,
        *,
        tenant_id: str,
        capabilities: tuple[BotManagementCapability, ...],
    ) -> SignalControlOverview:
        if BotManagementCapability.SIGNAL_ENDPOINT_MANAGE not in capabilities:
            raise SignalControlServiceError(SignalControlReasonCode.CAPABILITY_MISSING)
        status = (
            SignalAuthenticationProviderStatus.AVAILABLE
            if self._authentication_provider_available
            else SignalAuthenticationProviderStatus.UNAVAILABLE
        )
        endpoints = tuple(
            public_signal_endpoint_view(endpoint)
            for endpoint in self._repository.list_latest_endpoints(tenant_id)
        )
        return SignalControlOverview(
            authentication_provider_status=status,
            endpoints=endpoints,
            accepted_signal_processing_enabled=(
                self._authentication_provider_available
                and any(endpoint.enabled for endpoint in endpoints)
            ),
        )
