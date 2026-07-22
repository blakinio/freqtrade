from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Protocol

from ai_platform.portal.contracts.bots import BotInstance
from ai_platform.portal.contracts.common import ContractModel, CorrelationContext
from ai_platform.portal.contracts.execution import OrderRecord
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    RejectedExecutionIntent,
    RiskDecision,
    TradeSide,
)
from ai_platform.portal.control_plane.context import RequestContext
from ai_platform.portal.control_plane.database import SessionFactory
from ai_platform.portal.control_plane.service import ControlPlaneService
from ai_platform.portal.execution.errors import UnsupportedExecutionOperationError
from ai_platform.portal.risk.schema import RiskEvaluationSnapshot
from ai_platform.portal.risk.service import RiskEvaluationResult, RiskService


class RiskSnapshotUnavailableError(RuntimeError):
    pass


class TerminalExecutionState(StrEnum):
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    SUBMITTED = "SUBMITTED"


class TerminalIntentResult(ContractModel):
    risk_decision: RiskDecision
    execution_state: TerminalExecutionState
    execution_reason_code: str
    order: OrderRecord | None = None


class RiskSnapshotProvider(Protocol):
    def build_snapshot(
        self,
        context: RequestContext,
        bot: BotInstance,
        *,
        pair: str,
        side: TradeSide,
        amount: Decimal,
    ) -> RiskEvaluationSnapshot: ...


class ApprovedIntentSubmitter(Protocol):
    def submit_approved_intent(
        self,
        intent: ApprovedExecutionIntent,
        context: CorrelationContext,
    ) -> OrderRecord: ...


class UnavailableRiskSnapshotProvider:
    def build_snapshot(
        self,
        context: RequestContext,
        bot: BotInstance,
        *,
        pair: str,
        side: TradeSide,
        amount: Decimal,
    ) -> RiskEvaluationSnapshot:
        del context, bot, pair, side, amount
        raise RiskSnapshotUnavailableError("RISK_SNAPSHOT_UNAVAILABLE")


class UnavailableApprovedIntentSubmitter:
    def submit_approved_intent(
        self,
        intent: ApprovedExecutionIntent,
        context: CorrelationContext,
    ) -> OrderRecord:
        del intent, context
        raise UnsupportedExecutionOperationError("ORDER_SUBMISSION_NOT_IMPLEMENTED")


class TerminalService:
    def __init__(
        self,
        session_factory: SessionFactory,
        *,
        snapshot_provider: RiskSnapshotProvider | None = None,
        execution_submitter: ApprovedIntentSubmitter | None = None,
    ) -> None:
        self._control_plane = ControlPlaneService(session_factory)
        self._risk = RiskService(session_factory)
        self._snapshot_provider = snapshot_provider or UnavailableRiskSnapshotProvider()
        self._execution_submitter = execution_submitter or UnavailableApprovedIntentSubmitter()

    def submit_manual_intent(
        self,
        context: RequestContext,
        *,
        bot_id: str,
        pair: str,
        side: TradeSide,
        amount: Decimal,
    ) -> TerminalIntentResult:
        bot = self._control_plane.get_bot(context, bot_id)
        if pair not in bot.spec.pair_universe:
            raise ValueError("pair is not allowed by the bot's immutable pair universe")

        snapshot = self._snapshot_provider.build_snapshot(
            context,
            bot,
            pair=pair,
            side=side,
            amount=amount,
        )
        risk_result: RiskEvaluationResult = self._risk.evaluate_manual_intent(
            context,
            bot_id=bot_id,
            pair=pair,
            side=side,
            amount=amount,
            environment=bot.spec.environment,
            risk_policy_version_id=bot.spec.risk_policy_version,
            snapshot=snapshot,
        )
        decision = risk_result.risk_decision
        if isinstance(risk_result, RejectedExecutionIntent):
            return TerminalIntentResult(
                risk_decision=decision,
                execution_state=TerminalExecutionState.REJECTED,
                execution_reason_code=decision.reason_codes[0],
            )

        try:
            order = self._execution_submitter.submit_approved_intent(
                risk_result,
                context.correlation_context(),
            )
        except UnsupportedExecutionOperationError as exc:
            return TerminalIntentResult(
                risk_decision=decision,
                execution_state=TerminalExecutionState.BLOCKED,
                execution_reason_code=str(exc),
            )
        return TerminalIntentResult(
            risk_decision=decision,
            execution_state=TerminalExecutionState.SUBMITTED,
            execution_reason_code="ORDER_SUBMITTED",
            order=order,
        )
