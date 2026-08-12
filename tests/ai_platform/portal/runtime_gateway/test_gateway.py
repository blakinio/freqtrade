from __future__ import annotations

import json
from typing import Any

import pytest

from ai_platform.portal.runtime_gateway.contract import bundled_contract_digest
from ai_platform.portal.runtime_gateway.errors import GatewayError
from ai_platform.portal.runtime_gateway.gateway import RuntimeGateway
from ai_platform.portal.runtime_gateway.models import (
    CONTRACT_VERSION,
    GatewayBinding,
    GatewayRequest,
    Operation,
)
from ai_platform.portal.runtime_gateway.protocol import decode_request, encode_document


class RecordingUpstream:
    def __init__(self, response: Any = None) -> None:
        self.response = response if response is not None else {"status": "ok"}
        self.endpoints: list[str] = []

    def get(self, endpoint: str) -> Any:
        self.endpoints.append(endpoint)
        return self.response


@pytest.fixture
def binding() -> GatewayBinding:
    return GatewayBinding(
        tenant_id="tenant-1",
        bot_id="bot-1",
        generation_id="generation-42",
        mode="PAPER",
        gateway_artifact_digest=f"sha256:{'a' * 64}",
        gateway_contract_version=CONTRACT_VERSION,
        gateway_contract_digest=bundled_contract_digest(),
    )


def request(operation: Operation = Operation.HEALTH, **overrides: Any) -> GatewayRequest:
    values = {
        "contract_version": CONTRACT_VERSION,
        "tenant_id": "tenant-1",
        "bot_id": "bot-1",
        "generation_id": "generation-42",
        "request_id": "request-1",
        "operation": operation,
        "body": {},
    }
    values.update(overrides)
    return GatewayRequest(**values)


@pytest.mark.parametrize("field", ["tenant_id", "bot_id", "generation_id"])
def test_rejects_wrong_or_cross_generation_identity(binding: GatewayBinding, field: str) -> None:
    gateway = RuntimeGateway(binding, RecordingUpstream())
    with pytest.raises(GatewayError, match="does not match") as error:
        gateway.handle(request(**{field: "other"}))
    assert error.value.code == "GENERATION_IDENTITY_MISMATCH"


def test_runtime_identity_preserves_exact_generation_tcb(binding: GatewayBinding) -> None:
    upstream = RecordingUpstream()
    response = RuntimeGateway(binding, upstream).handle(request(Operation.RUNTIME_IDENTITY))
    assert response.authoritative is True
    assert response.data == {
        "tenant_id": binding.tenant_id,
        "bot_id": binding.bot_id,
        "generation_id": binding.generation_id,
        "mode": "PAPER",
        "gateway_artifact_digest": binding.gateway_artifact_digest,
        "gateway_contract_version": binding.gateway_contract_version,
        "gateway_contract_digest": binding.gateway_contract_digest,
    }
    assert upstream.endpoints == []


@pytest.mark.parametrize(
    ("operation", "endpoint"),
    [
        (Operation.HEALTH, "/api/v1/ping"),
        (Operation.READ_POSITIONS, "/api/v1/status"),
        (Operation.READ_OPEN_ORDERS, "/api/v1/open_orders"),
        (Operation.READ_TRADES, "/api/v1/trades"),
    ],
)
def test_maps_allowlisted_reads_to_fixed_endpoints(
    binding: GatewayBinding, operation: Operation, endpoint: str
) -> None:
    upstream = RecordingUpstream([])
    response = RuntimeGateway(binding, upstream).handle(request(operation))
    assert response.ok is True
    assert upstream.endpoints == [endpoint]


def test_rejects_arbitrary_arguments_and_proxy_shape(binding: GatewayBinding) -> None:
    gateway = RuntimeGateway(binding, RecordingUpstream())
    with pytest.raises(GatewayError) as error:
        gateway.handle(request(body={"method": "DELETE", "url": "http://example.test"}))
    assert error.value.code == "UNSUPPORTED_ARGUMENT"


def test_rejects_unsupported_command() -> None:
    raw = json.dumps(
        {
            "contract_version": CONTRACT_VERSION,
            "tenant_id": "tenant-1",
            "bot_id": "bot-1",
            "generation_id": "generation-42",
            "request_id": "request-1",
            "operation": "submit_live_order",
            "body": {},
        }
    ).encode()
    with pytest.raises(GatewayError) as error:
        decode_request(raw)
    assert error.value.code == "UNSUPPORTED_OPERATION"


def test_live_mode_and_contract_substitution_fail_closed(binding: GatewayBinding) -> None:
    values = binding.__dict__ | {"mode": "LIVE"}
    with pytest.raises(GatewayError) as live_error:
        GatewayBinding(**values)
    assert live_error.value.code == "LIVE_UNAVAILABLE"

    values = binding.__dict__ | {"gateway_contract_digest": f"sha256:{'b' * 64}"}
    with pytest.raises(GatewayError) as digest_error:
        RuntimeGateway(GatewayBinding(**values), RecordingUpstream())
    assert digest_error.value.code == "CONTRACT_DIGEST_MISMATCH"


def test_response_bound_is_finite() -> None:
    with pytest.raises(GatewayError) as error:
        encode_document({"value": "x" * 100}, 10)
    assert error.value.code == "RESPONSE_TOO_LARGE"
