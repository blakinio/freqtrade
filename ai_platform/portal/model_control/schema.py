from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr, UtcDateTime
from ai_platform.portal.contracts.environment import Environment


class ModelPromotionAction(StrEnum):
    PROMOTE = "PROMOTE"
    ROLLBACK = "ROLLBACK"


class ModelPromotionSlot(ContractModel):
    tenant_id: NonEmptyStr
    model_family_id: NonEmptyStr
    environment: Environment
    model_version_id: NonEmptyStr
    updated_at: UtcDateTime
    updated_by_actor_id: NonEmptyStr


class ModelPromotionTransition(ContractModel):
    transition_id: UUID
    tenant_id: NonEmptyStr
    model_family_id: NonEmptyStr
    environment: Environment
    from_model_version_id: NonEmptyStr | None = None
    to_model_version_id: NonEmptyStr
    action: ModelPromotionAction
    actor_id: NonEmptyStr
    occurred_at: UtcDateTime
