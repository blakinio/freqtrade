"""Versioned, immutable assumptions used to identify PAPER execution semantics."""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


NonNegativeDecimal = Annotated[Decimal, Field(ge=0)]
NonNegativeInt = Annotated[int, Field(ge=0, strict=True)]
PositiveInt = Annotated[int, Field(gt=0, strict=True)]
NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ImmutableModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
        hide_input_in_errors=True,
    )


class AssumptionStatus(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class Limitation(ImmutableModel):
    """Stable, digest-bound disclosure of missing or approximate realism."""

    code: Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*$")]
    description: NonBlank


class Assumption(ImmutableModel):
    """Common fail-closed state for one execution-realism assumption."""

    status: AssumptionStatus
    model: NonBlank | None
    limitations: tuple[Limitation, ...]

    @model_validator(mode="after")
    def validate_disclosure(self) -> Assumption:
        if self.status is AssumptionStatus.SUPPORTED and self.model is None:
            raise ValueError("supported assumptions require an explicit model")
        if self.status is not AssumptionStatus.SUPPORTED:
            if self.model is not None:
                raise ValueError(
                    "unsupported or unknown assumptions cannot name an implemented model"
                )
            if not self.limitations:
                raise ValueError("unsupported or unknown assumptions require a limitation")
        codes = [item.code for item in self.limitations]
        if len(codes) != len(set(codes)):
            raise ValueError("limitation codes must be unique within an assumption")
        return self


class FeeModel(Assumption):
    maker_rate: NonNegativeDecimal | None
    taker_rate: NonNegativeDecimal | None

    @model_validator(mode="after")
    def validate_values(self) -> FeeModel:
        _require_values_for_supported(self, "maker_rate", "taker_rate")
        return self


class BpsModel(Assumption):
    bps: NonNegativeDecimal | None

    @model_validator(mode="after")
    def validate_values(self) -> BpsModel:
        _require_values_for_supported(self, "bps")
        return self


class LatencyModel(Assumption):
    submit_ms: NonNegativeInt | None
    acknowledge_ms: NonNegativeInt | None
    fill_ms: NonNegativeInt | None

    @model_validator(mode="after")
    def validate_values(self) -> LatencyModel:
        _require_values_for_supported(self, "submit_ms", "acknowledge_ms", "fill_ms")
        return self


class OrderTypeModel(Assumption):
    order_types: tuple[Literal["market", "limit", "stop", "stop_limit"], ...] | None

    @field_validator("order_types")
    @classmethod
    def normalize_order_types(cls, value: tuple[str, ...] | None) -> tuple[str, ...] | None:
        return None if value is None else tuple(sorted(value))

    @model_validator(mode="after")
    def validate_values(self) -> OrderTypeModel:
        _require_values_for_supported(self, "order_types")
        if self.order_types is not None:
            if not self.order_types:
                raise ValueError("supported order types cannot be empty")
            if len(self.order_types) != len(set(self.order_types)):
                raise ValueError("order types must be unique")
        return self


class LiquidityModel(Assumption):
    max_participation_rate: Annotated[Decimal, Field(ge=0, le=1)] | None
    depth_levels: PositiveInt | None

    @model_validator(mode="after")
    def validate_values(self) -> LiquidityModel:
        _require_values_for_supported(self, "max_participation_rate", "depth_levels")
        return self


class PartialFillModel(Assumption):
    policy: Literal["all_or_none", "volume_proportional", "deterministic_chunks"] | None
    minimum_fill_ratio: Annotated[Decimal, Field(gt=0, le=1)] | None

    @model_validator(mode="after")
    def validate_values(self) -> PartialFillModel:
        _require_values_for_supported(self, "policy", "minimum_fill_ratio")
        if self.policy == "all_or_none" and self.minimum_fill_ratio != Decimal("1"):
            raise ValueError("all_or_none requires minimum_fill_ratio exactly 1")
        return self


class CancelReplaceModel(Assumption):
    cancel_timeout_ms: NonNegativeInt | None
    replace_latency_ms: NonNegativeInt | None

    @model_validator(mode="after")
    def validate_values(self) -> CancelReplaceModel:
        _require_values_for_supported(self, "cancel_timeout_ms", "replace_latency_ms")
        return self


class StaleDataModel(Assumption):
    maximum_age_ms: NonNegativeInt | None
    action: Literal["reject_new_orders", "cancel_open_orders", "suspend_execution"] | None

    @model_validator(mode="after")
    def validate_values(self) -> StaleDataModel:
        _require_values_for_supported(self, "maximum_age_ms", "action")
        return self


class FundingModel(Assumption):
    rate_bps_per_interval: Decimal | None
    interval_seconds: PositiveInt | None

    @model_validator(mode="after")
    def validate_values(self) -> FundingModel:
        _require_values_for_supported(self, "rate_bps_per_interval", "interval_seconds")
        return self


class MarginModel(Assumption):
    maximum_leverage: Annotated[Decimal, Field(ge=1)] | None
    maintenance_margin_rate: Annotated[Decimal, Field(ge=0, lt=1)] | None

    @model_validator(mode="after")
    def validate_values(self) -> MarginModel:
        _require_values_for_supported(self, "maximum_leverage", "maintenance_margin_rate")
        return self


class LiquidationModel(Assumption):
    maintenance_buffer_rate: Annotated[Decimal, Field(ge=0, lt=1)] | None
    price_source: Literal["mark", "last", "index"] | None

    @model_validator(mode="after")
    def validate_values(self) -> LiquidationModel:
        _require_values_for_supported(self, "maintenance_buffer_rate", "price_source")
        return self


class ThrottlingModel(Assumption):
    requests_per_minute: PositiveInt | None
    burst_size: PositiveInt | None

    @model_validator(mode="after")
    def validate_values(self) -> ThrottlingModel:
        _require_values_for_supported(self, "requests_per_minute", "burst_size")
        return self


def _require_values_for_supported(assumption: Assumption, *fields: str) -> None:
    values = [getattr(assumption, field) for field in fields]
    if assumption.status is AssumptionStatus.SUPPORTED and any(value is None for value in values):
        raise ValueError("supported assumptions require every material value")
    if assumption.status is not AssumptionStatus.SUPPORTED and any(
        value is not None for value in values
    ):
        raise ValueError("unsupported or unknown assumptions cannot contain modeled values")


class PaperExecutionProfile(ImmutableModel):
    """Complete v1 PAPER assumptions; the SHA-256 digest is its immutable identity."""

    schema_version: Literal["paper-execution-profile-v1"]
    backwards_compatibility: Literal["exact-version-and-digest-only"]
    venue: NonBlank
    market_type: Literal["spot", "margin", "futures"]
    order_types: OrderTypeModel
    fee: FeeModel
    spread: BpsModel
    slippage: BpsModel
    latency: LatencyModel
    liquidity: LiquidityModel
    partial_fill: PartialFillModel
    cancel_replace: CancelReplaceModel
    stale_data: StaleDataModel
    funding: FundingModel
    margin: MarginModel
    liquidation: LiquidationModel
    throttling: ThrottlingModel

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def canonical_bytes(self) -> bytes:
        return self.canonical_json().encode("utf-8")

    def canonical_json(self) -> str:
        normalized = _normalize(self.model_dump(mode="python"))
        return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _normalize(value: Any) -> Any:
    if isinstance(value, Decimal):
        normalized = value.normalize()
        return "0" if normalized == 0 else format(normalized, "f")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        normalized_items = [_normalize(item) for item in value]
        if all(isinstance(item, dict) and "code" in item for item in normalized_items):
            return sorted(normalized_items, key=lambda item: item["code"])
        return normalized_items
    return value


def _freeze_evidence(value: Any) -> Any:
    """Recursively freeze comparison evidence so digest-bound values cannot be mutated."""

    if isinstance(value, dict):
        return tuple((key, _freeze_evidence(item)) for key, item in sorted(value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_evidence(item) for item in value)
    return value


class ComparisonReasonCode(StrEnum):
    IDENTICAL_PROFILE = "IDENTICAL_PROFILE"
    DIFFERENT_PROFILE_IDENTITY = "DIFFERENT_PROFILE_IDENTITY"
    MATERIAL_ASSUMPTION_DIFFERENCE = "MATERIAL_ASSUMPTION_DIFFERENCE"


class ProfileDifference(ImmutableModel):
    path: NonBlank
    left: Any
    right: Any
    reason_code: Literal[ComparisonReasonCode.MATERIAL_ASSUMPTION_DIFFERENCE]


class ProfileComparison(ImmutableModel):
    comparable: bool
    identical: bool
    left_digest: NonBlank
    right_digest: NonBlank
    reason_codes: tuple[ComparisonReasonCode, ...]
    differences: tuple[ProfileDifference, ...]


def compare_profiles(
    left: PaperExecutionProfile, right: PaperExecutionProfile
) -> ProfileComparison:
    """Compare exact identities; unequal profiles are disclosed and never silently comparable."""

    if left.digest == right.digest:
        return ProfileComparison(
            comparable=True,
            identical=True,
            left_digest=left.digest,
            right_digest=right.digest,
            reason_codes=(ComparisonReasonCode.IDENTICAL_PROFILE,),
            differences=(),
        )
    differences = tuple(_differences(_normalize(left.model_dump()), _normalize(right.model_dump())))
    return ProfileComparison(
        comparable=False,
        identical=False,
        left_digest=left.digest,
        right_digest=right.digest,
        reason_codes=(
            ComparisonReasonCode.DIFFERENT_PROFILE_IDENTITY,
            ComparisonReasonCode.MATERIAL_ASSUMPTION_DIFFERENCE,
        ),
        differences=differences,
    )


def _differences(left: Any, right: Any, path: str = "$") -> list[ProfileDifference]:
    if left == right:
        return []
    if isinstance(left, dict) and isinstance(right, dict):
        result: list[ProfileDifference] = []
        for key in sorted(left.keys() | right.keys()):
            result.extend(_differences(left.get(key), right.get(key), f"{path}.{key}"))
        return result
    return [
        ProfileDifference(
            path=path,
            left=_freeze_evidence(left),
            right=_freeze_evidence(right),
            reason_code=ComparisonReasonCode.MATERIAL_ASSUMPTION_DIFFERENCE,
        )
    ]
