from __future__ import annotations

from enum import StrEnum
from hashlib import sha256


class ReplayDecision(StrEnum):
    NEW = "NEW"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    NONCE_REPLAYED = "NONCE_REPLAYED"


def nonce_digest(nonce: str | None) -> str | None:
    if nonce is None:
        return None
    return sha256(nonce.encode("utf-8")).hexdigest()
