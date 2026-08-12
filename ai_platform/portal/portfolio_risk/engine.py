from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from threading import Lock
from uuid import NAMESPACE_URL, uuid5

from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.portfolio_risk.models import (
    AllocationRequest,
    PortfolioBudget,
    PortfolioRiskDecision,
    PortfolioRiskOutcome,
    PortfolioRiskPolicy,
    PortfolioRiskSnapshot,
)


ALLOW = "ALLOW"
BOT_ALLOCATION_EXCEEDED = "BOT_ALLOCATION_EXCEEDED"
BOT_SUSPENDED = "BOT_SUSPENDED"
CONCENTRATION_LIMIT_EXCEEDED = "CONCENTRATION_LIMIT_EXCEEDED"
CORRELATION_EVIDENCE_UNAVAILABLE = "CORRELATION_EVIDENCE_UNAVAILABLE"
CORRELATION_LIMIT_EXCEEDED = "CORRELATION_LIMIT_EXCEEDED"
DRAWDOWN_EVIDENCE_UNAVAILABLE = "DRAWDOWN_EVIDENCE_UNAVAILABLE"
DRAWDOWN_LIMIT_EXCEEDED = "DRAWDOWN_LIMIT_EXCEEDED"
GROSS_EXPOSURE_LIMIT_EXCEEDED = "GROSS_EXPOSURE_LIMIT_EXCEEDED"
LIQUIDITY_EVIDENCE_UNAVAILABLE = "LIQUIDITY_EVIDENCE_UNAVAILABLE"
LIQUIDITY_LIMIT_EXCEEDED = "LIQUIDITY_LIMIT_EXCEEDED"
NET_EXPOSURE_LIMIT_EXCEEDED = "NET_EXPOSURE_LIMIT_EXCEEDED"
NO_BOT_ALLOCATION = "NO_BOT_ALLOCATION"
PORTFOLIO_SUSPENDED = "PORTFOLIO_SUSPENDED"
STALE_BUDGET = "STALE_BUDGET"
STALE_POLICY = "STALE_POLICY"
SYMBOL_EXPOSURE_LIMIT_EXCEEDED = "SYMBOL_EXPOSURE_LIMIT_EXCEEDED"
TENANT_MISMATCH = "TENANT_MISMATCH"
TURNOVER_EVIDENCE_UNAVAILABLE = "TURNOVER_EVIDENCE_UNAVAILABLE"
TURNOVER_LIMIT_EXCEEDED = "TURNOVER_LIMIT_EXCEEDED"


class PortfolioRiskEngine:
    """Pure evaluator plus optional in-process compare-and-swap reservation boundary."""

    def __init__(self, policy: PortfolioRiskPolicy, budget: PortfolioBudget) -> None:
        if policy.tenant_id != budget.tenant_id:
            raise ValueError("policy and budget tenants must match")
        self._policy = policy
        self._budget = budget
        self._lock = Lock()

    def evaluate(
        self,
        request: AllocationRequest,
        snapshot: PortfolioRiskSnapshot,
    ) -> PortfolioRiskDecision:
        return evaluate_portfolio_risk(self._policy, self._budget, request, snapshot)

    def reserve(
        self,
        request: AllocationRequest,
        snapshot: PortfolioRiskSnapshot,
    ) -> PortfolioRiskDecision:
        """Allow at most one reservation against an exact immutable budget revision."""
        with self._lock:
            decision = evaluate_portfolio_risk(self._policy, self._budget, request, snapshot)
            if decision.outcome is PortfolioRiskOutcome.ALLOW:
                allocations = tuple(
                    item.model_copy(update={"amount": item.amount - request.notional})
                    if item.bot_id == request.bot_id
                    else item
                    for item in self._budget.allocations
                )
                self._budget = self._budget.model_copy(
                    update={"revision": self._budget.revision + 1, "allocations": allocations}
                )
            return decision


