from __future__ import annotations

import hashlib
import inspect
import math
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from strategy_engine.features.records import make_confirmed_htf_record
from strategy_engine.validation.leakage import (
    LeakageError,
    LeakageReason,
    assert_features_available,
)

from ai_platform.portal.contracts.execution import RuntimeHealthState
from ai_platform.portal.risk.schema import RiskEvaluationSnapshot, RiskPolicyLimits
from ai_platform.research.strategy_engine import ase00_adapter
from ai_platform.research.strategy_engine.ase00_adapter import (
    AcceptedSyntheticEvent,
    Ase00Reason,
    Ase00ShadowEngine,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CODE_HASH = hashlib.sha256(b"ase00-code").hexdigest()
SOURCE_VERSION = hashlib.sha256(b"accepted-synthetic-dataset-v1").hexdigest()
START = datetime(2026, 7, 28, 0, 0, tzinfo=UTC)


def _event_id(kind: str, index: int) -> str:
    return hashlib.sha256(f"{kind}:{index}".encode()).hexdigest()


def _events() -> list[AcceptedSyntheticEvent]:
    events: list[AcceptedSyntheticEvent] = []
    for index in range(60):
        event_time = START + timedelta(minutes=5 * index)
        close = 100.0 + math.sin(index / 2.0) * 6.0 + index * 0.08
        open_price = close - math.sin(index) * 0.4
        high = max(open_price, close) + 1.1
        low = min(open_price, close) - 1.1
        event_id = _event_id("market", index)
        events.append(
            AcceptedSyntheticEvent(
                event_id=event_id,
                idempotency_key=event_id,
                kind="market_bar",
                symbol="BTC/USDT:USDT",
                timeframe="5m",
                event_time=event_time,
                detected_at=event_time,
                available_at=event_time + timedelta(milliseconds=25),
                source="accepted-synthetic-market",
                is_confirmed=True,
                source_data_version=SOURCE_VERSION,
                payload={
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1000.0 + index,
                },
            )
        )
    liquidation_time = START + timedelta(minutes=5 * 59, seconds=1)
    liquidation_id = _event_id("liquidation", 1)
    events.append(
        AcceptedSyntheticEvent(
            event_id=liquidation_id,
            idempotency_key=liquidation_id,
            kind="liquidation",
            symbol="BTC/USDT:USDT",
            timeframe="5m",
            event_time=liquidation_time,
            detected_at=liquidation_time + timedelta(milliseconds=50),
            available_at=liquidation_time + timedelta(milliseconds=100),
            source="accepted-synthetic-liquidation",
            is_confirmed=True,
            source_data_version=SOURCE_VERSION,
            payload={"notional_z": 3.5, "side": "long", "notional": 250000.0},
        )
    )
    return events


def _strategy() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "strategy_id": "ase00-synthetic",
        "version": "1.0.0",
        "universe": {"symbols": ["BTC/USDT:USDT"], "timeframes": ["5m"]},
        "features": [
            {
                "id": "squeeze_ratio.v1",
                "params": {
                    "bb_length": 20,
                    "bb_mult": 2.0,
                    "kc_length": 20,
                    "kc_mult": 1.5,
                    "use_true_range": True,
                    "compatibility_mode": "corrected",
                },
                "timeframe": "5m",
                "confirmation": "closed_bar",
            },
            {
                "id": "supertrend_direction.v1",
                "params": {
                    "atr_period": 10,
                    "multiplier": 3.0,
                    "atr_type": "rma",
                    "source": "hl2",
                },
                "timeframe": "5m",
                "confirmation": "closed_bar",
            },
            {
                "id": "confirmed_pivot.v1",
                "params": {"left_bars": 2, "right_bars": 2},
                "timeframe": "5m",
                "confirmation": "closed_bar",
            },
            {
                "id": "liquidation_notional_z.v1",
                "params": {"window": 20, "cluster_seconds": 60},
                "timeframe": "5m",
                "confirmation": "closed_bar",
            },
        ],
        "regime": {
            "all": [
                {
                    "feature": "supertrend_direction.v1",
                    "parameter": "direction",
                    "op": "in_range",
                    "value": [-1, 1],
                }
            ]
        },
        "entry_long": {
            "all": [
                {
                    "feature": "squeeze_ratio.v1",
                    "parameter": "squeeze_ratio",
                    "op": "gt",
                    "value": 0,
                },
                {
                    "feature": "confirmed_pivot.v1",
                    "parameter": "level",
                    "op": "gt",
                    "value": 0,
                },
                {
                    "feature": "liquidation_notional_z.v1",
                    "parameter": "notional_z",
                    "op": "gt",
                    "value": 1,
                },
            ]
        },
        "entry_short": None,
        "exit": {"any": [{"event": "supertrend_flip", "direction": "down"}]},
        "risk": {
            "max_leverage": 1,
            "max_open_positions": 1,
            "position_size": {"type": "risk_fraction", "value": 0.01},
            "max_exposure": 0.1,
        },
        "execution": {
            "signal_delay_ms": 0,
            "order_type": "market",
            "slippage_model": "none",
            "fee_model": "none",
            "use_closed_bars_only": True,
        },
        "provenance": {
            "producer": "ase00-test",
            "source_event_id": "strategy:ase00-synthetic",
            "details": {
                "lineage_complete": True,
                "future_shift": 0,
                "research_mode": True,
            },
        },
    }


