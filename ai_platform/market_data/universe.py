from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from ai_platform.market_data.contracts import (
    Exchange,
    FrozenJsonObject,
    InstrumentSnapshot,
    MarketType,
    UniverseDecision,
    UniverseSnapshot,
    canonical_sha256,
    decimal_text,
    decimal_value,
)


class SourceMode(StrEnum):
    INTERSECTION = "intersection"
    UNION = "union"


class MissingMetricBehavior(StrEnum):
    EXCLUDE = "exclude"
    RANK_LAST = "rank_last"


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    canonical_instrument_id: str
    measured_at_ms: int
    quote_volume_24h: Decimal | None
    trade_count_24h: int | None
    open_interest_usd: Decimal | None
    spread_bps: Decimal | None
    source_snapshot_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.canonical_instrument_id.strip():
            raise ValueError("canonical_instrument_id must be non-empty")
        if self.measured_at_ms <= 0:
            raise ValueError("measured_at_ms must be > 0")
        for field_name in ("quote_volume_24h", "open_interest_usd", "spread_bps"):
            value = getattr(self, field_name)
            if value is not None:
                parsed = decimal_value(value, field=field_name)
                if parsed < 0:
                    raise ValueError(f"{field_name} must be >= 0")
        if self.trade_count_24h is not None:
            if isinstance(self.trade_count_24h, bool) or self.trade_count_24h < 0:
                raise ValueError("trade_count_24h must be a non-negative integer")
        if not self.source_snapshot_ids:
            raise ValueError("source_snapshot_ids must be non-empty")
        if len(set(self.source_snapshot_ids)) != len(self.source_snapshot_ids):
            raise ValueError("source_snapshot_ids must not contain duplicates")

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "measured_at_ms": self.measured_at_ms,
            "quote_volume_24h": (
                None
                if self.quote_volume_24h is None
                else decimal_text(self.quote_volume_24h)
            ),
            "trade_count_24h": self.trade_count_24h,
            "open_interest_usd": (
                None
                if self.open_interest_usd is None
                else decimal_text(self.open_interest_usd)
            ),
            "spread_bps": (
                None if self.spread_bps is None else decimal_text(self.spread_bps)
            ),
            "source_snapshot_ids": list(self.source_snapshot_ids),
        }


@dataclass(frozen=True, slots=True)
class UniverseSelectionPolicy:
    profile_identity: str
    policy_version: str
    spot_limit: int | None
    derivatives_limit: int | None
    source_mode: SourceMode
    required_exchanges: tuple[Exchange, ...]
    missing_metric_behavior: MissingMetricBehavior

    def __post_init__(self) -> None:
        if self.profile_identity not in {
            "all-active-lite-v1",
            "top100-microstructure-v1",
            "top20-high-frequency-v1",
        }:
            raise ValueError("unsupported profile_identity")
        if not self.policy_version.strip():
            raise ValueError("policy_version must be non-empty")
        if not self.required_exchanges:
            raise ValueError("required_exchanges must be non-empty")
        if len(set(self.required_exchanges)) != len(self.required_exchanges):
            raise ValueError("required_exchanges must be unique")
        if self.profile_identity == "all-active-lite-v1":
            if self.spot_limit is not None or self.derivatives_limit is not None:
                raise ValueError("all-active-lite-v1 must not define limits")
        else:
            if self.spot_limit is None or self.derivatives_limit is None:
                raise ValueError("ranked profiles require spot and derivatives limits")
            if self.spot_limit < 0 or self.derivatives_limit < 0:
                raise ValueError("profile limits must be >= 0")
            expected_total = (
                100 if self.profile_identity == "top100-microstructure-v1" else 20
            )
            if self.spot_limit + self.derivatives_limit != expected_total:
                raise ValueError(f"profile limits must sum to {expected_total}")


DEFAULT_POLICIES: dict[str, UniverseSelectionPolicy] = {
    "all-active-lite-v1": UniverseSelectionPolicy(
        profile_identity="all-active-lite-v1",
        policy_version="market-data-universe-policy-v1",
        spot_limit=None,
        derivatives_limit=None,
        source_mode=SourceMode.UNION,
        required_exchanges=(Exchange.BINANCE, Exchange.BYBIT, Exchange.OKX),
        missing_metric_behavior=MissingMetricBehavior.EXCLUDE,
    ),
    "top100-microstructure-v1": UniverseSelectionPolicy(
        profile_identity="top100-microstructure-v1",
        policy_version="market-data-universe-policy-v1",
        spot_limit=50,
        derivatives_limit=50,
        source_mode=SourceMode.UNION,
        required_exchanges=(Exchange.BINANCE, Exchange.BYBIT, Exchange.OKX),
        missing_metric_behavior=MissingMetricBehavior.EXCLUDE,
    ),
    "top20-high-frequency-v1": UniverseSelectionPolicy(
        profile_identity="top20-high-frequency-v1",
        policy_version="market-data-universe-policy-v1",
        spot_limit=10,
        derivatives_limit=10,
        source_mode=SourceMode.INTERSECTION,
        required_exchanges=(Exchange.BINANCE, Exchange.BYBIT, Exchange.OKX),
        missing_metric_behavior=MissingMetricBehavior.EXCLUDE,
    ),
}


