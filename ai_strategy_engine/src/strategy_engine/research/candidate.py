from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal, Self, cast

from pydantic import Field, JsonValue, model_validator

from strategy_engine.domain.models import CanonicalModel, StrategyDefinition
from strategy_engine.dsl.validator import StrategyValidationError, StrategyValidator
from strategy_engine.registry import FeatureRegistry, RegistryError, SearchSpaceRegistry

_FEATURE_SEARCH_SPACES = {
    "squeeze_ratio.v1": "squeeze",
    "supertrend_direction.v1": "supertrend",
    "macd.v1": "macd",
    "confirmed_pivot.v1": "pivot",
    "rsi.v1": "rsi",
    "stoch_rsi.v1": "stoch_rsi",
    "adx.v1": "adx",
    "mfi.v1": "mfi",
    "roc.v1": "roc",
    "wavetrend.v1": "wavetrend",
    "psar.v1": "psar",
    "atr_range_filter.v1": "atr_range_filter",
}
_SAFE_CONDITIONS: dict[str, tuple[str, JsonValue]] = {
    "macd.v1": ("gt", 0.0),
    "roc.v1": ("gt", 0.0),
    "rsi.v1": ("gt", 50.0),
    "atr.v1": ("gt", 0.0),
    "candle_geometry.v1": ("gt", 0.0),
}


class CandidateGenerationError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


class FalsificationTest(CanonicalModel):
    hypothesis: str = Field(min_length=1)
    reject_if: str = Field(min_length=1)
    minimum_trades: int = Field(ge=1)
    maximum_drawdown: float = Field(gt=0.0, le=1.0)


class FeatureSelection(CanonicalModel):
    feature_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    parameter_overrides: dict[str, JsonValue] = Field(default_factory=dict)


class CandidateRequest(CanonicalModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    request_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    model_identifier: str = Field(min_length=1)
    symbols: tuple[str, ...]
    timeframes: tuple[str, ...]
    features: tuple[FeatureSelection, ...]
    falsification_test: FalsificationTest
    max_features: int = Field(default=6, ge=1, le=6)
    max_conditions: int = Field(default=8, ge=1, le=8)

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        if not self.symbols or len(self.symbols) != len(set(self.symbols)):
            raise ValueError("symbols must be non-empty and unique")
        if not self.timeframes or len(self.timeframes) != len(set(self.timeframes)):
            raise ValueError("timeframes must be non-empty and unique")
        if not self.features:
            raise ValueError("at least one feature is required")
        if len(self.features) > self.max_features:
            raise ValueError("feature count exceeds max_features")
        feature_ids = [item.feature_id for item in self.features]
        if len(feature_ids) != len(set(feature_ids)):
            raise ValueError("feature IDs must be unique")
        undeclared = sorted({item.timeframe for item in self.features} - set(self.timeframes))
        if undeclared:
            raise ValueError(f"feature timeframes are undeclared: {undeclared}")
        return self


class CandidateGenerator:
    def __init__(
        self,
        registry: FeatureRegistry,
        search_spaces: SearchSpaceRegistry,
    ) -> None:
        self.registry = registry
        self.search_spaces = search_spaces
        self.validator = StrategyValidator(registry)

    def generate(self, request: CandidateRequest) -> StrategyDefinition:
        selections = {item.feature_id: item for item in request.features}
        try:
            ordered_ids = self.registry.resolve_dependencies(tuple(selections))
        except RegistryError as exc:
            raise CandidateGenerationError("FEATURE_REGISTRY_REJECTED", str(exc)) from exc

        feature_payloads: list[dict[str, JsonValue]] = []
        entry_conditions: list[dict[str, JsonValue]] = []
        for feature_id in ordered_ids:
            definition = self.registry.get(feature_id)
            if not definition.approved_for_ai or definition.status != "validated":
                raise CandidateGenerationError(
                    "FEATURE_NOT_APPROVED_FOR_AI",
                    f"feature is not validated and approved for AI use: {feature_id}",
                )
            selection = selections.get(feature_id)
            if selection is None:
                raise CandidateGenerationError(
                    "DEPENDENCY_NOT_DECLARED",
                    f"AI candidate request must declare dependency explicitly: {feature_id}",
                )
            try:
                resolved = self.registry.validate_parameters(
                    feature_id, cast(Mapping[str, object], selection.parameter_overrides)
                )
                space_name = _FEATURE_SEARCH_SPACES.get(feature_id)
                if space_name is not None:
                    self.search_spaces.get(space_name).validate_parameters(
                        cast(Mapping[str, object], selection.parameter_overrides)
                    )
            except RegistryError as exc:
                raise CandidateGenerationError("FEATURE_PARAMETERS_REJECTED", str(exc)) from exc

            feature_payloads.append(
                {
                    "id": feature_id,
                    "params": cast(dict[str, JsonValue], resolved),
                    "timeframe": selection.timeframe,
                    "confirmation": "closed_bar",
                }
            )
            condition = _SAFE_CONDITIONS.get(feature_id)
            if condition is not None and (
                "trigger" in definition.roles or "confirmation" in definition.roles
            ):
                operator, value = condition
                entry_conditions.append({"feature": feature_id, "op": operator, "value": value})

        if not entry_conditions:
            raise CandidateGenerationError(
                "NO_SAFE_ENTRY_TEMPLATE",
                "selected registry features do not have a bounded DSL entry template",
            )
        if len(entry_conditions) > request.max_conditions:
            raise CandidateGenerationError(
                "COMPLEXITY_LIMIT_EXCEEDED", "generated entry conditions exceed max_conditions"
            )

        strategy_payload: dict[str, Any] = {
            "schema_version": "1.0.0",
            "strategy_id": request.strategy_id,
            "version": request.version,
            "universe": {
                "symbols": list(request.symbols),
                "timeframes": list(request.timeframes),
            },
            "features": feature_payloads,
            "regime": None,
            "entry_long": {"all": entry_conditions},
            "entry_short": None,
            "exit": {"any": [{"risk": "time_stop"}]},
            "risk": {
                "max_leverage": 1.0,
                "max_exposure": 0.20,
                "max_open_positions": 2,
                "position_size": {"type": "risk_fraction", "value": 0.005},
            },
            "execution": {
                "use_closed_bars_only": True,
                "research_only": True,
                "execution_authority": False,
                "order_submission": False,
            },
            "provenance": {
                "producer": "ase02-ai-candidate-generator",
                "source_event_id": request.request_id,
                "lineage": [],
                "details": {
                    "created_by": "ai",
                    "model_identifier": request.model_identifier,
                    "registry_version": self.registry.version,
                    "falsification_test": request.falsification_test.model_dump(mode="json"),
                    "final_holdout_used": False,
                    "execution_authority": False,
                },
            },
        }
        try:
            return self.validator.validate(strategy_payload, generated_by_ai=True)
        except StrategyValidationError as exc:
            raise CandidateGenerationError(exc.reason_code, str(exc)) from exc
