from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.policies import SignalAuthority, SignalCommand
from ai_platform.portal.contracts.bot_management.signals import SignalAuthenticationMode
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.identity import Actor, ActorType
from ai_platform.portal.signal_control.repository import InMemorySignalControlRepository
from ai_platform.portal.signal_control.schema import (
    AuthoritativeSignalTargetState,
    CreateSignalEndpoint,
    SignalControlContext,
    SignalProcessingRequest,
    SignatureVerificationDecision,
    SignatureVerificationStatus,
)
from ai_platform.portal.signal_control.service import SignalControlService


NOW = datetime(2026, 7, 27, 12, 0, tzinfo=UTC)
ALL_COMMANDS = tuple(sorted(SignalCommand, key=lambda item: item.value))


class StaticVerifier:
    def __init__(self, status: SignatureVerificationStatus = SignatureVerificationStatus.VALID):
        self.status = status
        self.calls = 0

    def verify(self, **_: object) -> SignatureVerificationDecision:
        self.calls += 1
        if self.status == SignatureVerificationStatus.UNAVAILABLE:
            return SignatureVerificationDecision(status=self.status)
        suffix = "valid0001" if self.status == SignatureVerificationStatus.VALID else "invalid001"
        return SignatureVerificationDecision(
            status=self.status,
            evidence_ref=f"sigev_{suffix}",
        )


class RaisingVerifier:
    def verify(self, **_: object) -> SignatureVerificationDecision:
        raise RuntimeError("provider offline")


def context(tenant_id: str = "tenant-a", *, manage: bool = True) -> SignalControlContext:
    capabilities = (
        (BotManagementCapability.SIGNAL_ENDPOINT_MANAGE, BotManagementCapability.SIGNAL_RULE_MANAGE)
        if manage
        else (BotManagementCapability.SIGNAL_RULE_MANAGE,)
    )
    return SignalControlContext(
        tenant_id=tenant_id,
        actor=Actor(actor_id="service-webhook", tenant_id=tenant_id, actor_type=ActorType.SERVICE),
        environment=Environment.STAGING,
        capabilities=tuple(sorted(capabilities, key=lambda item: item.value)),
        correlation=CorrelationContext(
            request_id=UUID("00000000-0000-0000-0000-000000000001"),
            correlation_id=UUID("00000000-0000-0000-0000-000000000002"),
        ),
    )


def endpoint_request(
    *,
    endpoint_id: str = "endpoint-a",
    authority: SignalAuthority = SignalAuthority.ADVISORY_ONLY,
    supported_commands: tuple[SignalCommand, ...] = ALL_COMMANDS,
    enabled: bool = True,
) -> CreateSignalEndpoint:
    return CreateSignalEndpoint(
        endpoint_id=endpoint_id,
        display_name="Signal endpoint",
        endpoint_slug="signal-endpoint-0001",
        authentication_mode=SignalAuthenticationMode.HMAC_SHA256,
        authentication_ref="signalref_opaque0001",
        schema_id="signal.v1",
        schema_revision=1,
        supported_commands=tuple(sorted(supported_commands, key=lambda item: item.value)),
        authority=authority,
        max_past_age_seconds=300,
        max_future_skew_seconds=30,
        replay_window_seconds=120,
        require_nonce=True,
        enabled=enabled,
    )


def target(tenant_id: str = "tenant-a") -> AuthoritativeSignalTargetState:
    return AuthoritativeSignalTargetState(
        tenant_id=tenant_id,
        bot_id="bot-a",
        bot_revision=4,
        config_revision=7,
        runtime_id="runtime-a",
        runtime_revision=3,
        observed_at=NOW,
    )


def payload(
    command: SignalCommand = SignalCommand.OPEN,
    **overrides: Any,
) -> dict[str, object]:
    data: dict[str, object] = {
        "signal_id": "signal-a",
        "tenant_id": "tenant-a",
        "endpoint_id": "endpoint-a",
        "issued_at": NOW.isoformat(),
        "nonce": "nonce-a",
        "idempotency_key": "idem-a",
        "bot_id": "bot-a",
        "bot_revision": 4,
        "config_revision": 7,
        "runtime_id": "runtime-a",
        "runtime_revision": 3,
        "command": command.value if isinstance(command, SignalCommand) else command,
    }
    if command in {SignalCommand.OPEN, SignalCommand.DCA}:
        data["pair"] = "BTC/USDT"
    if command in {
        SignalCommand.CLOSE_POSITION,
        SignalCommand.PARTIAL_CLOSE,
        SignalCommand.TAKE_PROFIT,
    }:
        data["position_id"] = "position-a"
        data["position_revision"] = 2
    if command == SignalCommand.PARTIAL_CLOSE:
        data["close_fraction"] = "0.5"
    data.update(overrides)
    return data


def processing_request(
    command: SignalCommand = SignalCommand.OPEN,
    **overrides: Any,
) -> SignalProcessingRequest:
    return SignalProcessingRequest(
        endpoint_id=str(overrides.pop("request_endpoint_id", "endpoint-a")),
        endpoint_revision=int(overrides.pop("endpoint_revision", 1)),
        schema_id=str(overrides.pop("schema_id", "signal.v1")),
        schema_revision=int(overrides.pop("schema_revision", 1)),
        payload=payload(command, **overrides),
    )


def service_with_endpoint(
    *,
    verifier: object | None = None,
    authority: SignalAuthority = SignalAuthority.ADVISORY_ONLY,
    supported_commands: tuple[SignalCommand, ...] = ALL_COMMANDS,
    enabled: bool = True,
    tenant_id: str = "tenant-a",
) -> tuple[SignalControlService, InMemorySignalControlRepository]:
    repository = InMemorySignalControlRepository()
    service = SignalControlService(
        repository,
        verifier or StaticVerifier(),
        clock=lambda: NOW,
    )
    service.create_endpoint(
        context(tenant_id),
        endpoint_request(
            authority=authority,
            supported_commands=supported_commands,
            enabled=enabled,
        ),
    )
    return service, repository
