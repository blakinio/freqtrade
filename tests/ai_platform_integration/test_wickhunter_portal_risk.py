from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

import pytest

from ai_platform.portal.contracts.environment import Environment
from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.contracts.risk import (
    ApprovedExecutionIntent,
    RiskDecisionOutcome,
    RiskLimitEvaluation,
    TradeSide,
)
from ai_platform.portal.contracts.risk import (
    RiskDecision as PortalRiskDecision,
)
from ai_platform.wickhunter.contracts import (
    BotMode,
    DataFreshnessEvidence,
    DcaPlan,
    RiskDecision,
    RiskOutcome,
    SourceHealth,
    TradeDirection,
    WickHunterTradeIntent,
)
from ai_platform.wickhunter.portal_risk import (
    PortalRiskBinding,
    PortalRiskBridgeBlockedError,
    PortalRiskEvidenceMismatchError,
    PortalRiskSnapshotSource,
    build_portal_risk_request,
    persist_portal_risk_evidence,
    validate_portal_risk_result,
)


def _hash(character: str) -> str:
    return character * 64


def _intent() -> WickHunterTradeIntent:
    return WickHunterTradeIntent(
        schema_version="wickhunter-trade-intent-v1",
        trade_intent_id=_hash("a"),
        candidate_id=_hash("b"),
        score_id=_hash("c"),
        bot_instance="wickhunter-shadow-01",
        strategy_version="wickhunter-v1",
        model_version=None,
        parameter_version="compatibility-prior-v1",
        symbol="BTC/USDT:USDT",
        side=TradeDirection.LONG,
        decision_timestamp_ms=1_700_000_000_000,
        decision_price=Decimal("100"),
        candidate_reason=("LIQUIDATION_BURST",),
        liquidation_evidence_ids=("event-1",),
        feature_hash=_hash("d"),
        confidence=Decimal("0.80"),
        requested_base_risk_ratio=Decimal("0.01"),
        requested_leverage=Decimal("2"),
        take_profit_ratio=Decimal("0.02"),
        stop_loss_ratio=Decimal("0.01"),
        dca_plan=DcaPlan(
            enabled=True,
            maximum_levels=2,
            spacing_ratio=Decimal("0.01"),
            maximum_total_risk_ratio=Decimal("0.015"),
        ),
        expiration_timestamp_ms=1_700_000_060_000,
        freshness=DataFreshnessEvidence(
            liquidation_age_ms=100,
            candle_age_ms=200,
            open_interest_age_ms=300,
            funding_age_ms=400,
            source_health=(("binance", SourceHealth.HEALTHY),),
        ),
        dataset_hash=_hash("e"),
        model_hash=None,
        code_sha="1" * 40,
        parameter_hash=_hash("f"),
        mode=BotMode.SHADOW,
    )


def _local_decision(
    *,
    outcome: RiskOutcome = RiskOutcome.ALLOW,
    policy: str = "portal-risk-v1",
) -> RiskDecision:
    return RiskDecision(
        risk_decision_id=_hash("1"),
        trade_intent_id=_hash("a"),
        outcome=outcome,
        reason_codes=(
            ("RISK_APPROVED",)
            if outcome is RiskOutcome.ALLOW
            else ("GLOBAL_KILL_SWITCH_ACTIVE",)
        ),
        evaluated_at_ms=1_700_000_001_000,
        risk_policy_version=policy,
    )


def _binding(
    *,
    environment: Environment = Environment.TEST,
    policy: str = "portal-risk-v1",
) -> PortalRiskBinding:
    return PortalRiskBinding(
        tenant_id="tenant-1",
        source_actor_id="wickhunter-shadow-runtime",
        environment=environment,
        portal_risk_policy_version=policy,
    )


def _snapshot(*, observed_at_ms: int = 1_700_000_000_500) -> PortalRiskSnapshotSource:
    return PortalRiskSnapshotSource(
        account_equity_quote=Decimal("10000"),
        current_gross_exposure_quote=Decimal("1000"),
        current_open_positions=2,
        daily_loss_quote=Decimal("50"),
        current_drawdown=Decimal("0.05"),
        runtime_health=RuntimeHealthState.HEALTHY,
        observed_at_ms=observed_at_ms,
    )


