from __future__ import annotations

import json
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import pytest

from ai_platform.wickhunter.contracts import (
    BotMode,
    DriftState,
    LiquidationSourceState,
    RiskOutcome,
    ShadowDecisionEvidence,
    ShadowStatus,
    SourceHealth,
    StrategyHypothesis,
    TradeDirection,
)
from ai_platform.wickhunter.deterministic_replay import CandidateLabel, LabelOutcome
from ai_platform.wickhunter.shadow import ShadowDecisionRequest
from ai_platform.wickhunter.shadow_runtime import (
    PositionCloseReason,
    RuntimeHealth,
    ShadowRuntime,
    ShadowRuntimeError,
    ShadowRuntimePolicy,
    ShadowRuntimeStore,
    ShadowRuntimeTick,
    initial_runtime_state,
    verify_replay_shadow_parity,
)
from ai_platform.wickhunter.universe import (
    DynamicUniverseSnapshot,
    UniverseInstrumentDecision,
)


OBSERVED_MS = 2_000_000
DATASET_HASH = "d" * 64
CODE_SHA = "a" * 40
PARAMETER_HASH = "b" * 64
MODEL_HASH = "c" * 64


def _policy(**overrides: object) -> ShadowRuntimePolicy:
    values: dict[str, object] = {
        "policy_version": "wickhunter-shadow-runtime-policy-v1",
        "simulated_initial_equity_quote": Decimal("10000"),
        "maximum_universe_age_ms": 60_000,
        "maximum_source_age_ms": 30_000,
        "minimum_healthy_sources": 1,
        "maximum_open_positions": 3,
        "maximum_drawdown_ratio": Decimal("0.20"),
        "decision_history_limit": 10,
    }
    values.update(overrides)
    return ShadowRuntimePolicy(**values)  # type: ignore[arg-type]


def _universe(*, selected_at_ms: int = OBSERVED_MS - 1_000) -> DynamicUniverseSnapshot:
    return DynamicUniverseSnapshot(
        schema_version="wickhunter-dynamic-universe-v1",
        policy_version="wickhunter-dynamic-universe-policy-v1",
        selected_at_ms=selected_at_ms,
        decisions=(
            UniverseInstrumentDecision(
                canonical_instrument_id="bybit:perpetual:BTCUSDT",
                canonical_symbol="BTCUSDT",
                included=True,
                reason_codes=("eligible",),
            ),
        ),
    )


def _source_state(
    *,
    health: SourceHealth = SourceHealth.HEALTHY,
    last_received_at_ms: int | None = OBSERVED_MS - 1_000,
    observed_at_ms: int = OBSERVED_MS - 500,
) -> LiquidationSourceState:
    return LiquidationSourceState(
        source="bybit-linear",
        health=health,
        coverage_available=health is SourceHealth.HEALTHY,
        last_received_at_ms=last_received_at_ms,
        observed_at_ms=observed_at_ms,
    )


def _request(
    *,
    universe: DynamicUniverseSnapshot,
    decision_timestamp_ms: int = OBSERVED_MS - 100,
) -> ShadowDecisionRequest:
    request = SimpleNamespace(
        bot_instance="wickhunter-shadow-1",
        mode=BotMode.SHADOW,
        universe=universe,
        market=SimpleNamespace(
            symbol="BTCUSDT",
            decision_timestamp_ms=decision_timestamp_ms,
        ),
        hypothesis=StrategyHypothesis.REVERSAL,
    )
    return cast(ShadowDecisionRequest, request)


