from __future__ import annotations

from typing import Any

from ai_platform.portal.security.sensitive_data import reject_sensitive_data


def reject_sensitive_payload_keys(value: Any, *, path: str = "payload") -> Any:
    """Fail closed before public event/audit payload persistence or publication."""

    return reject_sensitive_data(value, path=path)