def _approved_result(request):
    occurred_at = datetime.fromtimestamp(1_700_000_002, tz=UTC)
    decision = PortalRiskDecision(
        risk_decision_id=uuid5(NAMESPACE_URL, "portal-risk-decision"),
        tenant_id=request.portal_trade_intent.tenant_id,
        trade_intent_id=request.portal_trade_intent.trade_intent_id,
        risk_policy_version=request.portal_risk_policy_version,
        decision=RiskDecisionOutcome.APPROVED,
        reason_codes=("RISK_APPROVED",),
        evaluated_limits=(
            RiskLimitEvaluation(
                limit_name="max_order_notional",
                configured_value="500",
                observed_value="300",
                passed=True,
            ),
        ),
        occurred_at=occurred_at,
        context=request.portal_trade_intent.context,
    )
    return ApprovedExecutionIntent(
        execution_intent_id=uuid5(NAMESPACE_URL, "portal-execution-intent"),
        tenant_id=request.portal_trade_intent.tenant_id,
        trade_intent=request.portal_trade_intent,
        risk_decision=decision,
        created_at=occurred_at,
        context=request.portal_trade_intent.context,
    )


def test_build_portal_request_is_deterministic_and_conservative() -> None:
    request = build_portal_risk_request(
        intent=_intent(),
        local_decision=_local_decision(),
        binding=_binding(),
        snapshot=_snapshot(),
    )
    repeated = build_portal_risk_request(
        intent=_intent(),
        local_decision=_local_decision(),
        binding=_binding(),
        snapshot=_snapshot(),
    )

    assert request == repeated
    assert request.request_sha256 == repeated.request_sha256
    assert request.portal_trade_intent.side is TradeSide.BUY
    assert request.portal_trade_intent.amount == Decimal("3")
    assert request.portal_snapshot.intent_notional == Decimal("300")
    assert request.portal_snapshot.projected_gross_exposure == Decimal("1300")
    assert request.portal_snapshot.projected_open_positions == 3
    assert request.execution_adapter_authorized is False
    assert request.live_capital_authorized is False


@pytest.mark.parametrize(
    ("decision", "binding", "snapshot"),
    [
        (_local_decision(outcome=RiskOutcome.REJECT), _binding(), _snapshot()),
        (_local_decision(), _binding(policy="other-policy"), _snapshot()),
        (
            _local_decision(),
            _binding(),
            _snapshot(observed_at_ms=1_700_000_002_000),
        ),
    ],
)
def test_build_portal_request_fails_closed(
    decision: RiskDecision,
    binding: PortalRiskBinding,
    snapshot: PortalRiskSnapshotSource,
) -> None:
    with pytest.raises(PortalRiskBridgeBlockedError):
        build_portal_risk_request(
            intent=_intent(),
            local_decision=decision,
            binding=binding,
            snapshot=snapshot,
        )


def test_production_binding_is_forbidden() -> None:
    with pytest.raises(PortalRiskBridgeBlockedError):
        _binding(environment=Environment.PRODUCTION)


def test_validate_and_persist_terminal_portal_evidence(tmp_path) -> None:
    request = build_portal_risk_request(
        intent=_intent(),
        local_decision=_local_decision(),
        binding=_binding(),
        snapshot=_snapshot(),
    )
    result = _approved_result(request)

    validate_portal_risk_result(request=request, result=result)
    artifacts = persist_portal_risk_evidence(
        output_root=tmp_path / "one",
        request=request,
        result=result,
    )
    repeated = persist_portal_risk_evidence(
        output_root=tmp_path / "two",
        request=request,
        result=result,
    )

    assert artifacts.request_sha256 == repeated.request_sha256
    assert artifacts.result_sha256 == repeated.result_sha256
    assert artifacts.manifest_sha256 == repeated.manifest_sha256
    assert artifacts.request_path.is_file()
    assert artifacts.result_path is not None
    assert artifacts.result_path.is_file()
    manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "approved"
    assert manifest["order_submission_performed"] is False
    assert manifest["execution_adapter_called"] is False
    assert manifest["live_capital_authorized"] is False

    with pytest.raises(FileExistsError):
        persist_portal_risk_evidence(
            output_root=tmp_path / "one",
            request=request,
            result=result,
        )


def test_portal_result_policy_mismatch_is_rejected() -> None:
    request = build_portal_risk_request(
        intent=_intent(),
        local_decision=_local_decision(),
        binding=_binding(),
        snapshot=_snapshot(),
    )
    approved = _approved_result(request)
    tampered_decision = approved.risk_decision.model_copy(
        update={"risk_policy_version": "tampered-policy"}
    )
    tampered = approved.model_copy(update={"risk_decision": tampered_decision})

    with pytest.raises(PortalRiskEvidenceMismatchError):
        validate_portal_risk_result(request=request, result=tampered)