def _allowed_evidence(
    *,
    decision_timestamp_ms: int = OBSERVED_MS - 100,
    decision_price: Decimal = Decimal("100"),
    trade_intent_id: str = "1" * 64,
    shadow_decision_id: str = "2" * 64,
    dataset_hash: str = DATASET_HASH,
    code_sha: str = CODE_SHA,
) -> ShadowDecisionEvidence:
    candidate = SimpleNamespace(
        candidate_id="3" * 64,
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        decision_timestamp_ms=decision_timestamp_ms,
        reason_codes=("reversal_long",),
    )
    score = SimpleNamespace(score_id="4" * 64)
    intent = SimpleNamespace(
        trade_intent_id=trade_intent_id,
        symbol="BTCUSDT",
        side=TradeDirection.LONG,
        decision_timestamp_ms=decision_timestamp_ms,
        decision_price=decision_price,
        requested_base_risk_ratio=Decimal("0.01"),
        requested_leverage=Decimal("2"),
        take_profit_ratio=Decimal("0.02"),
        stop_loss_ratio=Decimal("0.01"),
        dca_plan=SimpleNamespace(maximum_total_risk_ratio=Decimal("0.02")),
        model_version="wickhunter-lightgbm-v1",
        model_hash=MODEL_HASH,
        parameter_version="wickhunter-parameters-v1",
        parameter_hash=PARAMETER_HASH,
        dataset_hash=dataset_hash,
        code_sha=code_sha,
    )
    risk = SimpleNamespace(
        risk_decision_id="5" * 64,
        outcome=RiskOutcome.ALLOW,
        reason_codes=("risk_allowed",),
    )
    evidence = SimpleNamespace(
        shadow_decision_id=shadow_decision_id,
        status=ShadowStatus.SIMULATED_ALLOWED,
        candidate=candidate,
        score=score,
        trade_intent=intent,
        risk_decision=risk,
    )
    return cast(ShadowDecisionEvidence, evidence)


def _tick(
    *,
    observed_at_ms: int = OBSERVED_MS,
    universe: DynamicUniverseSnapshot | None = None,
    requests: tuple[ShadowDecisionRequest, ...] = (),
    mark_price: Decimal = Decimal("100"),
    source_state: LiquidationSourceState | None = None,
    model_drift: DriftState = DriftState.HEALTHY,
    data_drift: DriftState = DriftState.HEALTHY,
) -> ShadowRuntimeTick:
    return ShadowRuntimeTick(
        observed_at_ms=observed_at_ms,
        universe=universe or _universe(),
        decision_requests=requests,
        mark_prices=(("BTCUSDT", mark_price),),
        source_states=(source_state or _source_state(),),
        model_drift=model_drift,
        data_drift=data_drift,
        validation_state="accepted_candidate_only",
        retraining_state="idle",
    )


def _runtime(
    *,
    evaluator=None,
    store: ShadowRuntimeStore | None = None,
    policy: ShadowRuntimePolicy | None = None,
) -> ShadowRuntime:
    kwargs = {}
    if evaluator is not None:
        kwargs["decision_evaluator"] = evaluator
    return ShadowRuntime(
        bot_instance="wickhunter-shadow-1",
        mode=BotMode.SHADOW,
        policy=policy or _policy(),
        store=store,
        **kwargs,
    )


def _label(**overrides: object) -> CandidateLabel:
    values: dict[str, object] = {
        "schema_version": "wickhunter-candidate-label-v1",
        "label_id": "f" * 64,
        "policy_version": "wickhunter-replay-policy-v1",
        "policy_sha256": "e" * 64,
        "dataset_id": "wickhunter-wh01-production-dataset",
        "dataset_manifest_sha256": DATASET_HASH,
        "market_manifest_sha256": "9" * 64,
        "split_geometry_sha256": "8" * 64,
        "dataset_row_sha256": "7" * 64,
        "price_path_manifest_sha256": "6" * 64,
        "source_commit_sha": CODE_SHA,
        "split_name": "validation",
        "symbol": "BTCUSDT",
        "side": TradeDirection.LONG,
        "decision_timestamp_ms": OBSERVED_MS - 100,
        "label_end_ms": OBSERVED_MS + 900_000,
        "outcome": LabelOutcome.TAKE_PROFIT,
        "entry_timestamp_ms": OBSERVED_MS,
        "entry_aggregate_trade_id": 100,
        "entry_trade_sha256": "5" * 64,
        "raw_entry_price": Decimal("100"),
        "executed_entry_price": Decimal("100.1"),
        "exit_timestamp_ms": OBSERVED_MS + 10_000,
        "exit_aggregate_trade_id": 101,
        "exit_trade_sha256": "4" * 64,
        "raw_exit_price": Decimal("102"),
        "executed_exit_price": Decimal("101.9"),
        "gross_return_ratio": Decimal("0.018"),
        "net_return_ratio": Decimal("0.016"),
        "maximum_favorable_excursion_ratio": Decimal("0.02"),
        "maximum_adverse_excursion_ratio": Decimal("0.002"),
        "time_to_outcome_ms": 10_000,
        "fee_ratio": Decimal("0.0005"),
        "slippage_ratio": Decimal("0.001"),
        "take_profit_ratio": Decimal("0.02"),
        "stop_loss_ratio": Decimal("0.01"),
        "entry_delay_ms": 0,
        "maximum_entry_delay_ms": 5_000,
        "protected_holdout_accessed": False,
        "immutable_inputs_mutated": False,
        "model_execution_authorized": False,
        "performance_research_authorized": False,
        "execution_enabled": False,
        "live_capital_authorized": False,
        "trading_credentials_present": False,
        "orders_submitted": 0,
    }
    values.update(overrides)
    return CandidateLabel(**values)  # type: ignore[arg-type]


