from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from ai_platform.portal.contracts.risk import TradeSide
from ai_platform.portal.portfolio_risk import (
    AllocationRequest,
    BotBudgetAllocation,
    CorrelationEvidence,
    PortfolioBudget,
    PortfolioPosition,
    PortfolioRiskEngine,
    PortfolioRiskOutcome,
    PortfolioRiskPolicy,
    PortfolioRiskSnapshot,
)


NOW = datetime(2026, 8, 12, 8, 0, tzinfo=UTC)
TENANT = "tenant-a"
BOT = "bot-a"


def _policy(**updates: object) -> PortfolioRiskPolicy:
    values = {
        "policy_id": UUID("10000000-0000-4000-8000-000000000001"),
        "tenant_id": TENANT,
        "version": 1,
        "effective_at": NOW - timedelta(days=1),
        "expires_at": NOW + timedelta(days=1),
        "max_gross_exposure": Decimal(1000),
        "max_net_exposure": Decimal(1000),
        "max_symbol_exposure": Decimal(700),
        "max_concentration": Decimal("0.70"),
        "max_correlation": Decimal("0.80"),
        "max_drawdown": Decimal("0.20"),
        "max_turnover": Decimal(2000),
        "min_liquidity": Decimal(500),
    }
    values.update(updates)
    return PortfolioRiskPolicy(**values)


def _budget(**updates: object) -> PortfolioBudget:
    values = {
        "budget_id": UUID("20000000-0000-4000-8000-000000000001"),
        "tenant_id": TENANT,
        "revision": 7,
        "virtual_capital": Decimal(1000),
        "allocations": (
            BotBudgetAllocation(tenant_id=TENANT, bot_id=BOT, amount=Decimal(600)),
            BotBudgetAllocation(tenant_id=TENANT, bot_id="bot-b", amount=Decimal(400)),
        ),
        "effective_at": NOW - timedelta(days=1),
        "expires_at": NOW + timedelta(days=1),
    }
    values.update(updates)
    return PortfolioBudget(**values)


def _snapshot(**updates: object) -> PortfolioRiskSnapshot:
    values = {
        "snapshot_id": UUID("30000000-0000-4000-8000-000000000001"),
        "tenant_id": TENANT,
        "observed_at": NOW,
        "positions": (),
        "correlations": (),
        "drawdown": Decimal("0.05"),
        "turnover": Decimal(100),
        "liquidity_by_symbol": (("BTC/USDT", Decimal(1000)),),
        "portfolio_suspended": False,
        "suspended_bot_ids": (),
    }
    values.update(updates)
    return PortfolioRiskSnapshot(**values)


def _request(
    policy: PortfolioRiskPolicy, budget: PortfolioBudget, **updates: object
) -> AllocationRequest:
    values = {
        "request_id": UUID("40000000-0000-4000-8000-000000000001"),
        "tenant_id": TENANT,
        "bot_id": BOT,
        "symbol": "BTC/USDT",
        "side": TradeSide.BUY,
        "notional": Decimal(100),
        "policy_digest": policy.digest(),
        "budget_digest": budget.digest(),
        "requested_at": NOW,
    }
    values.update(updates)
    return AllocationRequest(**values)


def _evaluate(
    *,
    policy: PortfolioRiskPolicy | None = None,
    budget: PortfolioBudget | None = None,
    snapshot: PortfolioRiskSnapshot | None = None,
    request_updates: dict[str, object] | None = None,
):
    policy = policy or _policy()
    budget = budget or _budget()
    request = _request(policy, budget, **(request_updates or {}))
    return PortfolioRiskEngine(policy, budget).evaluate(request, snapshot or _snapshot())


def test_allows_complete_evidence_and_preserves_exact_input_identities() -> None:
    policy, budget, snapshot = _policy(), _budget(), _snapshot()
    request = _request(policy, budget)

    decision = PortfolioRiskEngine(policy, budget).evaluate(request, snapshot)

    assert decision.outcome is PortfolioRiskOutcome.ALLOW
    assert decision.reason_codes == ("ALLOW",)
    assert decision.request_digest == request.digest()
    assert decision.policy_digest == policy.digest()
    assert decision.budget_digest == budget.digest()
    assert decision.snapshot_digest == snapshot.digest()


def test_aggregate_exposure_across_multiple_bots_is_evaluated() -> None:
    snapshot = _snapshot(
        positions=(
            PortfolioPosition(
                tenant_id=TENANT, bot_id=BOT, symbol="ETH/USDT", signed_notional=Decimal(450)
            ),
            PortfolioPosition(
                tenant_id=TENANT, bot_id="bot-b", symbol="XRP/USDT", signed_notional=Decimal(450)
            ),
        ),
        correlations=(
            CorrelationEvidence(
                left_symbol="BTC/USDT", right_symbol="ETH/USDT", correlation=Decimal("0.2")
            ),
            CorrelationEvidence(
                left_symbol="BTC/USDT", right_symbol="XRP/USDT", correlation=Decimal("0.2")
            ),
        ),
    )

    decision = _evaluate(snapshot=snapshot, request_updates={"notional": Decimal(200)})

    assert decision.outcome is PortfolioRiskOutcome.REJECT
    assert "GROSS_EXPOSURE_LIMIT_EXCEEDED" in decision.reason_codes


