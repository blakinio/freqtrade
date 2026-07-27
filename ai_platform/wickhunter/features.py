from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, localcontext

from ai_platform.research.liquidations.contracts import (
    LiquidatedPositionSide,
    LiquidationEvent,
)
from ai_platform.wickhunter.contracts import (
    LiquidationFeatureVector,
    LiquidationHistorySnapshot,
    LiquidationSourceState,
    MarketContextSnapshot,
    SourceHealth,
    SourceLiquidationAggregate,
)


FEATURE_SCHEMA_VERSION = "wickhunter-liquidation-features-v1"
REQUIRED_MARKET_METRICS = (
    "quote_volume_24h_usd",
    "vwap",
    "vwma",
    "atr_ratio",
    "volatility_ratio",
    "wick_ratio",
    "trend_return_ratio",
    "spread_bps",
    "market_wide_liquidation_intensity",
)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, Decimal(0)) / Decimal(len(values))


def _zscore(value: Decimal, history: tuple[Decimal, ...]) -> Decimal:
    mean = _mean(history)
    variance = sum(((item - mean) ** 2 for item in history), Decimal(0)) / Decimal(len(history))
    if variance == 0:
        return Decimal(0)
    with localcontext() as context:
        context.prec = 28
        return (value - mean) / variance.sqrt()


def _percentile(value: Decimal, history: tuple[Decimal, ...]) -> Decimal:
    less_or_equal = sum(1 for item in history if item <= value)
    return Decimal(less_or_equal) / Decimal(len(history))


def _validate_market_snapshot(snapshot: MarketContextSnapshot) -> None:
    names = {metric.name for metric in snapshot.metrics}
    missing = sorted(set(REQUIRED_MARKET_METRICS) - names)
    if missing:
        raise ValueError(f"missing required market metrics: {missing}")
    for metric in snapshot.metrics:
        if metric.available_at_ms > snapshot.decision_timestamp_ms:
            raise ValueError(f"market metric is not available at decision time: {metric.name}")
        if metric.source.startswith("completed_candle"):
            if metric.available_at_ms < snapshot.completed_candle_close_ms:
                raise ValueError(f"completed-candle metric available before close: {metric.name}")


def _validate_source_states(
    source_states: tuple[LiquidationSourceState, ...],
    decision_timestamp_ms: int,
) -> dict[str, LiquidationSourceState]:
    if not source_states:
        raise ValueError("at least one liquidation source state is required")
    sources = [state.source for state in source_states]
    if sources != sorted(sources) or len(sources) != len(set(sources)):
        raise ValueError("source states must be unique and sorted")
    for state in source_states:
        if state.observed_at_ms > decision_timestamp_ms:
            raise ValueError(f"source state is from the future: {state.source}")
        if (
            state.last_received_at_ms is not None
            and state.last_received_at_ms > decision_timestamp_ms
        ):
            raise ValueError(f"source last-received timestamp is from the future: {state.source}")
    return {state.source: state for state in source_states}