def test_initial_state_forbids_live_mode() -> None:
    with pytest.raises(ShadowRuntimeError, match="live mode"):
        initial_runtime_state(
            bot_instance="wickhunter-live",
            mode=BotMode.LIVE_BLOCKED,
            policy=_policy(),
        )


def test_stale_source_fails_closed_without_evaluating() -> None:
    called = False

    def evaluator(_request: ShadowDecisionRequest) -> ShadowDecisionEvidence:
        nonlocal called
        called = True
        return _allowed_evidence()

    runtime = _runtime(evaluator=evaluator)
    stale = _source_state(last_received_at_ms=OBSERVED_MS - 60_000)
    result = runtime.step(
        _tick(
            requests=(_request(universe=_universe()),),
            source_state=stale,
        )
    )
    assert not called
    assert result.snapshot.health is RuntimeHealth.FAIL_CLOSED
    assert result.snapshot.circuit_breaker_active
    assert "insufficient_fresh_sources" in result.snapshot.circuit_breaker_reasons
    assert result.snapshot.orders_submitted == 0
    assert not result.snapshot.trading_credentials_present
    assert not result.snapshot.order_adapter_present
    assert not result.snapshot.live_capital_authorized


def test_allowed_decision_opens_position_and_persists_restart(tmp_path) -> None:
    universe = _universe()
    store = ShadowRuntimeStore(tmp_path / "runtime")
    runtime = _runtime(evaluator=lambda _request: _allowed_evidence(), store=store)
    result = runtime.step(
        _tick(
            universe=universe,
            requests=(_request(universe=universe),),
        )
    )
    assert len(result.state.positions) == 1
    position = result.state.positions[0]
    assert position.symbol == "BTCUSDT"
    assert position.quantity == Decimal("4.00000000")
    assert result.snapshot.dynamic_universe == ("BTCUSDT",)
    assert result.snapshot.model_hash == MODEL_HASH
    assert result.snapshot.parameter_hash == PARAMETER_HASH
    assert result.snapshot.dataset_hash == DATASET_HASH
    assert result.snapshot.code_sha == CODE_SHA
    assert result.snapshot.read_only
    assert store.snapshot_path.is_file()
    persisted_snapshot = json.loads(store.snapshot_path.read_text(encoding="utf-8"))
    assert persisted_snapshot["snapshot_id"] == result.snapshot.snapshot_id
    assert persisted_snapshot["orders_submitted"] == 0

    restarted = _runtime(evaluator=lambda _request: _allowed_evidence(), store=store)
    assert restarted.state == result.state
    assert restarted.state.state_sha256 == result.state.state_sha256


