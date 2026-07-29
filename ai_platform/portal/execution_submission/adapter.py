from __future__ import annotations

from typing import Protocol

from ai_platform.portal.contracts.bots import BotInstance
from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.execution import (
    ExecutionAdapter,
    ExecutionHealth,
    OpenPosition,
    OrderRecord,
    RuntimeStatus,
    TradeRecord,
)
from ai_platform.portal.contracts.risk import ApprovedExecutionIntent


class ApprovedIntentSubmitter(Protocol):
    def submit_approved_intent(
        self,
        intent: ApprovedExecutionIntent,
        context: CorrelationContext,
    ) -> OrderRecord: ...


class PrivateSubmissionExecutionAdapter:
    """Compose the existing private runtime adapter with the PI-08 submitter.

    Lifecycle and read operations remain owned by the existing adapter. Only the
    approved-intent method is replaced, and only when this wrapper is explicitly
    assembled by trusted server-side composition.
    """

    def __init__(
        self,
        delegate: ExecutionAdapter,
        submitter: ApprovedIntentSubmitter,
    ) -> None:
        self._delegate = delegate
        self._submitter = submitter

    def provision_bot(self, bot: BotInstance, context: CorrelationContext) -> RuntimeStatus:
        return self._delegate.provision_bot(bot, context)

    def start_bot(self, bot: BotInstance, context: CorrelationContext) -> RuntimeStatus:
        return self._delegate.start_bot(bot, context)

    def pause_bot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        return self._delegate.pause_bot(tenant_id, bot_id, context)

    def stop_bot(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        return self._delegate.stop_bot(tenant_id, bot_id, context)

    def get_health(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> ExecutionHealth:
        return self._delegate.get_health(tenant_id, bot_id, context)

    def get_runtime_status(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> RuntimeStatus:
        return self._delegate.get_runtime_status(tenant_id, bot_id, context)

    def submit_approved_intent(
        self,
        intent: ApprovedExecutionIntent,
        context: CorrelationContext,
    ) -> OrderRecord:
        return self._submitter.submit_approved_intent(intent, context)

    def get_open_positions(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> tuple[OpenPosition, ...]:
        return self._delegate.get_open_positions(tenant_id, bot_id, context)

    def get_orders(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> tuple[OrderRecord, ...]:
        return self._delegate.get_orders(tenant_id, bot_id, context)

    def get_trades(
        self,
        tenant_id: str,
        bot_id: str,
        context: CorrelationContext,
    ) -> tuple[TradeRecord, ...]:
        return self._delegate.get_trades(tenant_id, bot_id, context)
