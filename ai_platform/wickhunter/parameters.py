from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ai_platform.wickhunter.canonical import canonical_sha256


@dataclass(frozen=True, slots=True)
class DecimalBound:
    minimum: Decimal
    maximum: Decimal

    def __post_init__(self) -> None:
        if not self.minimum.is_finite() or not self.maximum.is_finite():
            raise ValueError("parameter bounds must be finite")
        if self.minimum > self.maximum:
            raise ValueError("parameter minimum must not exceed maximum")

    def require(self, name: str, value: Decimal) -> None:
        if not value.is_finite() or not self.minimum <= value <= self.maximum:
            raise ValueError(f"{name} must be within [{self.minimum}, {self.maximum}], got {value}")


@dataclass(frozen=True, slots=True)
class IntegerBound:
    minimum: int
    maximum: int

    def __post_init__(self) -> None:
        if self.minimum > self.maximum:
            raise ValueError("parameter minimum must not exceed maximum")

    def require(self, name: str, value: int) -> None:
        if isinstance(value, bool) or not self.minimum <= value <= self.maximum:
            raise ValueError(f"{name} must be within [{self.minimum}, {self.maximum}], got {value}")


@dataclass(frozen=True, slots=True)
class WickHunterParameterBounds:
    liquidation_percentile: DecimalBound
    liquidation_zscore: DecimalBound
    burst_window_ms: IntegerBound
    minimum_quote_volume_usd: DecimalBound
    long_vwap_distance_ratio: DecimalBound
    short_vwap_distance_ratio: DecimalBound
    minimum_wick_ratio: DecimalBound
    minimum_volatility: DecimalBound
    maximum_volatility: DecimalBound
    cooldown_ms: IntegerBound
    maximum_event_age_ms: IntegerBound
    base_risk_ratio: DecimalBound
    leverage: DecimalBound
    dca_levels: IntegerBound
    dca_spacing_ratio: DecimalBound
    dca_total_risk_ratio: DecimalBound
    take_profit_ratio: DecimalBound
    stop_loss_ratio: DecimalBound
    maximum_holding_ms: IntegerBound
    minimum_confidence: DecimalBound
    risk_multiplier: DecimalBound


@dataclass(frozen=True, slots=True)
class WickHunterParameters:
    parameter_version: str
    liquidation_percentile: Decimal
    liquidation_zscore: Decimal
    burst_window_ms: int
    minimum_quote_volume_usd: Decimal
    long_vwap_distance_ratio: Decimal
    short_vwap_distance_ratio: Decimal
    minimum_wick_ratio: Decimal
    minimum_volatility: Decimal
    maximum_volatility: Decimal
    cooldown_ms: int
    maximum_event_age_ms: int
    base_risk_ratio: Decimal
    leverage: Decimal
    dca_enabled: bool
    dca_levels: int
    dca_spacing_ratio: Decimal
    dca_total_risk_ratio: Decimal
    take_profit_ratio: Decimal
    stop_loss_ratio: Decimal
    maximum_holding_ms: int
    minimum_confidence: Decimal
    minimum_risk_multiplier: Decimal
    maximum_risk_multiplier: Decimal

    def __post_init__(self) -> None:
        if not self.parameter_version.strip():
            raise ValueError("parameter_version must be non-empty")
        if self.minimum_volatility > self.maximum_volatility:
            raise ValueError("minimum_volatility must not exceed maximum_volatility")
        if self.minimum_risk_multiplier > self.maximum_risk_multiplier:
            raise ValueError("minimum_risk_multiplier must not exceed maximum_risk_multiplier")
        if not self.dca_enabled and self.dca_levels != 0:
            raise ValueError("disabled DCA requires dca_levels=0")
        if self.dca_enabled and self.dca_levels < 1:
            raise ValueError("enabled DCA requires at least one level")

    @property
    def parameter_hash(self) -> str:
        return canonical_sha256(self)


