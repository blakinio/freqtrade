from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
ALLOWED_CLASSIFICATIONS = {"confirmed_ui", "probable", "unknown"}


def _classified_names(section: Mapping[str, Any]) -> set[str]:
    names: set[str] = set()
    for classification in ALLOWED_CLASSIFICATIONS:
        values = section[classification]
        if isinstance(values, Mapping):
            names.update(str(key) for key in values)
        elif isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
            names.update(str(value) for value in values)
        else:
            raise TypeError(f"invalid classification payload: {classification}")
    return names


def test_miyagi_map_is_research_only_and_has_no_parity_claim() -> None:
    document = yaml.safe_load(
        (ROOT / "configs/miyagi_parameter_map.v1.yaml").read_text(encoding="utf-8")
    )
    assert document["source_policy"] == {
        "parity_claim": False,
        "execution_dependency": False,
        "provenance_only": True,
    }
    for section_name in ("miyagi_10_in_1", "miyagi_bonsai"):
        assert set(document[section_name]) == ALLOWED_CLASSIFICATIONS


def test_all_requested_research_hypotheses_are_classified() -> None:
    document = yaml.safe_load(
        (ROOT / "configs/miyagi_parameter_map.v1.yaml").read_text(encoding="utf-8")
    )
    ten_in_one = _classified_names(document["miyagi_10_in_1"])
    assert {
        "ema",
        "macd",
        "rsi",
        "stochastic_rsi",
        "vwap",
        "squeeze",
        "adx",
        "supertrend",
        "mfi",
        "roc",
        "wavetrend",
        "psar",
        "price_action",
        "alerts",
        "no_repeat_signals",
        "cooldown",
    } <= ten_in_one

    bonsai = _classified_names(document["miyagi_bonsai"])
    assert {
        "atr_range_filter",
        "fibonacci_period_ma_ensemble",
        "volume_filter",
        "rsi_filter",
        "adx_filter",
        "mfi_filter",
        "time_filter",
        "take_profit",
        "stop_loss",
        "trailing_exit",
        "partial_take_profit",
        "bounded_dca",
        "leverage_limits",
        "sizing",
        "pair_universe_limit",
    } <= bonsai


def test_miyagi_name_is_absent_from_runtime_provider_source() -> None:
    runtime_source = ROOT / "src/strategy_engine"
    offending = [
        str(path.relative_to(ROOT))
        for path in runtime_source.rglob("*.py")
        if "miyagi" in path.read_text(encoding="utf-8").lower()
    ]
    assert offending == []
