from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ai_platform.market_data.contracts import InstrumentSnapshot, MarketType
from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import SourceHealth


@dataclass(frozen=True, slots=True)
class LiquidationCoverage:
    source: str
    health: SourceHealth
    last_received_at_ms: int | None

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise ValueError("liquidation source must be non-empty")
        if self.last_received_at_ms is not None and self.last_received_at_ms <= 0:
            raise ValueError("last_received_at_ms must be > 0 when supplied")


@dataclass(frozen=True, slots=True)
class UniverseQualitySnapshot:
    canonical_instrument_id: str
    measured_at_ms: int
    quote_volume_24h_usd: Decimal
    spread_bps: Decimal | None
    candle_history_rows: int
    feature_history_rows: int
    latest_candle_available_at_ms: int
    liquidation_coverage: tuple[LiquidationCoverage, ...]
    symbol_risk_blocked: bool = False

    def __post_init__(self) -> None:
        if not self.canonical_instrument_id.strip():
            raise ValueError("canonical_instrument_id must be non-empty")
        if self.measured_at_ms <= 0 or self.latest_candle_available_at_ms <= 0:
            raise ValueError("quality timestamps must be > 0")
        if not self.quote_volume_24h_usd.is_finite() or self.quote_volume_24h_usd < 0:
            raise ValueError("quote_volume_24h_usd must be finite and >= 0")
        if self.spread_bps is not None:
            if not self.spread_bps.is_finite() or self.spread_bps < 0:
                raise ValueError("spread_bps must be finite and >= 0")
        if self.candle_history_rows < 0 or self.feature_history_rows < 0:
            raise ValueError("history row counts must be >= 0")
        sources = [coverage.source for coverage in self.liquidation_coverage]
        if sources != sorted(sources) or len(sources) != len(set(sources)):
            raise ValueError("liquidation coverage must be unique and sorted")


