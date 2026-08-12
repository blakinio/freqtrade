from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ai_platform.portal.runtime_gateway.errors import GatewayError


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
CONTRACT_VERSION = "runtime-gateway.v1"


class Operation(StrEnum):
    HEALTH = "health"
    RUNTIME_IDENTITY = "runtime_identity"
    READ_OPEN_ORDERS = "read_open_orders"
    READ_POSITIONS = "read_positions"
    READ_TRADES = "read_trades"


@dataclass(frozen=True)
class GatewayBinding:
    tenant_id: str
    bot_id: str
    generation_id: str
    mode: str
    gateway_artifact_digest: str
    gateway_contract_version: str
    gateway_contract_digest: str

    def __post_init__(self) -> None:
        for name in ("tenant_id", "bot_id", "generation_id"):
            if not _IDENTIFIER.fullmatch(getattr(self, name)):
                raise GatewayError("INVALID_BINDING", f"invalid {name}")
        if self.mode != "PAPER":
            raise GatewayError("LIVE_UNAVAILABLE", "Runtime Gateway supports PAPER only")
        if self.gateway_contract_version != CONTRACT_VERSION:
            raise GatewayError("CONTRACT_MISMATCH", "unsupported Gateway contract version")
        for name in ("gateway_artifact_digest", "gateway_contract_digest"):
            value = getattr(self, name)
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
                raise GatewayError("INVALID_BINDING", f"invalid {name}")


@dataclass(frozen=True)
class GatewayLimits:
    max_request_bytes: int = 64 * 1024
    max_response_bytes: int = 1024 * 1024
    upstream_timeout_seconds: float = 3.0
    io_timeout_seconds: float = 3.0

    def __post_init__(self) -> None:
        if not 256 <= self.max_request_bytes <= 1024 * 1024:
            raise GatewayError("INVALID_LIMIT", "request limit outside reviewed bounds")
        if not 1024 <= self.max_response_bytes <= 8 * 1024 * 1024:
            raise GatewayError("INVALID_LIMIT", "response limit outside reviewed bounds")
        if not 0.05 <= self.upstream_timeout_seconds <= 10.0:
            raise GatewayError("INVALID_LIMIT", "upstream timeout outside reviewed bounds")
        if not 0.05 <= self.io_timeout_seconds <= 10.0:
            raise GatewayError("INVALID_LIMIT", "I/O timeout outside reviewed bounds")


@dataclass(frozen=True)
class GatewayRequest:
    contract_version: str
    tenant_id: str
    bot_id: str
    generation_id: str
    request_id: str
    operation: Operation
    body: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GatewayResponse:
    request_id: str
    generation_id: str
    operation: str
    ok: bool
    authoritative: bool
    data: Any = None
    error: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "generation_id": self.generation_id,
            "operation": self.operation,
            "ok": self.ok,
            "authoritative": self.authoritative,
            "data": self.data,
            "error": self.error,
        }
