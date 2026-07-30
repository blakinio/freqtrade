from dataclasses import dataclass
from decimal import Decimal

import pytest

from strategy_engine.research.liquidation_alignment import (
    AlignedObservation,
    AlignmentStatus,
    LiquidationAlignment,
    MarketObservation,
    ObservationConflictError,
    ObservationKind,
    align_liquidation_context,
    deduplicate_observations,
)


@dataclass(frozen=True, slots=True)
class LiquidationFixture:
    schema_version: int
    source: str
    source_event_id: str
    symbol: str
    occurred_at_ms: int
    received_at_ms: int


def liquidation() -> LiquidationFixture:
    return LiquidationFixture(
        schema_version=1,
        source="bybit-linear",
        source_event_id="liq-1",
        symbol="BTCUSDT",
        occurred_at_ms=10_000,
        received_at_ms=10_050,
    )


def observation(
    source: str,
    kind: ObservationKind,
    event: int,
    available: int,
    value: str,
    *,
    event_id: str | None = None,
) -> MarketObservation:
    return MarketObservation(
        schema_version=1,
        data_version="v1",
        source=source,
        source_event_id=event_id or f"{source}-{kind.value}-{event}",
        symbol="BTCUSDT",
        kind=kind,
        event_time_ms=event,
        received_at_ms=event + 10,
        available_at_ms=available,
        value=Decimal(value),
    )


def by(
    result: LiquidationAlignment,
    source: str,
    kind: ObservationKind,
) -> AlignedObservation:
    return next(item for item in result.observations if item.source == source and item.kind is kind)


def test_alignment_uses_latest_visible_observation_without_lookahead() -> None:
    result = align_liquidation_context(
        liquidation(),
        [
            observation(
                "bybit-linear",
                ObservationKind.OPEN_INTEREST,
                9_000,
                9_020,
                "10",
            ),
            observation(
                "bybit-linear",
                ObservationKind.OPEN_INTEREST,
                9_900,
                10_040,
                "11",
            ),
            observation(
                "bybit-linear",
                ObservationKind.OPEN_INTEREST,
                10_001,
                10_020,
                "99",
            ),
            observation(
                "bybit-linear",
                ObservationKind.FUNDING_RATE,
                9_800,
                9_830,
                "-0.0001",
            ),
        ],
        expected_sources=["bybit-linear"],
        max_age_ms=1_000,
    )

    oi = by(result, "bybit-linear", ObservationKind.OPEN_INTEREST)
    funding = by(result, "bybit-linear", ObservationKind.FUNDING_RATE)

    assert result.liquidation_schema_version == 1
    assert result.liquidation_source == "bybit-linear"
    assert result.liquidation_source_event_id == "liq-1"
    assert result.event_time_ms == 10_000
    assert result.received_at_ms == 10_050
    assert oi.status is AlignmentStatus.ALIGNED
    assert oi.value == Decimal(11)
    assert oi.source_event_id == "bybit-linear-open_interest-9900"
    assert oi.schema_version == 1
    assert oi.data_version == "v1"
    assert oi.event_time_ms == 9_900
    assert oi.received_at_ms == 9_910
    assert oi.available_at_ms == 10_040
    assert oi.age_ms == 100
    assert funding.value == Decimal("-0.0001")


def test_missing_delayed_and_stale_are_distinct() -> None:
    result = align_liquidation_context(
        liquidation(),
        [
            observation(
                "bybit-linear",
                ObservationKind.OPEN_INTEREST,
                9_900,
                10_100,
                "11",
            ),
            observation(
                "okx-swap",
                ObservationKind.OPEN_INTEREST,
                8_000,
                8_020,
                "8",
            ),
        ],
        expected_sources=["bybit-linear", "binance-usdm", "okx-swap"],
        max_age_ms=500,
    )

    delayed = by(result, "bybit-linear", ObservationKind.OPEN_INTEREST)
    missing = by(result, "binance-usdm", ObservationKind.OPEN_INTEREST)
    stale = by(result, "okx-swap", ObservationKind.OPEN_INTEREST)

    assert delayed.status is AlignmentStatus.DELAYED
    assert delayed.delay_ms == 50
    assert delayed.schema_version == 1
    assert delayed.data_version == "v1"
    assert missing.status is AlignmentStatus.MISSING
    assert missing.schema_version is None
    assert missing.data_version is None
    assert stale.status is AlignmentStatus.STALE
    assert stale.age_ms == 2_000


def test_deduplication_is_deterministic_and_conflicts_fail_closed() -> None:
    item = observation(
        "bybit-linear",
        ObservationKind.OPEN_INTEREST,
        9_000,
        9_020,
        "10",
        event_id="same",
    )
    assert deduplicate_observations([item, item]) == (item,)

    conflict = observation(
        "bybit-linear",
        ObservationKind.OPEN_INTEREST,
        9_000,
        9_020,
        "11",
        event_id="same",
    )
    with pytest.raises(ObservationConflictError, match="conflicting payloads"):
        deduplicate_observations([item, conflict])


def test_result_order_and_identity_are_input_order_independent() -> None:
    first = align_liquidation_context(
        liquidation(),
        [],
        expected_sources=["okx-swap", "bybit-linear"],
        max_age_ms=1_000,
    )
    second = align_liquidation_context(
        liquidation(),
        [],
        expected_sources=["bybit-linear", "okx-swap"],
        max_age_ms=1_000,
    )

    assert first == second
    assert [(item.source, item.kind.value) for item in first.observations] == [
        ("bybit-linear", "open_interest"),
        ("bybit-linear", "funding_rate"),
        ("okx-swap", "open_interest"),
        ("okx-swap", "funding_rate"),
    ]


def test_invalid_observation_timestamps_and_values_fail_closed() -> None:
    with pytest.raises(ValueError, match="available_at_ms"):
        MarketObservation(
            1,
            "v1",
            "x",
            "id",
            "BTCUSDT",
            ObservationKind.OPEN_INTEREST,
            100,
            110,
            109,
            Decimal(1),
        )
    with pytest.raises(ValueError, match="open_interest"):
        observation("x", ObservationKind.OPEN_INTEREST, 100, 120, "-1")
    with pytest.raises(ValueError, match="as_of_ms"):
        align_liquidation_context(
            liquidation(),
            [],
            expected_sources=["x"],
            as_of_ms=9_999,
            max_age_ms=1,
        )


def test_invalid_liquidation_contract_fails_closed() -> None:
    invalid = LiquidationFixture(
        schema_version=2,
        source="bybit-linear",
        source_event_id="liq-1",
        symbol="BTCUSDT",
        occurred_at_ms=10_000,
        received_at_ms=10_050,
    )
    with pytest.raises(ValueError, match="liquidation schema_version"):
        align_liquidation_context(
            invalid,
            [],
            expected_sources=["bybit-linear"],
            max_age_ms=1_000,
        )