@dataclass(frozen=True, slots=True)
class DynamicUniversePolicy:
    policy_version: str
    required_market_type: MarketType
    required_quote_asset: str
    minimum_quote_volume_24h_usd: Decimal
    maximum_spread_bps: Decimal | None
    minimum_candle_history_rows: int
    minimum_feature_history_rows: int
    minimum_healthy_liquidation_sources: int
    maximum_quality_age_ms: int
    maximum_candle_age_ms: int
    maximum_liquidation_age_ms: int

    def __post_init__(self) -> None:
        if not self.policy_version.strip() or not self.required_quote_asset.strip():
            raise ValueError("universe policy identities must be non-empty")
        if self.minimum_quote_volume_24h_usd < 0:
            raise ValueError("minimum quote volume must be >= 0")
        if self.maximum_spread_bps is not None and self.maximum_spread_bps < 0:
            raise ValueError("maximum spread must be >= 0")
        for field_name in (
            "minimum_candle_history_rows",
            "minimum_feature_history_rows",
            "minimum_healthy_liquidation_sources",
            "maximum_quality_age_ms",
            "maximum_candle_age_ms",
            "maximum_liquidation_age_ms",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be >= 0")


@dataclass(frozen=True, slots=True)
class UniverseInstrumentDecision:
    canonical_instrument_id: str
    canonical_symbol: str
    included: bool
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.canonical_instrument_id.strip() or not self.canonical_symbol.strip():
            raise ValueError("universe decision identities must be non-empty")
        if not self.reason_codes:
            raise ValueError("universe decision requires reason_codes")
        if self.reason_codes != tuple(sorted(set(self.reason_codes))):
            raise ValueError("universe reason_codes must be unique and sorted")


@dataclass(frozen=True, slots=True)
class DynamicUniverseSnapshot:
    schema_version: str
    policy_version: str
    selected_at_ms: int
    decisions: tuple[UniverseInstrumentDecision, ...]

    def __post_init__(self) -> None:
        if not self.schema_version.strip() or not self.policy_version.strip():
            raise ValueError("universe snapshot identities must be non-empty")
        if self.selected_at_ms <= 0:
            raise ValueError("selected_at_ms must be > 0")
        ids = [decision.canonical_instrument_id for decision in self.decisions]
        if ids != sorted(ids) or len(ids) != len(set(ids)):
            raise ValueError("universe decisions must be unique and sorted")

    @property
    def selected_symbols(self) -> tuple[str, ...]:
        return tuple(
            sorted({decision.canonical_symbol for decision in self.decisions if decision.included})
        )

    @property
    def snapshot_hash(self) -> str:
        return canonical_sha256(self)

    def includes_symbol(self, symbol: str) -> bool:
        normalized = symbol.upper()
        return any(item.upper() == normalized for item in self.selected_symbols)


def _quality_reasons(  # noqa: C901
    *,
    instrument: InstrumentSnapshot,
    quality: UniverseQualitySnapshot,
    policy: DynamicUniversePolicy,
    decision_timestamp_ms: int,
) -> list[str]:
    reasons: list[str] = []
    if not instrument.active:
        reasons.append("instrument_inactive")
    if instrument.market_type is not policy.required_market_type:
        reasons.append("market_type_not_supported")
    if instrument.quote_asset.upper() != policy.required_quote_asset.upper():
        reasons.append("quote_asset_not_supported")
    if quality.measured_at_ms > decision_timestamp_ms:
        reasons.append("quality_snapshot_from_future")
    elif decision_timestamp_ms - quality.measured_at_ms > policy.maximum_quality_age_ms:
        reasons.append("quality_snapshot_stale")
    if quality.latest_candle_available_at_ms > decision_timestamp_ms:
        reasons.append("candle_availability_from_future")
    elif (
        decision_timestamp_ms - quality.latest_candle_available_at_ms > policy.maximum_candle_age_ms
    ):
        reasons.append("candle_data_stale")
    if quality.quote_volume_24h_usd < policy.minimum_quote_volume_24h_usd:
        reasons.append("quote_volume_below_minimum")
    if (
        policy.maximum_spread_bps is not None
        and quality.spread_bps is not None
        and quality.spread_bps > policy.maximum_spread_bps
    ):
        reasons.append("spread_above_maximum")
    if policy.maximum_spread_bps is not None and quality.spread_bps is None:
        reasons.append("spread_unavailable")
    if quality.candle_history_rows < policy.minimum_candle_history_rows:
        reasons.append("insufficient_candle_history")
    if quality.feature_history_rows < policy.minimum_feature_history_rows:
        reasons.append("insufficient_feature_history")
    if quality.symbol_risk_blocked:
        reasons.append("symbol_risk_blocked")

    healthy_sources = 0
    for coverage in quality.liquidation_coverage:
        if coverage.health is not SourceHealth.HEALTHY:
            continue
        if coverage.last_received_at_ms is None:
            continue
        if coverage.last_received_at_ms > decision_timestamp_ms:
            reasons.append(f"liquidation_source_future:{coverage.source}")
            continue
        if decision_timestamp_ms - coverage.last_received_at_ms > policy.maximum_liquidation_age_ms:
            reasons.append(f"liquidation_source_stale:{coverage.source}")
            continue
        healthy_sources += 1
    if healthy_sources < policy.minimum_healthy_liquidation_sources:
        reasons.append("insufficient_healthy_liquidation_sources")
    return reasons


def select_dynamic_universe(
    *,
    instruments: tuple[InstrumentSnapshot, ...],
    quality_snapshots: tuple[UniverseQualitySnapshot, ...],
    policy: DynamicUniversePolicy,
    decision_timestamp_ms: int,
) -> DynamicUniverseSnapshot:
    if decision_timestamp_ms <= 0:
        raise ValueError("decision_timestamp_ms must be > 0")
    instrument_ids = [instrument.canonical_instrument_id for instrument in instruments]
    if len(instrument_ids) != len(set(instrument_ids)):
        raise ValueError("duplicate instrument snapshots are not allowed")
    quality_ids = [snapshot.canonical_instrument_id for snapshot in quality_snapshots]
    if len(quality_ids) != len(set(quality_ids)):
        raise ValueError("duplicate quality snapshots are not allowed")
    unknown = sorted(set(quality_ids) - set(instrument_ids))
    if unknown:
        raise ValueError(f"quality snapshots reference unknown instruments: {unknown}")
    quality_by_id = {snapshot.canonical_instrument_id: snapshot for snapshot in quality_snapshots}

    decisions: list[UniverseInstrumentDecision] = []
    for instrument in sorted(instruments, key=lambda item: item.canonical_instrument_id):
        quality = quality_by_id.get(instrument.canonical_instrument_id)
        if quality is None:
            reasons = ["quality_snapshot_missing"]
        else:
            reasons = _quality_reasons(
                instrument=instrument,
                quality=quality,
                policy=policy,
                decision_timestamp_ms=decision_timestamp_ms,
            )
        included = not reasons
        decisions.append(
            UniverseInstrumentDecision(
                canonical_instrument_id=instrument.canonical_instrument_id,
                canonical_symbol=instrument.canonical_symbol,
                included=included,
                reason_codes=("eligible",) if included else tuple(sorted(set(reasons))),
            )
        )

    return DynamicUniverseSnapshot(
        schema_version="wickhunter-dynamic-universe-v1",
        policy_version=policy.policy_version,
        selected_at_ms=decision_timestamp_ms,
        decisions=tuple(decisions),
    )
