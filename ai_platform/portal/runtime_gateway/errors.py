from __future__ import annotations


class GatewayError(Exception):
    """Stable fail-closed protocol error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class UpstreamError(GatewayError):
    """A bounded error from the generation-local Freqtrade relationship."""