def build_liquidation_features(  # noqa: C901
    *,
    events: tuple[LiquidationEvent, ...],
    market: MarketContextSnapshot,
    history: LiquidationHistorySnapshot,
    source_states: tuple[LiquidationSourceState, ...],
    burst_window_ms: int,
) -> LiquidationFeatureVector:
    if burst_window_ms <= 0:
        raise ValueError("burst_window_ms must be > 0")
    _validate_market_snapshot(market)
    state_by_source = _validate_source_states(source_states, market.decision_timestamp_ms)
    if history.symbol.upper() != market.symbol.upper():
        raise ValueError("history symbol does not match market symbol")
    if history.available_at_ms > market.decision_timestamp_ms:
        raise ValueError("liquidation history is not available at decision time")

    window_start = market.decision_timestamp_ms - burst_window_ms
    selected: list[LiquidationEvent] = []
    identities: set[tuple[str, str]] = set()
    for event in events:
        if event.symbol.upper() != market.symbol.upper():
            raise ValueError("liquidation event symbol does not match market symbol")
        if event.received_at_ms > market.decision_timestamp_ms:
            raise ValueError("liquidation event was received after decision time")
        identity = (event.source, event.source_event_id)
        if identity in identities:
            raise ValueError("duplicate source-labelled liquidation event")
        identities.add(identity)
        if event.received_at_ms >= window_start:
            selected.append(event)
    if not selected:
        raise ValueError("no liquidation events are available in the burst window")

    by_source: dict[str, list[LiquidationEvent]] = defaultdict(list)
    for event in selected:
        by_source[event.source].append(event)
        if event.source not in state_by_source:
            raise ValueError(f"missing source health state for event source: {event.source}")

    total = sum((event.notional_usd for event in selected), Decimal(0))
    long_total = sum(
        (
            event.notional_usd
            for event in selected
            if event.liquidated_position_side is LiquidatedPositionSide.LONG
        ),
        Decimal(0),
    )
    short_total = total - long_total
    imbalance = (short_total - long_total) / total
    maximum_event = max(event.notional_usd for event in selected)
    maximum_latency = max(event.ingest_latency_ms for event in selected)

    aggregates: list[SourceLiquidationAggregate] = []
    for source in sorted(by_source):
        source_events = by_source[source]
        source_total = sum((event.notional_usd for event in source_events), Decimal(0))
        source_long = sum(
            (
                event.notional_usd
                for event in source_events
                if event.liquidated_position_side is LiquidatedPositionSide.LONG
            ),
            Decimal(0),
        )
        aggregates.append(
            SourceLiquidationAggregate(
                source=source,
                event_count=len(source_events),
                total_notional_usd=source_total,
                liquidated_long_notional_usd=source_long,
                liquidated_short_notional_usd=source_total - source_long,
                maximum_event_notional_usd=max(event.notional_usd for event in source_events),
                maximum_ingest_latency_ms=max(event.ingest_latency_ms for event in source_events),
                latest_received_at_ms=max(event.received_at_ms for event in source_events),
            )
        )

    healthy_sources = sum(
        1
        for state in source_states
        if state.coverage_available and state.health is SourceHealth.HEALTHY
    )
    source_coverage_ratio = Decimal(healthy_sources) / Decimal(len(source_states))
    historical_burst_mean = _mean(history.burst_window_notionals_usd)
    burst_intensity = total / historical_burst_mean
    time_since_previous = (
        None
        if history.previous_burst_received_at_ms is None
        else market.decision_timestamp_ms - history.previous_burst_received_at_ms
    )
    if time_since_previous is not None and time_since_previous < 0:
        raise ValueError("previous burst timestamp cannot be after decision")

    feature_available_at_ms = max(
        max(event.received_at_ms for event in selected),
        history.available_at_ms,
        max(metric.available_at_ms for metric in market.metrics),
        max(state.observed_at_ms for state in source_states),
    )
    return LiquidationFeatureVector(
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        symbol=market.symbol.upper(),
        decision_timestamp_ms=market.decision_timestamp_ms,
        decision_price=market.decision_price,
        event_count=len(selected),
        total_notional_usd=total,
        liquidated_long_notional_usd=long_total,
        liquidated_short_notional_usd=short_total,
        long_short_imbalance=imbalance,
        maximum_event_notional_usd=maximum_event,
        maximum_event_percentile=_percentile(maximum_event, history.event_notionals_usd),
        maximum_event_zscore=_zscore(maximum_event, history.event_notionals_usd),
        liquidation_burst_intensity=burst_intensity,
        time_since_previous_burst_ms=time_since_previous,
        ingest_latency_ms=maximum_latency,
        source_coverage_ratio=source_coverage_ratio,
        source_aggregates=tuple(aggregates),
        market_metrics=tuple(sorted(market.metrics, key=lambda metric: metric.name)),
        feature_available_at_ms=feature_available_at_ms,
        input_event_ids=tuple(
            sorted(f"{event.source}:{event.source_event_id}" for event in selected)
        ),
        history_id=history.history_id,
        history_sha256=history.history_sha256,
    )
