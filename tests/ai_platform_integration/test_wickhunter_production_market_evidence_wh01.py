from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from ai_platform.wickhunter.production_market_evidence_service import EXPECTED_AUTHORITY
from ai_platform.wickhunter.production_market_evidence_wh01 import (
    MetricLookbacks,
    _active_sources_as_of,
    _safe_member,
    _source_metrics,
    build_wh01_input_package,
    load_policy,
)


POLICY_PATH = Path(
    "ai_platform/wickhunter/policies/wickhunter-production-market-evidence-wh01-policy-v1.json"
)
TIMEFRAME_MS = 300_000


def _candles(*, start_ms: int, count: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(count):
        open_ms = start_ms + index * TIMEFRAME_MS
        close = "999" if index == count - 1 else "100"
        rows.append(
            {
                "source": "binance-usdm",
                "symbol": "BTCUSDT",
                "open_time_ms": open_ms,
                "close_time_ms_exclusive": open_ms + TIMEFRAME_MS,
                "open": "100",
                "high": "101",
                "low": "99",
                "close": close,
                "base_volume": "10",
                "quote_volume": "1000",
            }
        )
    return rows


def test_frozen_policy_declares_24h_maximum_lookback() -> None:
    policy = load_policy(POLICY_PATH)
    assert policy.lookbacks.maximum_rows == 288
    assert policy.source_aggregation == "source_balanced_mean_require_all"
    assert policy.required_sources == ("bybit-linear", "binance-usdm")
    assert policy.label_horizon_ms == 0
    assert policy.embargo_ms == 0


def test_source_metrics_do_not_read_future_candle() -> None:
    start_ms = 1_000_000
    decision_ms = start_ms + 288 * TIMEFRAME_MS
    values = _source_metrics(
        _candles(start_ms=start_ms, count=289),
        decision_ms,
        MetricLookbacks(
            quote_volume_rows=288,
            vwap_rows=288,
            vwma_rows=288,
            atr_rows=14,
            volatility_rows=287,
            wick_rows=288,
            trend_rows=288,
        ),
    )
    assert values["decision_price"] == Decimal("100")
    assert values["quote_volume_24h_usd"] == Decimal("288000")


def test_source_metrics_volatility_ratio_is_return_standard_deviation() -> None:
    start_ms = 1_000_000
    closes = (Decimal("100"), Decimal("101"), Decimal("99"), Decimal("102"))
    candles = _candles(start_ms=start_ms, count=len(closes))
    for row, close in zip(candles, closes, strict=True):
        row["open"] = str(close)
        row["high"] = str(close + Decimal("1"))
        row["low"] = str(close - Decimal("1"))
        row["close"] = str(close)
        row["quote_volume"] = str(close * Decimal("10"))

    values = _source_metrics(
        candles,
        start_ms + len(closes) * TIMEFRAME_MS,
        MetricLookbacks(
            quote_volume_rows=1,
            vwap_rows=1,
            vwma_rows=1,
            atr_rows=1,
            volatility_rows=3,
            wick_rows=1,
            trend_rows=1,
        ),
    )
    returns = tuple(
        current / previous - Decimal(1)
        for previous, current in zip(closes[:-1], closes[1:], strict=True)
    )
    return_mean = sum(returns, Decimal(0)) / Decimal(len(returns))
    expected = (
        sum(((value - return_mean) ** 2 for value in returns), Decimal(0))
        / Decimal(len(returns))
    ).sqrt()

    assert values["volatility_ratio"] == expected
    assert values["volatility_ratio"] < Decimal("0.50")


def test_instrument_history_is_selected_as_of_decision_time() -> None:
    rows = [
        {
            "source": "binance-usdm",
            "canonical_symbol": "BTCUSDT",
            "available_at_ms": 1_000,
            "active": True,
        },
        {
            "source": "bybit-linear",
            "canonical_symbol": "BTCUSDT",
            "available_at_ms": 1_100,
            "active": True,
        },
        {
            "source": "bybit-linear",
            "canonical_symbol": "BTCUSDT",
            "available_at_ms": 2_100,
            "active": False,
        },
    ]
    assert _active_sources_as_of(rows, "BTCUSDT", 2_000) == {
        "binance-usdm",
        "bybit-linear",
    }
    assert _active_sources_as_of(rows, "BTCUSDT", 2_200) == {"binance-usdm"}


def test_missing_liquidation_binding_returns_blocked_without_output(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "wh01-input"
    result = build_wh01_input_package(
        evidence_package_root=tmp_path / "missing-evidence",
        accepted_import_roots=(),
        policy_path=POLICY_PATH,
        output_root=output_root,
    )
    assert result == {
        "schema_version": "wickhunter-production-market-evidence-wh01-report-v1",
        "status": "blocked",
        "blocker_code": "LIQUIDATION_ARCHIVE_NOT_BOUND",
        "blocker_detail": (
            "At least one real accepted immutable liquidation import must be bound."
        ),
        **EXPECTED_AUTHORITY,
    }
    assert not output_root.exists()


def test_safe_member_rejects_path_traversal_and_symlink(
    tmp_path: Path,
) -> None:
    root = tmp_path / "run"
    root.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(Exception, match="relative"):
        _safe_member(root, "../outside.json")

    link = root / "link.json"
    link.symlink_to(outside)
    with pytest.raises(Exception, match="symlink"):
        _safe_member(root, "link.json")
