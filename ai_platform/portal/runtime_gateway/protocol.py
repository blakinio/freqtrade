from __future__ import annotations

import json
from typing import Any

from ai_platform.portal.runtime_gateway.errors import GatewayError
from ai_platform.portal.runtime_gateway.models import GatewayRequest, Operation


_FIELDS = {
    "contract_version",
    "tenant_id",
    "bot_id",
    "generation_id",
    "request_id",
    "operation",
    "body",
}


def decode_request(raw: bytes) -> GatewayRequest:
    try:
        document = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GatewayError("MALFORMED_REQUEST", "request must be UTF-8 JSON") from exc
    if not isinstance(document, dict) or set(document) - _FIELDS:
        raise GatewayError("MALFORMED_REQUEST", "request has unknown or invalid fields")
    if set(document) != _FIELDS:
        raise GatewayError("MALFORMED_REQUEST", "request fields are incomplete")
    body = document["body"]
    if not isinstance(body, dict):
        raise GatewayError("MALFORMED_REQUEST", "body must be an object")
    try:
        operation = Operation(document["operation"])
    except (ValueError, TypeError) as exc:
        raise GatewayError("UNSUPPORTED_OPERATION", "operation is not allow-listed") from exc
    string_fields = (
        "contract_version",
        "tenant_id",
        "bot_id",
        "generation_id",
        "request_id",
    )
    if any(not isinstance(document[field], str) or not document[field] for field in string_fields):
        raise GatewayError("MALFORMED_REQUEST", "identity fields must be non-empty strings")
    return GatewayRequest(
        contract_version=document["contract_version"],
        tenant_id=document["tenant_id"],
        bot_id=document["bot_id"],
        generation_id=document["generation_id"],
        request_id=document["request_id"],
        operation=operation,
        body=body,
    )


def encode_document(document: dict[str, Any], max_bytes: int) -> bytes:
    encoded = json.dumps(document, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(encoded) > max_bytes:
        raise GatewayError("RESPONSE_TOO_LARGE", "Gateway response exceeds reviewed bound")
    return encoded + b"\n"
