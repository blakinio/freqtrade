from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")


def reject_sensitive_payload_keys(value: Any, *, path: str = "payload") -> Any:
    """Fail closed when a public event/audit payload contains a raw sensitive-value field."""

    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalize_key(str(key))
            forbidden = (
                "secret" in normalized
                or "password" in normalized
                or normalized == "passphrase"
                or normalized == "token"
                or normalized.endswith("_token")
                or normalized.endswith("_key")
            )
            if forbidden:
                raise ValueError(f"sensitive payload field is forbidden at {path}.{key}")
            reject_sensitive_payload_keys(nested, path=f"{path}.{key}")
        return value

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            reject_sensitive_payload_keys(nested, path=f"{path}[{index}]")
    return value
