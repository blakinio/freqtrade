from __future__ import annotations

from enum import StrEnum

from pydantic import model_validator

from ai_platform.portal.contracts.bot_management.policies import SignalAuthority, SignalCommand
from ai_platform.portal.contracts.bot_management.signals import SignalAuthenticationMode
from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.signal_control.schema import SignalEndpointRevision


class SignalAuthenticationProviderStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class PublicSignalEndpointView(ContractModel):
    endpoint_id: NonEmptyStr
    revision: int
    display_name: NonEmptyStr
    authentication_mode: SignalAuthenticationMode
    schema_id: NonEmptyStr
    schema_revision: int
    supported_commands: tuple[SignalCommand, ...]
    authority: SignalAuthority
    max_past_age_seconds: int
    max_future_skew_seconds: int
    replay_window_seconds: int
    require_nonce: bool
    enabled: bool
    created_at: UtcDateTime
    authentication_reference_exposed: bool = False
    webhook_slug_exposed: bool = False

    @model_validator(mode="after")
    def validate_public_endpoint(self) -> PublicSignalEndpointView:
        if self.revision < 1 or self.schema_revision < 1:
            raise ValueError("public signal revisions must be positive")
        if self.authentication_reference_exposed or self.webhook_slug_exposed:
            raise ValueError("public signal endpoint must not expose authentication routing material")
        return self


class SignalControlOverview(ContractModel):
    authentication_provider_status: SignalAuthenticationProviderStatus
    endpoints: tuple[PublicSignalEndpointView, ...]
    accepted_signal_processing_enabled: bool
    execution_submission_enabled: bool = False

    @model_validator(mode="after")
    def validate_overview(self) -> SignalControlOverview:
        if self.authentication_provider_status == SignalAuthenticationProviderStatus.UNAVAILABLE:
            if self.accepted_signal_processing_enabled:
                raise ValueError("unavailable authentication provider must block accepted processing")
        if self.execution_submission_enabled:
            raise ValueError("BMW-03 signal overview must not enable execution submission")
        return self


def public_signal_endpoint_view(endpoint: SignalEndpointRevision) -> PublicSignalEndpointView:
    return PublicSignalEndpointView(
        endpoint_id=endpoint.endpoint_id,
        revision=endpoint.revision,
        display_name=endpoint.display_name,
        authentication_mode=endpoint.authentication_mode,
        schema_id=endpoint.schema_id,
        schema_revision=endpoint.schema_revision,
        supported_commands=endpoint.supported_commands,
        authority=endpoint.authority,
        max_past_age_seconds=endpoint.max_past_age_seconds,
        max_future_skew_seconds=endpoint.max_future_skew_seconds,
        replay_window_seconds=endpoint.replay_window_seconds,
        require_nonce=endpoint.require_nonce,
        enabled=endpoint.enabled,
        created_at=endpoint.created_at,
    )
