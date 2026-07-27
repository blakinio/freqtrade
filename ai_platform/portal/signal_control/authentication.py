from __future__ import annotations

from typing import Protocol

from ai_platform.portal.contracts.bot_management.signals import (
    SignalAuthenticationMode,
    SignalAuthenticationReference,
)
from ai_platform.portal.signal_control.schema import SignatureVerificationDecision


class SignatureVerificationProvider(Protocol):
    """Verify signatures through an injected provider without resolving secrets here."""

    def verify(
        self,
        *,
        authentication_ref: SignalAuthenticationReference,
        authentication_mode: SignalAuthenticationMode,
        canonical_payload: bytes,
        signature: bytes,
    ) -> SignatureVerificationDecision: ...
