from __future__ import annotations

from dataclasses import dataclass

from ai_platform.portal.bot_builder.repository import InMemoryBotConfigurationRepository
from ai_platform.portal.bot_builder.service import BotConfigurationBuilderService
from ai_platform.portal.bot_catalog.repository import InMemoryBotCatalogRepository
from ai_platform.portal.bot_catalog.service import BotCatalogService
from ai_platform.portal.bot_operations.service import BotCommandService
from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.signals import (
    SignalAuthenticationMode,
    SignalAuthenticationReference,
)
from ai_platform.portal.contracts.identity import Actor, Permission
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.exchange_connections.repository import InMemoryExchangeConnectionRepository
from ai_platform.portal.exchange_connections.service import ExchangeConnectionService
from ai_platform.portal.grid_control.repository import InMemoryGridControlRepository
from ai_platform.portal.grid_control.service import GridControlService
from ai_platform.portal.signal_control.authentication import SignatureVerificationProvider
from ai_platform.portal.signal_control.repository import InMemorySignalControlRepository
from ai_platform.portal.signal_control.schema import (
    SignatureVerificationDecision,
    SignatureVerificationStatus,
)
from ai_platform.portal.signal_control.service import SignalControlService


_PERMISSION_CAPABILITIES: dict[Permission, tuple[BotManagementCapability, ...]] = {
    Permission.BOT_READ: (
        BotManagementCapability.CATALOG_READ,
        BotManagementCapability.COMMAND_READ,
        BotManagementCapability.RECONCILIATION_READ,
        BotManagementCapability.TEMPLATE_READ,
    ),
    Permission.BOT_CREATE: (
        BotManagementCapability.BOT_CREATE,
        BotManagementCapability.BOT_REVISE,
    ),
    Permission.BOT_START: (BotManagementCapability.BOT_START,),
    Permission.BOT_PAUSE: (BotManagementCapability.BOT_PAUSE,),
    Permission.BOT_STOP: (BotManagementCapability.BOT_STOP,),
    Permission.TRADE_MANUAL_EXECUTE: (
        BotManagementCapability.ORDER_CANCEL,
        BotManagementCapability.ORDER_CANCEL_ALL,
        BotManagementCapability.ORDER_REPLACE,
        BotManagementCapability.POSITION_CLOSE,
        BotManagementCapability.POSITION_CLOSE_ALL,
        BotManagementCapability.POSITION_PARTIAL_CLOSE,
    ),
    Permission.EXCHANGE_MANAGE: (
        BotManagementCapability.EXCHANGE_CONNECTION_CREATE,
        BotManagementCapability.EXCHANGE_CONNECTION_REVOKE,
        BotManagementCapability.EXCHANGE_CONNECTION_ROTATE,
        BotManagementCapability.EXCHANGE_CONNECTION_VERIFY,
    ),
    Permission.RISK_MANAGE: (
        BotManagementCapability.KILL_SWITCH_USE,
        BotManagementCapability.PRIVILEGED_POLICY_MANAGE,
    ),
}


class UnavailableSignatureVerificationProvider(SignatureVerificationProvider):
    """Fail closed until a separately reviewed secret-backed verifier is injected."""

    def verify(
        self,
        *,
        authentication_ref: SignalAuthenticationReference,
        authentication_mode: SignalAuthenticationMode,
        canonical_payload: bytes,
        signature: bytes,
    ) -> SignatureVerificationDecision:
        del authentication_ref, authentication_mode, canonical_payload, signature
        return SignatureVerificationDecision(status=SignatureVerificationStatus.UNAVAILABLE)


@dataclass(frozen=True, slots=True)
class BotManagementServices:
    catalog: BotCatalogService
    builder: BotConfigurationBuilderService
    commands: BotCommandService
    signals: SignalControlService
    grid: GridControlService
    exchanges: ExchangeConnectionService


def actor_from_request(context: RequestContext) -> Actor:
    return Actor(
        actor_id=context.actor_id,
        tenant_id=context.tenant_id,
        actor_type=context.actor_type,
    )


def capabilities_from_request(
    context: RequestContext,
) -> tuple[BotManagementCapability, ...]:
    capabilities: set[BotManagementCapability] = set()
    for permission in context.permissions:
        capabilities.update(_PERMISSION_CAPABILITIES.get(permission, ()))
    if Permission.ADMIN_MANAGE in context.permissions:
        capabilities.update(BotManagementCapability)
    return tuple(sorted(capabilities, key=lambda item: item.value))


def build_default_bot_management_services(
    session_factory: SessionFactory,
) -> BotManagementServices:
    catalog = BotCatalogService(InMemoryBotCatalogRepository(()))
    return BotManagementServices(
        catalog=catalog,
        builder=BotConfigurationBuilderService(
            InMemoryBotConfigurationRepository(),
            catalog,
        ),
        commands=BotCommandService(session_factory),
        signals=SignalControlService(
            InMemorySignalControlRepository(),
            UnavailableSignatureVerificationProvider(),
        ),
        grid=GridControlService(InMemoryGridControlRepository()),
        exchanges=ExchangeConnectionService(InMemoryExchangeConnectionRepository()),
    )
