from __future__ import annotations

from typing import Any

from ai_platform.portal.security.sensitive_data import (
    REDACTED_VALUE,
    classify_sensitive_key,
    redact_sensitive_data,
)


REDACTED = REDACTED_VALUE


def redact_sensitive(value: Any) -> Any:
    return redact_sensitive_data(value, replacement=REDACTED)


def _is_sensitive_key(key: str) -> bool:
    return classify_sensitive_key(key) is not None