def validate_parameters(
    parameters: WickHunterParameters,
    bounds: WickHunterParameterBounds,
) -> None:
    bounds.liquidation_percentile.require(
        "liquidation_percentile", parameters.liquidation_percentile
    )
    bounds.liquidation_zscore.require("liquidation_zscore", parameters.liquidation_zscore)
    bounds.burst_window_ms.require("burst_window_ms", parameters.burst_window_ms)
    bounds.minimum_quote_volume_usd.require(
        "minimum_quote_volume_usd", parameters.minimum_quote_volume_usd
    )
    bounds.long_vwap_distance_ratio.require(
        "long_vwap_distance_ratio", parameters.long_vwap_distance_ratio
    )
    bounds.short_vwap_distance_ratio.require(
        "short_vwap_distance_ratio", parameters.short_vwap_distance_ratio
    )
    bounds.minimum_wick_ratio.require("minimum_wick_ratio", parameters.minimum_wick_ratio)
    bounds.minimum_volatility.require("minimum_volatility", parameters.minimum_volatility)
    bounds.maximum_volatility.require("maximum_volatility", parameters.maximum_volatility)
    bounds.cooldown_ms.require("cooldown_ms", parameters.cooldown_ms)
    bounds.maximum_event_age_ms.require("maximum_event_age_ms", parameters.maximum_event_age_ms)
    bounds.base_risk_ratio.require("base_risk_ratio", parameters.base_risk_ratio)
    bounds.leverage.require("leverage", parameters.leverage)
    bounds.dca_levels.require("dca_levels", parameters.dca_levels)
    bounds.dca_spacing_ratio.require("dca_spacing_ratio", parameters.dca_spacing_ratio)
    bounds.dca_total_risk_ratio.require("dca_total_risk_ratio", parameters.dca_total_risk_ratio)
    bounds.take_profit_ratio.require("take_profit_ratio", parameters.take_profit_ratio)
    bounds.stop_loss_ratio.require("stop_loss_ratio", parameters.stop_loss_ratio)
    bounds.maximum_holding_ms.require("maximum_holding_ms", parameters.maximum_holding_ms)
    bounds.minimum_confidence.require("minimum_confidence", parameters.minimum_confidence)
    bounds.risk_multiplier.require("minimum_risk_multiplier", parameters.minimum_risk_multiplier)
    bounds.risk_multiplier.require("maximum_risk_multiplier", parameters.maximum_risk_multiplier)
    if parameters.minimum_volatility > parameters.maximum_volatility:
        raise ValueError("volatility range is inverted")
    if parameters.dca_enabled and parameters.dca_total_risk_ratio < parameters.base_risk_ratio:
        raise ValueError("DCA total risk must not be below base risk")


DEFAULT_RESEARCH_BOUNDS = WickHunterParameterBounds(
    liquidation_percentile=DecimalBound(Decimal("0.50"), Decimal("0.995")),
    liquidation_zscore=DecimalBound(Decimal("0"), Decimal("8")),
    burst_window_ms=IntegerBound(5_000, 300_000),
    minimum_quote_volume_usd=DecimalBound(Decimal("1000000"), Decimal("500000000")),
    long_vwap_distance_ratio=DecimalBound(Decimal("0.001"), Decimal("0.05")),
    short_vwap_distance_ratio=DecimalBound(Decimal("0.001"), Decimal("0.05")),
    minimum_wick_ratio=DecimalBound(Decimal("0"), Decimal("0.20")),
    minimum_volatility=DecimalBound(Decimal("0"), Decimal("0.20")),
    maximum_volatility=DecimalBound(Decimal("0.001"), Decimal("0.50")),
    cooldown_ms=IntegerBound(0, 86_400_000),
    maximum_event_age_ms=IntegerBound(1_000, 300_000),
    base_risk_ratio=DecimalBound(Decimal("0.0005"), Decimal("0.01")),
    leverage=DecimalBound(Decimal("1"), Decimal("15")),
    dca_levels=IntegerBound(0, 5),
    dca_spacing_ratio=DecimalBound(Decimal("0.005"), Decimal("0.03")),
    dca_total_risk_ratio=DecimalBound(Decimal("0.0005"), Decimal("0.03")),
    take_profit_ratio=DecimalBound(Decimal("0.02"), Decimal("0.15")),
    stop_loss_ratio=DecimalBound(Decimal("0.01"), Decimal("0.08")),
    maximum_holding_ms=IntegerBound(60_000, 604_800_000),
    minimum_confidence=DecimalBound(Decimal("0.50"), Decimal("0.95")),
    risk_multiplier=DecimalBound(Decimal("0.25"), Decimal("1")),
)


# Compatibility prior only. The VWAP values are ratios: 0.003 = 0.3%, 0.005 = 0.5%.
INITIAL_COMPATIBILITY_PRIOR = WickHunterParameters(
    parameter_version="wickhunter-compatibility-prior-v1",
    liquidation_percentile=Decimal("0.50"),
    liquidation_zscore=Decimal("1.0"),
    burst_window_ms=60_000,
    minimum_quote_volume_usd=Decimal("10000000"),
    long_vwap_distance_ratio=Decimal("0.003"),
    short_vwap_distance_ratio=Decimal("0.005"),
    minimum_wick_ratio=Decimal("0.003"),
    minimum_volatility=Decimal("0.001"),
    maximum_volatility=Decimal("0.10"),
    cooldown_ms=300_000,
    maximum_event_age_ms=30_000,
    base_risk_ratio=Decimal("0.005"),
    leverage=Decimal("10"),
    dca_enabled=True,
    dca_levels=3,
    dca_spacing_ratio=Decimal("0.0125"),
    dca_total_risk_ratio=Decimal("0.015"),
    take_profit_ratio=Decimal("0.085"),
    stop_loss_ratio=Decimal("0.05"),
    maximum_holding_ms=86_400_000,
    minimum_confidence=Decimal("0.55"),
    minimum_risk_multiplier=Decimal("0.25"),
    maximum_risk_multiplier=Decimal("1"),
)

validate_parameters(INITIAL_COMPATIBILITY_PRIOR, DEFAULT_RESEARCH_BOUNDS)
