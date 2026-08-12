from __future__ import annotations

import hashlib
from importlib.resources import files

from ai_platform.portal.runtime_gateway.errors import GatewayError


def bundled_contract_digest() -> str:
    content = (
        files("ai_platform.portal.runtime_gateway")
        .joinpath("runtime-gateway-contract-v1.json")
        .read_bytes()
    )
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def verify_contract_digest(expected: str) -> None:
    if expected != bundled_contract_digest():
        raise GatewayError("CONTRACT_DIGEST_MISMATCH", "bound Gateway contract digest mismatch")
