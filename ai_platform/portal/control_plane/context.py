from __future__ import annotations

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, StringConstraints

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.identity import ActorType, Permission


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RequestContext(BaseModel):
    """Trusted application identity context supplied by an authenticated boundary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: NonEmptyStr
    actor_id: NonEmptyStr
    actor_type: ActorType
    permissions: tuple[Permission, ...]
    request_id: UUID
    correlation_id: UUID
    causation_id: UUID | None = None

    def correlation_context(self) -> CorrelationContext:
        return CorrelationContext(
            request_id=self.request_id,
            correlation_id=self.correlation_id,
            causation_id=self.causation_id,
        )


IdentityContextProvider = Callable[[], RequestContext]


def unconfigured_identity_context() -> RequestContext:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="trusted application identity context is not configured",
    )


def identity_dependency(
    provider: IdentityContextProvider | None,
) -> Callable[..., RequestContext]:
    selected = provider or unconfigured_identity_context

    def resolve(context: RequestContext = Depends(selected)) -> RequestContext:
        return context

    return resolve