def test_concurrent_requests_against_same_budget_snapshot_allow_only_one() -> None:
    policy = _policy()
    budget = _budget(
        allocations=(
            BotBudgetAllocation(tenant_id=TENANT, bot_id=BOT, amount=Decimal(100)),
            BotBudgetAllocation(tenant_id=TENANT, bot_id="bot-b", amount=Decimal(400)),
        )
    )
    request = _request(policy, budget, notional=Decimal(100))
    engine = PortfolioRiskEngine(policy, budget)

    with ThreadPoolExecutor(max_workers=2) as executor:
        decisions = tuple(executor.map(lambda _: engine.reserve(request, _snapshot()), range(2)))

    assert sorted(decision.outcome for decision in decisions) == [
        PortfolioRiskOutcome.ALLOW,
        PortfolioRiskOutcome.UNAVAILABLE,
    ]
    assert any(decision.reason_codes == ("STALE_BUDGET",) for decision in decisions)


@pytest.mark.parametrize(
    ("field", "reason"),
    (("policy_digest", "STALE_POLICY"), ("budget_digest", "STALE_BUDGET")),
)
def test_stale_policy_or_budget_fails_closed(field: str, reason: str) -> None:
    decision = _evaluate(request_updates={field: "0" * 64})

    assert decision.outcome is PortfolioRiskOutcome.UNAVAILABLE
    assert decision.reason_codes == (reason,)


def test_concentration_breach_rejects() -> None:
    decision = _evaluate(
        policy=_policy(max_concentration=Decimal("0.50")),
        request_updates={"notional": Decimal(600)},
    )

    assert decision.outcome is PortfolioRiskOutcome.REJECT
    assert "CONCENTRATION_LIMIT_EXCEEDED" in decision.reason_codes


def test_drawdown_breach_rejects() -> None:
    decision = _evaluate(snapshot=_snapshot(drawdown=Decimal("0.21")))

    assert decision.outcome is PortfolioRiskOutcome.REJECT
    assert decision.reason_codes == ("DRAWDOWN_LIMIT_EXCEEDED",)


def test_correlation_unavailable_is_not_zero_risk() -> None:
    snapshot = _snapshot(
        positions=(
            PortfolioPosition(
                tenant_id=TENANT, bot_id="bot-b", symbol="ETH/USDT", signed_notional=Decimal(100)
            ),
        ),
        correlations=None,
    )

    decision = _evaluate(snapshot=snapshot)

    assert decision.outcome is PortfolioRiskOutcome.UNAVAILABLE
    assert "CORRELATION_EVIDENCE_UNAVAILABLE" in decision.reason_codes


def test_missing_liquidity_is_insufficient_evidence() -> None:
    decision = _evaluate(snapshot=_snapshot(liquidity_by_symbol=None))

    assert decision.outcome is PortfolioRiskOutcome.UNAVAILABLE
    assert decision.reason_codes == ("LIQUIDITY_EVIDENCE_UNAVAILABLE",)


def test_exact_replay_is_byte_deterministic() -> None:
    policy, budget, snapshot = _policy(), _budget(), _snapshot()
    request = _request(policy, budget)
    engine = PortfolioRiskEngine(policy, budget)

    first = engine.evaluate(request, snapshot)
    second = engine.evaluate(request, snapshot)

    assert first.canonical_json() == second.canonical_json()
    assert first.digest() == second.digest()


def test_reason_and_metric_ordering_is_deterministic() -> None:
    policy = _policy(
        max_gross_exposure=Decimal(10),
        max_net_exposure=Decimal(10),
        max_symbol_exposure=Decimal(10),
    )
    decision = _evaluate(policy=policy, request_updates={"notional": Decimal(600)})

    assert decision.reason_codes == tuple(sorted(decision.reason_codes))
    assert [name for name, _ in decision.metrics] == sorted(name for name, _ in decision.metrics)


def test_bot_cannot_consume_another_bot_or_tenant_allocation() -> None:
    no_allocation = _evaluate(request_updates={"bot_id": "bot-c"})
    other_tenant = _evaluate(request_updates={"tenant_id": "tenant-b"})

    assert no_allocation.outcome is PortfolioRiskOutcome.REJECT
    assert no_allocation.reason_codes == ("NO_BOT_ALLOCATION",)
    assert other_tenant.outcome is PortfolioRiskOutcome.UNAVAILABLE
    assert "TENANT_MISMATCH" in other_tenant.reason_codes


def test_ai_suggestion_cannot_override_deterministic_reject() -> None:
    decision = _evaluate(
        snapshot=_snapshot(drawdown=Decimal("0.21")),
        request_updates={"ai_suggested_outcome": "ALLOW"},
    )

    assert decision.outcome is PortfolioRiskOutcome.REJECT
    assert decision.reason_codes == ("DRAWDOWN_LIMIT_EXCEEDED",)


@pytest.mark.parametrize(
    ("portfolio_suspended", "suspended_bot_ids", "reason"),
    ((True, (), "PORTFOLIO_SUSPENDED"), (False, (BOT,), "BOT_SUSPENDED")),
)
def test_suspension_inputs_veto_allocation(
    portfolio_suspended: bool,
    suspended_bot_ids: tuple[str, ...],
    reason: str,
) -> None:
    decision = _evaluate(
        snapshot=_snapshot(
            portfolio_suspended=portfolio_suspended,
            suspended_bot_ids=suspended_bot_ids,
        )
    )

    assert decision.outcome is PortfolioRiskOutcome.SUSPEND
    assert decision.reason_codes == (reason,)
