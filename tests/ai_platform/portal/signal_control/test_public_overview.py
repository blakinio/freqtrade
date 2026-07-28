from __future__ import annotations

from datetime import UTC, datetime

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.policies import SignalAuthority, SignalCommand
from ai_platform.portal.contracts.bot_management.signals import SignalAuthenticationMode
from ai_platform.portal.signal_control.overview_service import SignalControlOverviewService
from ai_platform.portal.signal_control.repository import InMemorySignalControlRepository
from ai_platform.portal.signal_control.schema import SignalEndpointRevision


NOW = datetime(2026, 7, 28, 12, 0, tzinfo=UTC)


def test_signal_overview_excludes_authentication_reference_and_webhook_slug() -> None:
    repository = InMemorySignalControlRepository()
    repository.save_endpoint(
        SignalEndpointRevision(
            endpoint_id="endpoint-a",
            tenant_id="tenant-a",
            revision=1,
            display_name="Signed endpoint",
            endpoint_slug="endpoint_slug_12345",
            authentication_mode=SignalAuthenticationMode.HMAC_SHA256,
            authentication_ref="signalref_12345678",
            schema_id="signal.v1",
            schema_revision=1,
            supported_commands=(SignalCommand.OPEN,),
            authority=SignalAuthority.ADVISORY_ONLY,
            max_past_age_seconds=300,
            max_future_skew_seconds=30,
            replay_window_seconds=300,
            require_nonce=True,
            enabled=True,
            created_by_actor_id="actor-a",
            created_at=NOW,
        )
    )
    service = SignalControlOverviewService(
        repository,
        authentication_provider_available=False,
    )

    overview = service.overview(
        tenant_id="tenant-a",
        capabilities=(BotManagementCapability.SIGNAL_ENDPOINT_MANAGE,),
    )
    serialized = overview.canonical_json().lower()

    assert overview.authentication_provider_status == "UNAVAILABLE"
    assert overview.accepted_signal_processing_enabled is False
    assert overview.execution_submission_enabled is False
    assert len(overview.endpoints) == 1
    assert overview.endpoints[0].authentication_reference_exposed is False
    assert overview.endpoints[0].webhook_slug_exposed is False
    assert "signalref_" not in serialized
    assert "endpoint_slug_12345" not in serialized
    assert "authentication_ref" not in serialized
    assert "endpoint_slug" not in serialized