def _stable_tie_breaker(instrument: InstrumentSnapshot) -> str:
    return "|".join(
        (
            instrument.canonical_symbol.upper(),
            instrument.market_type.value,
            instrument.exchange.value,
            instrument.canonical_instrument_id,
        )
    )


def _market_key(instrument: InstrumentSnapshot) -> tuple[MarketType, str]:
    return instrument.market_type, instrument.canonical_symbol.upper()


def _required_metric_names(market_type: MarketType) -> tuple[str, ...]:
    if market_type is MarketType.SPOT:
        return ("quote_volume_24h", "trade_count_24h", "spread_bps")
    return (
        "quote_volume_24h",
        "open_interest_usd",
        "trade_count_24h",
        "spread_bps",
    )


def _missing_metric_names(
    instrument: InstrumentSnapshot,
    metric: MetricSnapshot | None,
) -> tuple[str, ...]:
    if metric is None:
        return _required_metric_names(instrument.market_type)
    return tuple(
        field_name
        for field_name in _required_metric_names(instrument.market_type)
        if getattr(metric, field_name) is None
    )


def _ranking_components(
    instrument: InstrumentSnapshot,
    metric: MetricSnapshot | None,
) -> FrozenJsonObject:
    missing = _missing_metric_names(instrument, metric)
    return FrozenJsonObject.from_mapping(
        {
            "policy_family": (
                "spot" if instrument.market_type is MarketType.SPOT else "derivatives"
            ),
            "quote_volume_24h": (
                None
                if metric is None or metric.quote_volume_24h is None
                else decimal_text(metric.quote_volume_24h)
            ),
            "open_interest_usd": (
                None
                if metric is None or metric.open_interest_usd is None
                else decimal_text(metric.open_interest_usd)
            ),
            "trade_count_24h": None if metric is None else metric.trade_count_24h,
            "spread_bps": (
                None
                if metric is None or metric.spread_bps is None
                else decimal_text(metric.spread_bps)
            ),
            "missing_metrics": list(missing),
        }
    )


def _ranking_key(
    instrument: InstrumentSnapshot,
    metric: MetricSnapshot | None,
) -> tuple[object, ...]:
    missing = _missing_metric_names(instrument, metric)
    quote_volume = (
        Decimal("-1")
        if metric is None or metric.quote_volume_24h is None
        else metric.quote_volume_24h
    )
    trade_count = (
        -1
        if metric is None or metric.trade_count_24h is None
        else metric.trade_count_24h
    )
    spread = (
        Decimal("Infinity")
        if metric is None or metric.spread_bps is None
        else metric.spread_bps
    )
    tie_breaker = _stable_tie_breaker(instrument)
    if instrument.market_type is MarketType.SPOT:
        return (len(missing), -quote_volume, -trade_count, spread, tie_breaker)
    open_interest = (
        Decimal("-1")
        if metric is None or metric.open_interest_usd is None
        else metric.open_interest_usd
    )
    return (
        len(missing),
        -quote_volume,
        -open_interest,
        -trade_count,
        spread,
        tie_breaker,
    )


def _instrument_snapshot_hash(instruments: tuple[InstrumentSnapshot, ...]) -> str:
    ordered = sorted(
        (instrument.as_json_dict() for instrument in instruments),
        key=lambda item: str(item["canonical_instrument_id"]),
    )
    return canonical_sha256(ordered)