def evaluate_portfolio_risk(  # noqa: C901 - one ordered deterministic decision table
    policy: PortfolioRiskPolicy,
    budget: PortfolioBudget,
    request: AllocationRequest,
    snapshot: PortfolioRiskSnapshot,
) -> PortfolioRiskDecision:
    unavailable: set[str] = set()
    suspend: set[str] = set()
    rejects: set[str] = set()
    metrics: dict[str, str] = {}

    identities = {policy.tenant_id, budget.tenant_id, request.tenant_id, snapshot.tenant_id}
    if len(identities) != 1:
        unavailable.add(TENANT_MISMATCH)
    policy_active = _active(policy.effective_at, policy.expires_at, request.requested_at)
    if request.policy_digest != policy.digest() or not policy_active:
        unavailable.add(STALE_POLICY)
    budget_active = _active(budget.effective_at, budget.expires_at, request.requested_at)
    if request.budget_digest != budget.digest() or not budget_active:
        unavailable.add(STALE_BUDGET)
    if snapshot.portfolio_suspended:
        suspend.add(PORTFOLIO_SUSPENDED)
    if request.bot_id in snapshot.suspended_bot_ids:
        suspend.add(BOT_SUSPENDED)

    allocation = budget.allocation_for(request.bot_id)
    if allocation is None:
        rejects.add(NO_BOT_ALLOCATION)
    elif request.notional > allocation:
        rejects.add(BOT_ALLOCATION_EXCEEDED)
    metrics["bot_budget_available"] = str(allocation) if allocation is not None else "UNAVAILABLE"

    symbol_exposure: dict[str, Decimal] = defaultdict(Decimal)
    for position in snapshot.positions:
        symbol_exposure[position.symbol] += position.signed_notional
    delta = request.notional if request.side is TradeSide.BUY else -request.notional
    symbol_exposure[request.symbol] += delta
    gross = sum((abs(value) for value in symbol_exposure.values()), Decimal(0))
    net = abs(sum(symbol_exposure.values(), Decimal(0)))
    requested_symbol = abs(symbol_exposure[request.symbol])
    concentration = requested_symbol / budget.virtual_capital
    metrics.update(
        gross_exposure=str(gross),
        net_exposure=str(net),
        symbol_exposure=str(requested_symbol),
        concentration=str(concentration),
    )
    if gross > policy.max_gross_exposure:
        rejects.add(GROSS_EXPOSURE_LIMIT_EXCEEDED)
    if net > policy.max_net_exposure:
        rejects.add(NET_EXPOSURE_LIMIT_EXCEEDED)
    if requested_symbol > policy.max_symbol_exposure:
        rejects.add(SYMBOL_EXPOSURE_LIMIT_EXCEEDED)
    if concentration > policy.max_concentration:
        rejects.add(CONCENTRATION_LIMIT_EXCEEDED)

    other_symbols = sorted(
        symbol for symbol, value in symbol_exposure.items() if symbol != request.symbol and value
    )
    correlations = (
        None
        if snapshot.correlations is None
        else {
            (item.left_symbol, item.right_symbol): abs(item.correlation)
            for item in snapshot.correlations
        }
    )
    candidate_correlations: list[Decimal] = []
    for other in other_symbols:
        key = tuple(sorted((request.symbol, other)))
        if correlations is None or key not in correlations:
            unavailable.add(CORRELATION_EVIDENCE_UNAVAILABLE)
        else:
            candidate_correlations.append(correlations[key])
    maximum_correlation = max(candidate_correlations, default=Decimal(0))
    metrics["maximum_correlation"] = (
        str(maximum_correlation)
        if CORRELATION_EVIDENCE_UNAVAILABLE not in unavailable
        else "UNAVAILABLE"
    )
    if maximum_correlation > policy.max_correlation:
        rejects.add(CORRELATION_LIMIT_EXCEEDED)

    if snapshot.drawdown is None:
        unavailable.add(DRAWDOWN_EVIDENCE_UNAVAILABLE)
        metrics["drawdown"] = "UNAVAILABLE"
    else:
        metrics["drawdown"] = str(snapshot.drawdown)
        if snapshot.drawdown > policy.max_drawdown:
            rejects.add(DRAWDOWN_LIMIT_EXCEEDED)
    if snapshot.turnover is None:
        unavailable.add(TURNOVER_EVIDENCE_UNAVAILABLE)
        metrics["projected_turnover"] = "UNAVAILABLE"
    else:
        projected_turnover = snapshot.turnover + request.notional
        metrics["projected_turnover"] = str(projected_turnover)
        if projected_turnover > policy.max_turnover:
            rejects.add(TURNOVER_LIMIT_EXCEEDED)

    liquidity = (
        None
        if snapshot.liquidity_by_symbol is None
        else dict(snapshot.liquidity_by_symbol).get(request.symbol)
    )
    metrics["liquidity"] = str(liquidity) if liquidity is not None else "UNAVAILABLE"
    if liquidity is None:
        unavailable.add(LIQUIDITY_EVIDENCE_UNAVAILABLE)
    elif liquidity < policy.min_liquidity:
        rejects.add(LIQUIDITY_LIMIT_EXCEEDED)

    if unavailable:
        outcome, reasons = PortfolioRiskOutcome.UNAVAILABLE, unavailable
    elif suspend:
        outcome, reasons = PortfolioRiskOutcome.SUSPEND, suspend
    elif rejects:
        outcome, reasons = PortfolioRiskOutcome.REJECT, rejects
    else:
        outcome, reasons = PortfolioRiskOutcome.ALLOW, {ALLOW}
    reason_codes = tuple(sorted(reasons))
    decision_seed = "|".join(
        (
            request.digest(),
            policy.digest(),
            budget.digest(),
            snapshot.digest(),
            outcome.value,
            *reason_codes,
        )
    )
    return PortfolioRiskDecision(
        decision_id=uuid5(NAMESPACE_URL, decision_seed),
        outcome=outcome,
        reason_codes=reason_codes,
        request_id=request.request_id,
        request_digest=request.digest(),
        policy_id=policy.policy_id,
        policy_digest=policy.digest(),
        budget_id=budget.budget_id,
        budget_revision=budget.revision,
        budget_digest=budget.digest(),
        snapshot_id=snapshot.snapshot_id,
        snapshot_digest=snapshot.digest(),
        evaluated_at=request.requested_at,
        metrics=tuple(sorted(metrics.items())),
    )


def _active(effective_at: datetime, expires_at: datetime | None, at: datetime) -> bool:
    return effective_at <= at and (expires_at is None or at < expires_at)
