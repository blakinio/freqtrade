from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


REDACTED = "[REDACTED]"

_SENSITIVE_KEYS = frozenset(
    {
        "access_token",
        "accesstoken",
        "api_key",
        "api_secret",
        "apikey",
        "apisecret",
        "authorization",
        "client_secret",
        "clientsecret",
        "cookie",
        "password",
        "passphrase",
        "private_key",
        "privatekey",
        "refresh_token",
        "refreshtoken",
        "secret",
        "session_token",
        "sessiontoken",
        "set-cookie",
        "token",
        "websocket_token",
        "websockettoken",
        "ws_token",
        "wstoken",
    }
)


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                redacted[key_text] = REDACTED
            else:
                redacted[key_text] = redact_sensitive(child)
        return redacted
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [redact_sensitive(child) for child in value]
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    compact = normalized.replace("_", "")
    return normalized in _SENSITIVE_KEYS or compact in _SENSITIVE_KEYS
