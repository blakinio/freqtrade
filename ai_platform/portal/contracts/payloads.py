from __future__ import annotations

from typing import Any

from ai_platform.portal.security.sensitive_data import (
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_ITEMS,
    DEFAULT_MAX_SERIALIZED_LAYERS,
    DEFAULT_MAX_STRING_BYTES,
    reject_sensitive_data,
)


def reject_sensitive_payload_keys(
    value: Any,
    *,
    path: str = "payload",
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_items: int = DEFAULT_MAX_ITEMS,
    max_string_bytes: int = DEFAULT_MAX_STRING_BYTES,
    max_serialized_layers: int = DEFAULT_MAX_SERIALIZED_LAYERS,
) -> Any:
    """Fail closed before public event/audit payload persistence or publication."""

    return reject_sensitive_data(
        value,
        path=path,
        max_depth=max_depth,
        max_items=max_items,
        max_string_bytes=max_string_bytes,
        max_serialized_layers=max_serialized_layers,
    )
