from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from ai_platform.market_data.contracts import (
    Exchange,
    InstrumentSnapshot,
    MarketType,
    canonical_instrument_id,
)
from ai_platform.market_data.universe import (
    DEFAULT_POLICIES,
    MetricSnapshot,
    MissingMetricBehavior,
    SourceMode,
    UniverseSelectionPolicy,
    select_universe,
)

SOURCE_HASH = "d" * 64
SELECTION_MS = 1_800_000_000_000


def instrument(
    exchange: Exchange,
    market_type: MarketType,
    index: int,
    *,
    active: bool = True,
    canonical_symbol: str | None = None,
) -> InstrumentSnapshot:
    symbol = canonical_symbol or f"ASSET{index:03d}/USDT"
    if market_type is not MarketType.SPOT and not symbol.endswith(":USDT"):
        symbol = f"{symbol}:USDT"
    native_id = f"ASSET{index:03d}USDT-{exchange.value}-{market_type.value}"
    return InstrumentSnapshot(
        schema_version=1,
        exchange=exchange,
        market_type=market_type,
        native_instrument_id=native_id,
        canonical_instrument_id=canonical_instrument_id(exchange, market_type, native_id),
        native_symbol=native_id,
        canonical_symbol=symbol,
        base_asset=f"ASSET{index:03d}",
        quote_asset="USDT",
        settlement_asset=None if market_type is MarketType.SPOT else "USDT",
        contract_type=market_type,
        contract_value=None if market_type is MarketType.SPOT else Decimal("1"),
        contract_value_unit=None if market_type is MarketType.SPOT else "base_asset",
        tick_size=Decimal("0.01"),
        quantity_step=Decimal("0.001"),
        active=active,
        listed_at_ms=1_700_000_000_000,
        expires_at_ms=(
            1_900_000_000_000 if market_type is MarketType.DATED_FUTURE else None
        ),
        source_snapshot_id=f"{exchange.value}-{market_type.value}-snapshot",
        source_snapshot_sha256=SOURCE_HASH,
    )


def metric(item: InstrumentSnapshot, *, missing: bool = False) -> MetricSnapshot:
    suffix = int(item.base_asset.removeprefix("ASSET"))
    return MetricSnapshot(
        canonical_instrument_id=item.canonical_instrument_id,
        measured_at_ms=SELECTION_MS - 1,
        quote_volume_24h=None if missing else Decimal(1_000_000 - suffix),
        trade_count_24h=None if missing else 100_000 - suffix,
        open_interest_usd=(
            None
            if item.market_type is MarketType.SPOT or missing
            else Decimal(500_000 - suffix)
        ),
        spread_bps=None if missing else Decimal("1.0"),
        source_snapshot_ids=("synthetic-metrics-v1",),
    )


def test_all_active_selection_is_deterministic_and_excludes_inactive() -> None:
    items = (
        instrument(Exchange.BINANCE, MarketType.SPOT, 2),
        instrument(Exchange.OKX, MarketType.PERPETUAL, 1),
        instrument(Exchange.BYBIT, MarketType.SPOT, 3, active=False),
    )
    first = select_universe(
        instruments=items,
        metrics=(),
        selection_timestamp_ms=SELECTION_MS,
        policy=DEFAULT_POLICIES["all-active-lite-v1"],
    )
    second = select_universe(
        instruments=tuple(reversed(items)),
        metrics=(),
        selection_timestamp_ms=SELECTION_MS,
        policy=DEFAULT_POLICIES["all-active-lite-v1"],
    )
    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.ordered_instruments == second.ordered_instruments
    assert len(first.ordered_instruments) == 2
    excluded = next(item for item in first.decisions if not item.included)
    assert excluded.exclusion_reasons == ("inactive_in_source_snapshot",)


def test_top100_has_separate_spot_and_derivative_limits() -> None:
    spots = tuple(
        instrument(Exchange.BINANCE, MarketType.SPOT, index) for index in range(55)
    )
    derivatives = tuple(
        instrument(Exchange.BYBIT, MarketType.PERPETUAL, index + 100)
        for index in range(55)
    )
    items = spots + derivatives
    snapshot = select_universe(
        instruments=items,
        metrics=tuple(metric(item) for item in items),
        selection_timestamp_ms=SELECTION_MS,
        policy=DEFAULT_POLICIES["top100-microstructure-v1"],
    )
    selected = {
        decision.canonical_instrument_id: decision.market_bucket
        for decision in snapshot.decisions
        if decision.included
    }
    assert len(snapshot.ordered_instruments) == 100
    assert list(selected.values()).count("spot") == 50
    assert list(selected.values()).count("derivatives") == 50
    assert (
        sum(
            "outside_spot_profile_limit" in item.exclusion_reasons
            for item in snapshot.decisions
        )
        == 5
    )
    assert (
        sum(
            "outside_derivatives_profile_limit" in item.exclusion_reasons
            for item in snapshot.decisions
        )
        == 5
    )


