from __future__ import annotations

import hashlib
import json

from ai_platform.portal.bot_operations.schema import BotOperationCommand


def stable_command_idempotency_digest(command: BotOperationCommand) -> str:
    """Hash business identity while excluding retry-transport metadata."""

    payload = command.model_dump(mode="json")
    payload.pop("command_id", None)
    payload.pop("submitted_at", None)
    payload.pop("correlation", None)
    confirmation = payload.get("confirmation")
    if isinstance(confirmation, dict):
        confirmation.pop("confirmation_reference", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
