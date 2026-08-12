from __future__ import annotations

from typing import Any

from ai_platform.portal.runtime_gateway.contract import verify_contract_digest
from ai_platform.portal.runtime_gateway.errors import GatewayError
from ai_platform.portal.runtime_gateway.models import (
    CONTRACT_VERSION,
    GatewayBinding,
    GatewayRequest,
    GatewayResponse,
    Operation,
)
from ai_platform.portal.runtime_gateway.upstream import FreqtradeUpstream


_READ_ENDPOINTS = {
    Operation.HEALTH: "/api/v1/ping",
    Operation.READ_POSITIONS: "/api/v1/status",
    Operation.READ_OPEN_ORDERS: "/api/v1/open_orders",
    Operation.READ_TRADES: "/api/v1/trades",
}


class RuntimeGateway:
    def __init__(self, binding: GatewayBinding, upstream: FreqtradeUpstream) -> None:
        verify_contract_digest(binding.gateway_contract_digest)
        self._binding = binding
        self._upstream = upstream

    @property
    def binding(self) -> GatewayBinding:
        return self._binding

    def handle(self, request: GatewayRequest) -> GatewayResponse:
        self._validate_identity(request)
        if request.body:
            raise GatewayError(
                "UNSUPPORTED_ARGUMENT", "operation accepts no caller-controlled arguments"
            )
        if request.operation is Operation.RUNTIME_IDENTITY:
            data: Any = {
                "tenant_id": self._binding.tenant_id,
                "bot_id": self._binding.bot_id,
                "generation_id": self._binding.generation_id,
                "mode": "PAPER",
                "gateway_artifact_digest": self._binding.gateway_artifact_digest,
                "gateway_contract_version": self._binding.gateway_contract_version,
                "gateway_contract_digest": self._binding.gateway_contract_digest,
            }
        else:
            try:
                endpoint = _READ_ENDPOINTS[request.operation]
            except KeyError as exc:
                raise GatewayError(
                    "UNSUPPORTED_OPERATION", "operation is not allow-listed"
                ) from exc
            data = self._upstream.get(endpoint)
        return GatewayResponse(
            request_id=request.request_id,
            generation_id=self._binding.generation_id,
            operation=request.operation.value,
            ok=True,
            authoritative=request.operation is not Operation.HEALTH,
            data=data,
        )

    def _validate_identity(self, request: GatewayRequest) -> None:
        if request.contract_version != CONTRACT_VERSION:
            raise GatewayError("CONTRACT_MISMATCH", "request contract version mismatch")
        expected = (
            self._binding.tenant_id,
            self._binding.bot_id,
            self._binding.generation_id,
        )
        actual = (request.tenant_id, request.bot_id, request.generation_id)
        if actual != expected:
            raise GatewayError(
                "GENERATION_IDENTITY_MISMATCH", "request does not match this generation"
            )