def select_universe(  # noqa: C901
    *,
    instruments: tuple[InstrumentSnapshot, ...],
    metrics: tuple[MetricSnapshot, ...],
    selection_timestamp_ms: int,
    policy: UniverseSelectionPolicy,
) -> UniverseSnapshot:
    if selection_timestamp_ms <= 0:
        raise ValueError("selection_timestamp_ms must be > 0")
    instrument_ids = [instrument.canonical_instrument_id for instrument in instruments]
    if len(set(instrument_ids)) != len(instrument_ids):
        raise ValueError("duplicate instrument snapshots are not allowed")
    metric_ids = [metric.canonical_instrument_id for metric in metrics]
    if len(set(metric_ids)) != len(metric_ids):
        raise ValueError("duplicate metric snapshots are not allowed")
    unknown_metrics = sorted(set(metric_ids) - set(instrument_ids))
    if unknown_metrics:
        raise ValueError(f"metrics reference unknown instruments: {unknown_metrics}")
    metric_by_id = {metric.canonical_instrument_id: metric for metric in metrics}
    for metric in metrics:
        if metric.measured_at_ms > selection_timestamp_ms:
            raise ValueError("metric snapshots must not be from the future")

    exchange_set = set(policy.required_exchanges)
    active_by_key: dict[tuple[MarketType, str], set[Exchange]] = {}
    for instrument in instruments:
        if instrument.active and instrument.exchange in exchange_set:
            active_by_key.setdefault(_market_key(instrument), set()).add(
                instrument.exchange
            )

    prequalified_spot: list[InstrumentSnapshot] = []
    prequalified_derivatives: list[InstrumentSnapshot] = []
    exclusion_reasons: dict[str, list[str]] = {}
    inclusion_notes: dict[str, list[str]] = {}

    for instrument in instruments:
        reasons: list[str] = []
        if not instrument.active:
            reasons.append("inactive_in_source_snapshot")
        if instrument.exchange not in exchange_set:
            reasons.append("exchange_not_selected")
        if policy.source_mode is SourceMode.INTERSECTION:
            observed = active_by_key.get(_market_key(instrument), set())
            missing_exchanges = sorted(item.value for item in exchange_set - observed)
            if missing_exchanges:
                reasons.append(
                    "missing_from_required_exchanges:" + ",".join(missing_exchanges)
                )

        metric = metric_by_id.get(instrument.canonical_instrument_id)
        missing_metrics = _missing_metric_names(instrument, metric)
        if policy.profile_identity != "all-active-lite-v1" and missing_metrics:
            if policy.missing_metric_behavior is MissingMetricBehavior.EXCLUDE:
                reasons.append("missing_metrics:" + ",".join(missing_metrics))
            else:
                inclusion_notes[instrument.canonical_instrument_id] = [
                    "missing_metrics_ranked_last:" + ",".join(missing_metrics)
                ]

        if reasons:
            exclusion_reasons[instrument.canonical_instrument_id] = reasons
            continue
        if instrument.market_type is MarketType.SPOT:
            prequalified_spot.append(instrument)
        else:
            prequalified_derivatives.append(instrument)

    prequalified_spot.sort(
        key=lambda instrument: (
            _stable_tie_breaker(instrument)
            if policy.profile_identity == "all-active-lite-v1"
            else _ranking_key(
                instrument,
                metric_by_id.get(instrument.canonical_instrument_id),
            )
        )
    )
    prequalified_derivatives.sort(
        key=lambda instrument: (
            _stable_tie_breaker(instrument)
            if policy.profile_identity == "all-active-lite-v1"
            else _ranking_key(
                instrument,
                metric_by_id.get(instrument.canonical_instrument_id),
            )
        )
    )

    if policy.profile_identity == "all-active-lite-v1":
        included_spot = prequalified_spot
        included_derivatives = prequalified_derivatives
    else:
        spot_limit = policy.spot_limit
        derivatives_limit = policy.derivatives_limit
        if spot_limit is None or derivatives_limit is None:
            raise RuntimeError("validated ranked policy lost its limits")
        included_spot = prequalified_spot[:spot_limit]
        included_derivatives = prequalified_derivatives[:derivatives_limit]
        for instrument in prequalified_spot[spot_limit:]:
            exclusion_reasons[instrument.canonical_instrument_id] = [
                "outside_spot_profile_limit"
            ]
        for instrument in prequalified_derivatives[derivatives_limit:]:
            exclusion_reasons[instrument.canonical_instrument_id] = [
                "outside_derivatives_profile_limit"
            ]

    included_order = included_spot + included_derivatives
    rank_by_id = {
        instrument.canonical_instrument_id: rank
        for rank, instrument in enumerate(included_order, start=1)
    }
    instrument_by_id = {
        instrument.canonical_instrument_id: instrument for instrument in instruments
    }
    decisions: list[UniverseDecision] = []
    for instrument_id in sorted(instrument_by_id):
        instrument = instrument_by_id[instrument_id]
        included = instrument_id in rank_by_id
        reasons = inclusion_notes.get(instrument_id, [])
        if included:
            reasons.append("active_and_policy_eligible")
            if policy.source_mode is SourceMode.INTERSECTION:
                reasons.append("present_on_all_required_exchanges")
            else:
                reasons.append("source_union_member")
            if policy.profile_identity != "all-active-lite-v1":
                reasons.append("selected_by_deterministic_rank")
        decisions.append(
            UniverseDecision(
                canonical_instrument_id=instrument_id,
                included=included,
                rank=rank_by_id.get(instrument_id),
                market_bucket=(
                    "spot" if instrument.market_type is MarketType.SPOT else "derivatives"
                ),
                ranking_components=_ranking_components(
                    instrument,
                    metric_by_id.get(instrument_id),
                ),
                inclusion_reasons=tuple(reasons),
                exclusion_reasons=tuple(exclusion_reasons.get(instrument_id, [])),
                stable_tie_breaker=_stable_tie_breaker(instrument),
            )
        )

    return UniverseSnapshot.create(
        profile_identity=policy.profile_identity,
        selection_timestamp_ms=selection_timestamp_ms,
        source_instrument_snapshot_sha256=_instrument_snapshot_hash(instruments),
        selection_policy_version=policy.policy_version,
        source_mode=policy.source_mode.value,
        required_exchanges=policy.required_exchanges,
        ordered_instruments=tuple(
            instrument.canonical_instrument_id for instrument in included_order
        ),
        decisions=tuple(decisions),
    )
