from __future__ import annotations

from typing import Any

from ai_platform.portal.security.sensitive_data import (
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_ITEMS,
    reject_sensitive_data,
)


def reject_sensitive_payload_keys(
    value: Any,
    *,
    path: str = "payload",
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_items: int = DEFAULT_MAX_ITEMS,
) -> Any:
    """Fail closed before public event/audit payload persistence or publication."""

    return reject_sensitive_data(
        value,
        path=path,
        max_depth=max_depth,
        max_items=max_items,
    )
