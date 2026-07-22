from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import model_validator

from ai_platform.portal.contracts.common import ContractModel, NonEmptyStr
from ai_platform.portal.contracts.environment import Environment


class SecretKind(StrEnum):
    EXCHANGE_CREDENTIAL = "exchange_credential"
    FREQTRADE_CONTROL = "freqtrade_control"
    SERVICE_CREDENTIAL = "service_credential"


class SecretRef(ContractModel):
    provider: NonEmptyStr
    reference_id: NonEmptyStr
    version: NonEmptyStr
    environment: Environment
    tenant_id: NonEmptyStr
    kind: SecretKind


class ExchangeConnection(ContractModel):
    exchange_connection_id: NonEmptyStr
    tenant_id: NonEmptyStr
    name: NonEmptyStr
    environment: Environment
    exchange_id: NonEmptyStr
    secret_ref: SecretRef
    withdrawal_enabled: Literal[False] = False

    @model_validator(mode="after")
    def validate_secret_scope(self) -> Self:
        if self.secret_ref.tenant_id != self.tenant_id:
            raise ValueError("exchange secret reference must belong to the same tenant")
        if self.secret_ref.environment != self.environment:
            raise ValueError("exchange secret reference must match connection environment")
        if self.secret_ref.kind is not SecretKind.EXCHANGE_CREDENTIAL:
            raise ValueError("exchange connection requires an exchange credential reference")
        return self