def test_top20_intersection_requires_each_exchange() -> None:
    items: list[InstrumentSnapshot] = []
    markets = ((MarketType.SPOT, 0), (MarketType.PERPETUAL, 100))
    for market_type, offset in markets:
        for index in range(5):
            symbol = f"PAIR{index:02d}/USDT"
            for exchange in Exchange:
                items.append(
                    instrument(
                        exchange,
                        market_type,
                        index + offset,
                        canonical_symbol=symbol,
                    )
                )
    missing = instrument(
        Exchange.BINANCE,
        MarketType.SPOT,
        999,
        canonical_symbol="MISSING/USDT",
    )
    items.append(missing)
    snapshot = select_universe(
        instruments=tuple(items),
        metrics=tuple(metric(item) for item in items),
        selection_timestamp_ms=SELECTION_MS,
        policy=DEFAULT_POLICIES["top20-high-frequency-v1"],
    )
    assert len(snapshot.ordered_instruments) == 20
    missing_decision = next(
        item
        for item in snapshot.decisions
        if item.canonical_instrument_id == missing.canonical_instrument_id
    )
    assert not missing_decision.included
    assert missing_decision.exclusion_reasons == (
        "missing_from_required_exchanges:bybit,okx",
    )


def test_stable_tie_breaking_and_rank_last_missing_metrics() -> None:
    alpha = instrument(
        Exchange.BINANCE,
        MarketType.SPOT,
        10,
        canonical_symbol="ALPHA/USDT",
    )
    beta = instrument(
        Exchange.BINANCE,
        MarketType.SPOT,
        11,
        canonical_symbol="BETA/USDT",
    )
    derivatives = tuple(
        instrument(Exchange.BINANCE, MarketType.PERPETUAL, index + 100)
        for index in range(10)
    )
    policy = UniverseSelectionPolicy(
        profile_identity="top20-high-frequency-v1",
        policy_version="synthetic-policy-v1",
        spot_limit=10,
        derivatives_limit=10,
        source_mode=SourceMode.UNION,
        required_exchanges=(Exchange.BINANCE,),
        missing_metric_behavior=MissingMetricBehavior.RANK_LAST,
    )
    complete_beta = replace(
        metric(beta),
        quote_volume_24h=Decimal("100"),
        trade_count_24h=100,
    )
    complete_alpha = replace(
        metric(alpha),
        quote_volume_24h=Decimal("100"),
        trade_count_24h=100,
    )
    snapshot = select_universe(
        instruments=(beta, alpha, *derivatives),
        metrics=(complete_beta, complete_alpha, *(metric(item) for item in derivatives)),
        selection_timestamp_ms=SELECTION_MS,
        policy=policy,
    )
    assert snapshot.ordered_instruments[:2] == (
        alpha.canonical_instrument_id,
        beta.canonical_instrument_id,
    )

    rank_last = select_universe(
        instruments=(alpha, beta, *derivatives),
        metrics=(
            metric(alpha),
            metric(beta, missing=True),
            *(metric(item) for item in derivatives),
        ),
        selection_timestamp_ms=SELECTION_MS,
        policy=policy,
    )
    assert rank_last.ordered_instruments.index(
        beta.canonical_instrument_id
    ) > rank_last.ordered_instruments.index(alpha.canonical_instrument_id)


def test_missing_metrics_duplicates_and_changed_input_hash() -> None:
    complete = instrument(Exchange.BINANCE, MarketType.SPOT, 1)
    missing = instrument(Exchange.BINANCE, MarketType.SPOT, 2)
    policy = UniverseSelectionPolicy(
        profile_identity="top20-high-frequency-v1",
        policy_version="synthetic-policy-v1",
        spot_limit=10,
        derivatives_limit=10,
        source_mode=SourceMode.UNION,
        required_exchanges=(Exchange.BINANCE,),
        missing_metric_behavior=MissingMetricBehavior.EXCLUDE,
    )
    snapshot = select_universe(
        instruments=(complete, missing),
        metrics=(metric(complete), metric(missing, missing=True)),
        selection_timestamp_ms=SELECTION_MS,
        policy=policy,
    )
    missing_decision = next(
        item
        for item in snapshot.decisions
        if item.canonical_instrument_id == missing.canonical_instrument_id
    )
    assert not missing_decision.included
    assert missing_decision.exclusion_reasons[0].startswith("missing_metrics:")

    with pytest.raises(ValueError, match="duplicate instrument"):
        select_universe(
            instruments=(complete, complete),
            metrics=(metric(complete),),
            selection_timestamp_ms=SELECTION_MS,
            policy=policy,
        )
    with pytest.raises(ValueError, match="duplicate metric"):
        select_universe(
            instruments=(complete,),
            metrics=(metric(complete), metric(complete)),
            selection_timestamp_ms=SELECTION_MS,
            policy=policy,
        )

    baseline = select_universe(
        instruments=(complete,),
        metrics=(),
        selection_timestamp_ms=SELECTION_MS,
        policy=DEFAULT_POLICIES["all-active-lite-v1"],
    )
    changed = select_universe(
        instruments=(replace(complete, tick_size=Decimal("0.02")),),
        metrics=(),
        selection_timestamp_ms=SELECTION_MS,
        policy=DEFAULT_POLICIES["all-active-lite-v1"],
    )
    assert (
        baseline.source_instrument_snapshot_sha256
        != changed.source_instrument_snapshot_sha256
    )
    assert baseline.snapshot_sha256 != changed.snapshot_sha256
