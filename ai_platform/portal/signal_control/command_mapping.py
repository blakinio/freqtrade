from __future__ import annotations

from datetime import datetime
from hashlib import sha256

from ai_platform.portal.contracts.bot_management.capabilities import BotManagementCapability
from ai_platform.portal.contracts.bot_management.commands import LifecycleAction, PositionAction
from ai_platform.portal.contracts.bot_management.policies import SignalCommand
from ai_platform.portal.signal_control.schema import (
    AuthoritativeSignalTargetState,
    MappedCommandFamily,
    MappedCommandVocabulary,
    SignalCommandIntent,
    SignalEndpointRevision,
    SignalPayloadV1,
)


_MAPPING: dict[
    SignalCommand,
    tuple[
        MappedCommandVocabulary,
        MappedCommandFamily,
        str,
        BotManagementCapability | None,
    ],
] = {
    SignalCommand.OPEN: (
        MappedCommandVocabulary.BM00_SIGNAL,
        MappedCommandFamily.TRADE_INTENT,
        SignalCommand.OPEN.value,
        None,
    ),
    SignalCommand.DCA: (
        MappedCommandVocabulary.BM00_SIGNAL,
        MappedCommandFamily.TRADE_INTENT,
        SignalCommand.DCA.value,
        None,
    ),
    SignalCommand.CLOSE_POSITION: (
        MappedCommandVocabulary.BM03_POSITION,
        MappedCommandFamily.POSITION,
        PositionAction.CLOSE_POSITION.value,
        BotManagementCapability.POSITION_CLOSE,
    ),
    SignalCommand.PARTIAL_CLOSE: (
        MappedCommandVocabulary.BM03_POSITION,
        MappedCommandFamily.POSITION,
        PositionAction.PARTIAL_CLOSE.value,
        BotManagementCapability.POSITION_PARTIAL_CLOSE,
    ),
    SignalCommand.CLOSE_ALL: (
        MappedCommandVocabulary.BM03_POSITION,
        MappedCommandFamily.POSITION,
        PositionAction.CLOSE_ALL.value,
        BotManagementCapability.POSITION_CLOSE_ALL,
    ),
    SignalCommand.TAKE_PROFIT: (
        MappedCommandVocabulary.BM03_POSITION,
        MappedCommandFamily.POSITION,
        PositionAction.FORCE_TAKE_PROFIT.value,
        BotManagementCapability.POSITION_CLOSE,
    ),
    SignalCommand.ENABLE_BOT: (
        MappedCommandVocabulary.BM03_LIFECYCLE,
        MappedCommandFamily.LIFECYCLE,
        LifecycleAction.START.value,
        BotManagementCapability.BOT_START,
    ),
    SignalCommand.PAUSE_BOT: (
        MappedCommandVocabulary.BM03_LIFECYCLE,
        MappedCommandFamily.LIFECYCLE,
        LifecycleAction.PAUSE_NEW_ENTRIES.value,
        BotManagementCapability.BOT_PAUSE,
    ),
    SignalCommand.STOP_BOT: (
        MappedCommandVocabulary.BM03_LIFECYCLE,
        MappedCommandFamily.LIFECYCLE,
        LifecycleAction.STOP_KEEP_POSITIONS.value,
        BotManagementCapability.BOT_STOP,
    ),
}


def map_signal_to_command_intent(
    *,
    endpoint: SignalEndpointRevision,
    payload: SignalPayloadV1,
    target: AuthoritativeSignalTargetState,
    payload_sha256: str,
    created_at: datetime,
    preview_only: bool,
) -> SignalCommandIntent:
    vocabulary, family, action, capability = _MAPPING[payload.command]
    identity_material = "|".join(
        (
            endpoint.tenant_id,
            endpoint.endpoint_id,
            str(endpoint.revision),
            payload.signal_id,
            payload.idempotency_key,
            payload_sha256,
            vocabulary.value,
            action,
        )
    )
    intent_id = sha256(identity_material.encode("utf-8")).hexdigest()
    return SignalCommandIntent(
        intent_id=intent_id,
        signal_id=payload.signal_id,
        tenant_id=endpoint.tenant_id,
        endpoint_id=endpoint.endpoint_id,
        endpoint_revision=endpoint.revision,
        bot_id=target.bot_id,
        bot_revision=target.bot_revision,
        config_revision=target.config_revision,
        runtime_id=target.runtime_id,
        runtime_revision=target.runtime_revision,
        vocabulary=vocabulary,
        family=family,
        action=action,
        source_command=payload.command,
        required_capability=capability,
        idempotency_key=f"signal:{endpoint.endpoint_id}:{payload.idempotency_key}",
        pair=payload.pair,
        position_id=payload.position_id,
        position_revision=payload.position_revision,
        price=payload.price,
        quantity=payload.quantity,
        close_fraction=payload.close_fraction,
        preview_only=preview_only,
        created_at=created_at,
    )
