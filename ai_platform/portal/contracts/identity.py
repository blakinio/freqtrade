from __future__ import annotations

from enum import StrEnum

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr


class ActorType(StrEnum):
    USER = "user"
    SERVICE = "service"
    AGENT = "agent"
    SYSTEM = "system"


class RoleName(StrEnum):
    USER = "user"
    TRADER = "trader"
    ANALYST = "analyst"
    MODEL_REVIEWER = "model_reviewer"
    ADMIN = "admin"
    SERVICE = "service"


class Permission(StrEnum):
    BOT_READ = "bot.read"
    BOT_CREATE = "bot.create"
    BOT_START = "bot.start"
    BOT_PAUSE = "bot.pause"
    BOT_STOP = "bot.stop"
    TRADE_MANUAL_EXECUTE = "trade.manual_execute"
    EXCHANGE_MANAGE = "exchange.manage"
    MODEL_READ = "model.read"
    MODEL_TRAIN = "model.train"
    MODEL_PROMOTE = "model.promote"
    RISK_MANAGE = "risk.manage"
    AUDIT_READ = "audit.read"
    ADMIN_MANAGE = "admin.manage"


class Tenant(ContractModel):
    tenant_id: NonEmptyStr
    name: NonEmptyStr


class Organization(ContractModel):
    organization_id: NonEmptyStr
    tenant_id: NonEmptyStr
    name: NonEmptyStr


class User(ContractModel):
    user_id: NonEmptyStr
    tenant_id: NonEmptyStr
    identity_subject: NonEmptyStr
    display_name: NonEmptyStr


class Actor(ContractModel):
    actor_id: NonEmptyStr
    tenant_id: NonEmptyStr
    actor_type: ActorType


class ServiceIdentity(ContractModel):
    service_identity_id: NonEmptyStr
    tenant_id: NonEmptyStr
    name: NonEmptyStr


class Role(ContractModel):
    role_id: NonEmptyStr
    tenant_id: NonEmptyStr
    name: RoleName
    permissions: frozenset[Permission]
