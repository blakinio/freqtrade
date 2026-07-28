from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest

from strategy_engine.domain.models import Action, Side
from strategy_engine.dsl.evaluator import EvaluationSnapshot, StrategyEvaluator
from strategy_engine.dsl.validator import StrategyValidationError, StrategyValidator
from strategy_engine.registry import FeatureRegistry, RegistryError, SearchSpaceRegistry

ROOT = Path(__file__).resolve().parents[2]


def _registries() -> tuple[FeatureRegistry, SearchSpaceRegistry]:
    return (
        FeatureRegistry.load(ROOT / "configs/feature_registry.v1.yaml"),
        SearchSpaceRegistry.load(ROOT / "configs/search_spaces.v1.yaml"),
    )


def _strategy() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "strategy_id": "ase00-test",
        "version": "1.0.0",
        "universe": {"symbols": ["BTC/USDT"], "timeframes": ["5m"]},
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
        ],
        "regime": {
            "all": [
                {
                    "feature": "supertrend_direction.v1",
                    "parameter": "direction",
                    "op": "eq",
                    "value": 1,
                }
            ]
        },
        "entry_long": {
            "all": [
                {
                    "feature": "squeeze_ratio.v1",
                    "parameter": "squeeze_ratio",
                    "op": "lt",
                    "value": 2.0,
                },
                {
                    "feature": "confirmed_pivot.v1",
                    "parameter": "kind",
                    "op": "eq",
                    "value": "low",
                },
            ],
            "none": [{"event": "cooldown_active"}],
        },
        "entry_short": None,
        "exit": {"any": [{"event": "exit", "direction": "hit"}]},
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
            "producer": "test",
            "source_event_id": "strategy:test",
            "details": {
                "lineage_complete": True,
                "future_shift": 0,
                "research_mode": True,
            },
        },
    }


def test_registry_loads_versions_dependencies_and_policies() -> None:
    registry, spaces = _registries()
    squeeze = registry.get("squeeze_ratio.v1")
    assert registry.version == "1.0.0"
    assert spaces.version == "1.0.0"
    assert squeeze.timestamp_policy == "closed_bar"
    assert squeeze.normalization_policy
    assert squeeze.warmup
    assert registry.resolve_dependencies(("bos_choch.v1",)) == (
        "confirmed_pivot.v1",
        "bos_choch.v1",
    )


def test_registry_rejects_unknown_and_out_of_range_parameters() -> None:
    registry, _ = _registries()
    with pytest.raises(RegistryError):
        registry.get("not-registered.v1")
    with pytest.raises(RegistryError):
        registry.validate_parameters("squeeze_ratio.v1", {"bb_length": 2})


def test_search_space_keeps_legacy_squeeze_test_only() -> None:
    _, spaces = _registries()
    with pytest.raises(RegistryError):
        spaces.get("squeeze").validate_parameters({"compatibility_mode": "legacy_bug_compatible"})
    spaces.get("squeeze").validate_parameters({"compatibility_mode": "corrected"})


def test_registry_to_dsl_validation_and_feature_resolution() -> None:
    registry, spaces = _registries()
    validator = StrategyValidator(registry, spaces)
    strategy = validator.validate(_strategy())
    assert [feature.id for feature in strategy.features] == [
        "squeeze_ratio.v1",
        "supertrend_direction.v1",
        "confirmed_pivot.v1",
    ]


def test_dsl_rejects_feature_outside_registry() -> None:
    registry, spaces = _registries()
    document = _strategy()
    features = [dict(feature) for feature in cast(list[dict[str, object]], document["features"])]
    features[0] = {
        "id": "unknown.v1",
        "params": {},
        "timeframe": "5m",
        "confirmation": "closed_bar",
    }
    document["features"] = features
    with pytest.raises(StrategyValidationError) as captured:
        StrategyValidator(registry, spaces).validate(document)
    assert captured.value.reason_code == "FEATURE_REGISTRY_REJECTED"


def test_dsl_rejects_undeclared_timeframe() -> None:
    registry, spaces = _registries()
    document = _strategy()
    features = [dict(feature) for feature in cast(list[dict[str, object]], document["features"])]
    features[0] = {**features[0], "timeframe": "1h"}
    document["features"] = features
    with pytest.raises(StrategyValidationError) as captured:
        StrategyValidator(registry, spaces).validate(document)
    assert captured.value.reason_code == "UNDECLARED_TIMEFRAME"


def test_declarative_all_any_none_evaluator_enters_long() -> None:
    registry, spaces = _registries()
    strategy = StrategyValidator(registry, spaces).validate(_strategy())
    decision = StrategyEvaluator().evaluate(
        strategy,
        EvaluationSnapshot(
            features={
                "squeeze_ratio.v1": {"squeeze_ratio": 0.8},
                "supertrend_direction.v1": {"direction": 1},
                "confirmed_pivot.v1": {"kind": "low", "level": 100.0},
            },
            previous_features={},
            events={"cooldown_active": False, "exit": "none"},
            risk={},
        ),
    )
    assert decision.side is Side.LONG
    assert decision.action is Action.ENTER


def test_evaluator_handles_crosses_and_risk_named_values() -> None:
    document = _strategy()
    document["entry_long"] = {
        "all": [
            {
                "feature": "squeeze_ratio.v1",
                "parameter": "squeeze_ratio",
                "op": "crosses_above",
                "value": 1.0,
            }
        ],
        "none": [{"risk": "blocked"}],
    }
    registry, spaces = _registries()
    strategy = StrategyValidator(registry, spaces).validate(document)
    decision = StrategyEvaluator().evaluate(
        strategy,
        EvaluationSnapshot(
            features={
                "squeeze_ratio.v1": {"squeeze_ratio": 1.1},
                "supertrend_direction.v1": {"direction": 1},
                "confirmed_pivot.v1": {"kind": "low"},
            },
            previous_features={"squeeze_ratio.v1": {"squeeze_ratio": 0.9}},
            events={"exit": "none"},
            risk={"blocked": False},
        ),
    )
    assert decision.action is Action.ENTER


def test_validation_report_is_deterministic_at_fixed_time() -> None:
    registry, spaces = _registries()
    checked_at = datetime(2026, 7, 28, tzinfo=UTC)
    validator = StrategyValidator(registry, spaces)
    first = validator.validate_report(_strategy(), checked_at=checked_at)
    second = validator.validate_report(_strategy(), checked_at=checked_at)
    assert first == second
    assert first.valid
