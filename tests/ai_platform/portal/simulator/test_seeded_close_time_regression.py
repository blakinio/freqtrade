from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from ai_platform.portal.contracts.common import CorrelationContext
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    RiskDecision,
    RiskDecisionOutcome,
    RiskLimitEvaluation,
    TradeIntent,
)
from ai_platform.portal.simulator.exchange import DeterministicExchangeSimulator
from ai_platform.portal.simulator.schema import ScenarioManifest


SCENARIO = Path("tests/ai_platform/portal/simulator/scenarios/profitable.json")
CORRELATION_ID = UUID("11111111-1111-4111-8111-111111111111")


def _approved_intent(manifest: ScenarioManifest) -> tuple[ApprovedExecutionIntent, CorrelationContext]:
    context = CorrelationContext(request_id=uuid4(), correlation_id=CORRELATION_ID)
    trade_intent = TradeIntent(
        trade_intent_id=uuid4(),
        tenant_id=manifest.tenant_id,
        bot_id=manifest.bot_id,
        source_actor_id="agent-seeded-repair",
        pair=manifest.pair,
        side=manifest.side,
        amount=manifest.amount,
        environment=manifest.environment,
        created_at=manifest.entry_tick.occurred_at,
        context=context,
    )
    risk_decision = RiskDecision(
        risk_decision_id=uuid4(),
        tenant_id=manifest.tenant_id,
        trade_intent_id=trade_intent.trade_intent_id,
        risk_policy_version="risk-seeded-repair-v1",
        decision=RiskDecisionOutcome.APPROVED,
        reason_codes=("seeded-repair-approved",),
        evaluated_limits=(
            RiskLimitEvaluation(
                limit_name="seeded-repair",
                configured_value="1",
                observed_value="1",
                passed=True,
            ),
        ),
        occurred_at=manifest.entry_tick.occurred_at,
        context=context,
    )
    approved = ApprovedExecutionIntent(
        execution_intent_id=uuid4(),
        tenant_id=manifest.tenant_id,
        trade_intent=trade_intent,
        risk_decision=risk_decision,
        created_at=manifest.entry_tick.occurred_at,
        context=context,
    )
    return approved, context


def test_simulated_trade_closes_at_declared_exit_tick() -> None:
    manifest = ScenarioManifest.model_validate_json(SCENARIO.read_text(encoding="utf-8"))
    simulator = DeterministicExchangeSimulator(manifest)
    approved, context = _approved_intent(manifest)

    simulator.submit_approved_intent(approved, context)
    outcome = simulator.close_position()

    assert outcome.opened_at == manifest.entry_tick.occurred_at
    assert outcome.closed_at == manifest.exit_tick.occurred_at
    assert outcome.closed_at > outcome.opened_at