def _limits() -> RiskPolicyLimits:
    return RiskPolicyLimits(
        max_order_notional=Decimal(1000),
        max_projected_gross_exposure=Decimal(5000),
        max_projected_open_positions=3,
        max_daily_loss=Decimal(500),
        max_drawdown=Decimal("0.20"),
        require_healthy_runtime=True,
    )


def _snapshot(*, intent_notional: str = "100") -> RiskEvaluationSnapshot:
    return RiskEvaluationSnapshot(
        intent_notional=Decimal(intent_notional),
        projected_gross_exposure=Decimal(100),
        projected_open_positions=1,
        daily_loss=Decimal(0),
        current_drawdown=Decimal(0),
        runtime_health=RuntimeHealthState.HEALTHY,
    )


def _engine() -> Ase00ShadowEngine:
    return Ase00ShadowEngine(code_hash=CODE_HASH, repository_root=REPO_ROOT)


def _decision_time() -> datetime:
    return max(event.available_at for event in _events()) + timedelta(seconds=1)


def test_complete_synthetic_shadow_flow_uses_existing_risk_core() -> None:
    evidence = _engine().run(
        events=_events(),
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    assert evidence.risk_outcome == "approved"
    assert evidence.signal is not None
    assert evidence.signal.action.value == "enter"
    assert {record.feature_id for record in evidence.feature_records} == {
        "squeeze_ratio.v1",
        "supertrend_direction.v1",
        "confirmed_pivot.v1",
        "liquidation_notional_z.v1",
    }
    assert "RISK_APPROVED" in evidence.reason_codes
    assert evidence.no_order_submitted
    assert evidence.provenance.details["execution_adapter_used"] is False


def test_duplicate_event_is_idempotent() -> None:
    events = _events()
    first = _engine().run(
        events=events,
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    duplicate = _engine().run(
        events=[*events, events[-1]],
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    assert duplicate.signal == first.signal
    assert duplicate.feature_records == first.feature_records
    assert Ase00Reason.DUPLICATE_EVENT_IGNORED in duplicate.reason_codes


def test_delayed_event_is_accepted_when_available_before_decision() -> None:
    events = _events()
    events[-1] = replace(
        events[-1],
        available_at=events[-1].detected_at + timedelta(seconds=2),
    )
    decision_time = events[-1].available_at + timedelta(seconds=1)
    evidence = _engine().run(
        events=events,
        strategy_document=_strategy(),
        decision_time=decision_time,
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    assert evidence.risk_outcome == "approved"
    assert Ase00Reason.DELAYED_EVENT_ACCEPTED in evidence.reason_codes


def test_out_of_order_event_input_is_normalized() -> None:
    ordered = _engine().run(
        events=_events(),
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    reversed_input = _engine().run(
        events=list(reversed(_events())),
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    assert ordered.feature_records == reversed_input.feature_records
    assert ordered.signal == reversed_input.signal
    assert Ase00Reason.OUT_OF_ORDER_EVENT_NORMALIZED in reversed_input.reason_codes


def test_future_feature_is_rejected_fail_closed() -> None:
    events = _events()
    decision_time = _decision_time()
    events[-2] = replace(events[-2], available_at=decision_time + timedelta(seconds=1))
    evidence = _engine().run(
        events=events,
        strategy_document=_strategy(),
        decision_time=decision_time,
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    assert evidence.risk_outcome == "rejected"
    assert Ase00Reason.LEAKAGE_GUARD_REJECTED in evidence.reason_codes
    assert LeakageReason.FEATURE_AFTER_DECISION.value in evidence.reason_codes
    assert evidence.no_order_submitted


def test_unconfirmed_pivot_is_rejected() -> None:
    events = _events()
    baseline = _engine().run(
        events=events,
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    pivot = next(
        record for record in baseline.feature_records if record.feature_id == "confirmed_pivot.v1"
    )
    source_id = pivot.provenance.source_event_id
    events = [
        replace(event, is_confirmed=False) if event.event_id == source_id else event
        for event in events
    ]
    evidence = _engine().run(
        events=events,
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    assert evidence.risk_outcome == "rejected"
    assert LeakageReason.PIVOT_BEFORE_CONFIRMATION.value in evidence.reason_codes


def test_unconfirmed_htf_record_is_rejected() -> None:
    decision_time = START + timedelta(minutes=59)
    record = make_confirmed_htf_record(
        feature_id="supertrend_direction.v1",
        symbol="BTC/USDT:USDT",
        timeframe="1h",
        bar_open_time=START,
        bar_duration=timedelta(hours=1),
        processing_latency=timedelta(0),
        decision_time=decision_time,
        value={"value": 1},
        source="synthetic-htf",
        idempotency_key="htf:open",
        code_version=CODE_HASH,
        data_version=SOURCE_VERSION,
        configuration_hash=hashlib.sha256(b"config").hexdigest(),
        producer="ase00-test",
        source_event_id="htf:bar",
    )
    try:
        assert_features_available((record,), decision_time)
    except LeakageError as exc:
        assert exc.reason_code in {
            LeakageReason.FEATURE_AFTER_DECISION,
            LeakageReason.UNCONFIRMED_FEATURE,
            LeakageReason.HTF_BAR_NOT_CLOSED,
        }
    else:
        raise AssertionError("unconfirmed HTF record was accepted")


def test_existing_risk_core_rejection_is_preserved() -> None:
    evidence = _engine().run(
        events=_events(),
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(intent_notional="1001"),
    )
    assert evidence.risk_outcome == "rejected"
    assert "ORDER_NOTIONAL_LIMIT_EXCEEDED" in evidence.reason_codes
    assert evidence.signal is not None
    assert evidence.no_order_submitted


def test_restart_and_replay_produces_identical_evidence(tmp_path: Path) -> None:
    path = tmp_path / "shadow-evidence.json"
    first = _engine().run(
        events=_events(),
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
        evidence_path=path,
    )
    first_bytes = path.read_bytes()
    second = _engine().run(
        events=_events(),
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
        evidence_path=path,
    )
    assert second == first
    assert second.evidence_hash == first.evidence_hash
    assert path.read_bytes() == first_bytes


def test_missing_liquidation_data_fails_closed() -> None:
    events = [event for event in _events() if event.kind == "market_bar"]
    evidence = _engine().run(
        events=events,
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    assert evidence.risk_outcome == "rejected"
    assert Ase00Reason.MISSING_REQUIRED_DATA in evidence.reason_codes
    assert evidence.signal is None
    assert evidence.no_order_submitted


def test_conflicting_duplicate_fails_closed_with_reason_code() -> None:
    events = _events()
    conflict = replace(events[-1], payload={"notional_z": -9.0})
    evidence = _engine().run(
        events=[*events, conflict],
        strategy_document=_strategy(),
        decision_time=_decision_time(),
        risk_limits=_limits(),
        risk_snapshot=_snapshot(),
    )
    assert evidence.risk_outcome == "rejected"
    assert Ase00Reason.CONFLICTING_DUPLICATE_EVENT in evidence.reason_codes
    assert evidence.no_order_submitted


def test_adapter_has_no_execution_or_freqtrade_dependency() -> None:
    source = inspect.getsource(ase00_adapter)
    assert "ai_platform.portal.execution" not in source
    assert "ExecutionAdapter" not in source
    assert "submit_approved_intent" not in source
    assert "freqtrade" not in source.lower()
