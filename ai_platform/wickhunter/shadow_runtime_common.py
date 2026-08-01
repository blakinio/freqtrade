from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from ai_platform.wickhunter.canonical import canonical_sha256
from ai_platform.wickhunter.contracts import SourceHealth


RUNTIME_STATE_SCHEMA_VERSION = "wickhunter-shadow-runtime-state-v1"
RUNTIME_SNAPSHOT_SCHEMA_VERSION = "wickhunter-portal-observability-snapshot-v1"
RUNTIME_PARITY_SCHEMA_VERSION = "wickhunter-replay-shadow-parity-v1"
RUNTIME_STORE_SCHEMA_VERSION = "wickhunter-shadow-runtime-store-v1"


class ShadowRuntimeError(RuntimeError):
    """Raised when the shadow runtime cannot continue safely."""


class RuntimeHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAIL_CLOSED = "fail_closed"


class PositionCloseReason(StrEnum):
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    OPERATOR_RESET = "operator_reset"


def _require_text(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ShadowRuntimeError(f"{field} must be non-empty")
    return normalized


def _require_sha256(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise ShadowRuntimeError(f"{field} must be a lowercase SHA-256 digest")
    return normalized


def _require_git_sha(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 40 or any(char not in "0123456789abcdef" for char in normalized):
        raise ShadowRuntimeError(f"{field} must be a lowercase 40-character Git SHA")
    return normalized


def _require_finite(value: Decimal, *, field: str) -> Decimal:
    if not value.is_finite():
        raise ShadowRuntimeError(f"{field} must be finite")
    return value


def _require_non_negative(value: Decimal, *, field: str) -> Decimal:
    _require_finite(value, field=field)
    if value < 0:
        raise ShadowRuntimeError(f"{field} must be >= 0")
    return value


def _require_positive(value: Decimal, *, field: str) -> Decimal:
    _require_finite(value, field=field)
    if value <= 0:
        raise ShadowRuntimeError(f"{field} must be > 0")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.00000001"))


@dataclass(frozen=True, slots=True)
class ShadowRuntimePolicy:
    policy_version: str
    simulated_initial_equity_quote: Decimal
    maximum_universe_age_ms: int
    maximum_source_age_ms: int
    minimum_healthy_sources: int
    maximum_open_positions: int
    maximum_drawdown_ratio: Decimal
    decision_history_limit: int = 100
    require_healthy_model_drift: bool = True
    require_healthy_data_drift: bool = True

    def __post_init__(self) -> None:
        _require_text(self.policy_version, field="policy_version")
        _require_positive(
            self.simulated_initial_equity_quote,
            field="simulated_initial_equity_quote",
        )
        for field_name in (
            "maximum_universe_age_ms",
            "maximum_source_age_ms",
            "minimum_healthy_sources",
            "maximum_open_positions",
            "decision_history_limit",
        ):
            if getattr(self, field_name) < 1:
                raise ShadowRuntimeError(f"{field_name} must be >= 1")
        if not Decimal("0") < self.maximum_drawdown_ratio < Decimal("1"):
            raise ShadowRuntimeError("maximum_drawdown_ratio must be in (0, 1)")

    @property
    def policy_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class RuntimeSourceStatus:
    source: str
    health: SourceHealth
    observed_at_ms: int
    last_received_at_ms: int | None
    age_ms: int | None
    fresh: bool

    def __post_init__(self) -> None:
        _require_text(self.source, field="source")
        if self.observed_at_ms <= 0:
            raise ShadowRuntimeError("source observed_at_ms must be > 0")
        if self.last_received_at_ms is None:
            if self.age_ms is not None or self.fresh:
                raise ShadowRuntimeError("source without data cannot be fresh")
        else:
            if self.last_received_at_ms <= 0 or self.age_ms is None or self.age_ms < 0:
                raise ShadowRuntimeError("source age evidence is invalid")