def test_mark_price_closes_position_at_take_profit() -> None:
    universe = _universe()
    runtime = _runtime(evaluator=lambda _request: _allowed_evidence())
    first = runtime.step(
        _tick(
            universe=universe,
            requests=(_request(universe=universe),),
        )
    )
    assert first.state.positions
    second = runtime.step(
        _tick(
            observed_at_ms=OBSERVED_MS + 1_000,
            universe=DynamicUniverseSnapshot(
                schema_version=universe.schema_version,
                policy_version=universe.policy_version,
                selected_at_ms=OBSERVED_MS,
                decisions=universe.decisions,
            ),
            mark_price=Decimal("103"),
            source_state=_source_state(
                last_received_at_ms=OBSERVED_MS,
                observed_at_ms=OBSERVED_MS,
            ),
        )
    )
    assert second.state.positions == ()
    assert len(second.closed_positions) == 1
    assert second.closed_positions[0].close_reason is PositionCloseReason.TAKE_PROFIT
    assert second.closed_positions[0].realized_pnl_quote == Decimal("8.00000000")
    assert second.state.cumulative_realized_pnl_quote == Decimal("8.00000000")


def test_duplicate_symbol_does_not_open_second_position() -> None:
    universe = _universe()
    evidence_one = _allowed_evidence()
    evidence_two = _allowed_evidence(
        trade_intent_id="a" * 64,
        shadow_decision_id="b" * 64,
    )
    evidence = iter((evidence_one, evidence_two))
    runtime = _runtime(evaluator=lambda _request: next(evidence))
    first = runtime.step(
        _tick(universe=universe, requests=(_request(universe=universe),))
    )
    assert len(first.state.positions) == 1
    fresh_universe = DynamicUniverseSnapshot(
        schema_version=universe.schema_version,
        policy_version=universe.policy_version,
        selected_at_ms=OBSERVED_MS,
        decisions=universe.decisions,
    )
    second = runtime.step(
        _tick(
            observed_at_ms=OBSERVED_MS + 1_000,
            universe=fresh_universe,
            requests=(
                _request(
                    universe=fresh_universe,
                    decision_timestamp_ms=OBSERVED_MS + 500,
                ),
            ),
            source_state=_source_state(
                last_received_at_ms=OBSERVED_MS,
                observed_at_ms=OBSERVED_MS,
            ),
        )
    )
    assert len(second.state.positions) == 1
    assert "runtime_position_already_open" in second.snapshot.decisions[0].reason_codes


def test_runtime_rejects_non_monotonic_tick() -> None:
    runtime = _runtime()
    runtime.step(_tick())
    with pytest.raises(ShadowRuntimeError, match="strictly increasing"):
        runtime.step(_tick())


def test_runtime_fails_closed_on_drift() -> None:
    runtime = _runtime()
    result = runtime.step(_tick(model_drift=DriftState.DRIFTED))
    assert result.snapshot.health is RuntimeHealth.FAIL_CLOSED
    assert "model_drift_not_healthy" in result.snapshot.circuit_breaker_reasons


def test_store_rejects_tampered_state(tmp_path) -> None:
    store = ShadowRuntimeStore(tmp_path / "runtime")
    state = initial_runtime_state(
        bot_instance="wickhunter-shadow-1",
        mode=BotMode.SHADOW,
        policy=_policy(),
    )
    store.save(state)
    payload = json.loads(store.state_path.read_text(encoding="utf-8"))
    payload["state"]["generation"] = 99
    store.state_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ShadowRuntimeError, match="integrity"):
        store.load()


def test_replay_shadow_parity_accepts_exact_identity_and_policy() -> None:
    evidence = _allowed_evidence()
    parity = verify_replay_shadow_parity(
        shadow_decision=evidence,
        label=_label(),
    )
    assert parity.identities_match
    assert parity.policy_match
    assert parity.execution_authority_absent
    assert len(parity.parity_id) == 64


def test_replay_shadow_parity_rejects_mismatched_dataset() -> None:
    evidence = _allowed_evidence(dataset_hash="0" * 64)
    with pytest.raises(ShadowRuntimeError, match="not accepted"):
        verify_replay_shadow_parity(
            shadow_decision=evidence,
            label=_label(),
        )


def test_observability_snapshot_has_no_trade_control_fields() -> None:
    runtime = _runtime()
    snapshot = runtime.step(_tick()).snapshot
    payload = snapshot.__dataclass_fields__
    assert "read_only" in payload
    assert "orders_submitted" in payload
    assert "trade_button" not in payload
    assert "submit_order" not in payload
