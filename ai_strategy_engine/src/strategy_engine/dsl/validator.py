from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, cast

from pydantic import ValidationError

from strategy_engine.domain.models import StrategyDefinition, ValidationReport
from strategy_engine.registry import FeatureRegistry, RegistryError, SearchSpaceRegistry


class StrategyValidationError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


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
_ALLOWED_GROUP_KEYS = {"all", "any", "none"}
_ALLOWED_OPERATORS = {
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "crosses_above",
    "crosses_below",
    "in_range",
    "bars_since_lte",
}


class StrategyValidator:
    def __init__(
        self,
        registry: FeatureRegistry,
        search_spaces: SearchSpaceRegistry | None = None,
    ) -> None:
        self.registry = registry
        self.search_spaces = search_spaces

    def validate(
        self,
        strategy: Mapping[str, object],
        *,
        generated_by_ai: bool = False,
    ) -> StrategyDefinition:
        try:
            parsed = StrategyDefinition.model_validate(strategy)
        except ValidationError as exc:
            raise StrategyValidationError("DSL_SCHEMA_INVALID", str(exc)) from exc

        if parsed.execution.get("use_closed_bars_only") is not True:
            raise StrategyValidationError(
                "CLOSED_BAR_POLICY_REQUIRED", "use_closed_bars_only must be true"
            )

        max_leverage = parsed.risk.get("max_leverage")
        if not isinstance(max_leverage, (int, float)) or isinstance(max_leverage, bool):
            raise StrategyValidationError("RISK_POLICY_INVALID", "max_leverage must be numeric")
        if float(max_leverage) < 1.0:
            raise StrategyValidationError("RISK_POLICY_INVALID", "max_leverage must be >= 1")

        self._validate_dca(parsed.risk)
        declared_features = {feature.id for feature in parsed.features}
        if len(declared_features) != len(parsed.features):
            raise StrategyValidationError("DUPLICATE_FEATURE", "feature IDs must be unique")

        for feature in parsed.features:
            try:
                definition = self.registry.get(feature.id)
                resolved = self.registry.validate_parameters(feature.id, feature.params)
            except RegistryError as exc:
                raise StrategyValidationError("FEATURE_REGISTRY_REJECTED", str(exc)) from exc

            if generated_by_ai and not definition.approved_for_ai:
                raise StrategyValidationError(
                    "FEATURE_NOT_APPROVED_FOR_AI",
                    f"feature is not approved for AI use: {feature.id}",
                )
            if feature.timeframe not in parsed.universe.timeframes:
                raise StrategyValidationError(
                    "UNDECLARED_TIMEFRAME",
                    f"feature timeframe is not declared: {feature.timeframe}",
                )
            if feature.confirmation == "confirmed_htf" and "htf" not in definition.timestamp_policy:
                raise StrategyValidationError(
                    "HTF_POLICY_MISMATCH",
                    f"feature does not declare confirmed HTF semantics: {feature.id}",
                )
            if resolved.get("compatibility_mode") == "legacy_bug_compatible":
                details = parsed.provenance.details
                if details.get("research_mode") is not True:
                    raise StrategyValidationError(
                        "LEGACY_MODE_FORBIDDEN",
                        "legacy_bug_compatible is permitted only in explicit research_mode",
                    )
            if self.search_spaces is not None and feature.id in _FEATURE_SEARCH_SPACES:
                try:
                    self.search_spaces.get(_FEATURE_SEARCH_SPACES[feature.id]).validate_parameters(
                        feature.params
                    )
                except RegistryError as exc:
                    raise StrategyValidationError("SEARCH_SPACE_REJECTED", str(exc)) from exc

        self._validate_condition_group(parsed.regime, declared_features, "regime", optional=True)
        self._validate_condition_group(parsed.entry_long, declared_features, "entry_long")
        self._validate_condition_group(parsed.entry_short, declared_features, "entry_short", optional=True)
        self._validate_condition_group(parsed.exit, declared_features, "exit")
        return parsed

    def validate_report(
        self,
        strategy: Mapping[str, object],
        *,
        generated_by_ai: bool = False,
        checked_at: datetime | None = None,
    ) -> ValidationReport:
        checked = checked_at or datetime.now(timezone.utc)
        errors: tuple[str, ...]
        try:
            parsed = StrategyDefinition.model_validate(strategy)
            strategy_hash = parsed.canonical_sha256()
        except ValidationError:
            strategy_hash = "0" * 64
        try:
            self.validate(strategy, generated_by_ai=generated_by_ai)
            errors = ()
        except StrategyValidationError as exc:
            errors = (f"{exc.reason_code}:{exc}",)
        return ValidationReport(
            valid=not errors,
            checked_at=checked,
            strategy_hash=strategy_hash,
            errors=errors,
        )

    @staticmethod
    def _validate_dca(risk: Mapping[str, object]) -> None:
        position_size = risk.get("position_size")
        if isinstance(position_size, Mapping) and position_size.get("type") == "dca":
            if risk.get("max_exposure") is None:
                raise StrategyValidationError(
                    "DCA_REQUIRES_MAX_EXPOSURE", "DCA requires max_exposure"
                )

    def _validate_condition_group(
        self,
        raw_group: Mapping[str, object] | None,
        declared_features: set[str],
        label: str,
        *,
        optional: bool = False,
    ) -> None:
        if raw_group is None:
            if optional:
                return
            raise StrategyValidationError("CONDITION_GROUP_MISSING", f"{label} is required")
        unknown_keys = set(raw_group) - _ALLOWED_GROUP_KEYS
        if unknown_keys:
            raise StrategyValidationError(
                "CONDITION_GROUP_INVALID", f"{label} has unsupported keys: {sorted(unknown_keys)}"
            )
        if not raw_group:
            raise StrategyValidationError("CONDITION_GROUP_EMPTY", f"{label} cannot be empty")
        for group_name, conditions_raw in raw_group.items():
            if not isinstance(conditions_raw, list):
                raise StrategyValidationError(
                    "CONDITION_GROUP_INVALID", f"{label}.{group_name} must be a list"
                )
            conditions = cast(list[object], conditions_raw)
            if not conditions:
                raise StrategyValidationError(
                    "CONDITION_GROUP_EMPTY", f"{label}.{group_name} cannot be empty"
                )
            for index, raw_condition in enumerate(conditions):
                if not isinstance(raw_condition, Mapping):
                    raise StrategyValidationError(
                        "CONDITION_INVALID", f"{label}.{group_name}[{index}] must be an object"
                    )
                condition = cast(Mapping[str, object], raw_condition)
                nested_keys = set(condition) & _ALLOWED_GROUP_KEYS
                if nested_keys:
                    self._validate_condition_group(
                        condition,
                        declared_features,
                        f"{label}.{group_name}[{index}]",
                    )
                    continue
                self._validate_condition(
                    condition,
                    declared_features,
                    f"{label}.{group_name}[{index}]",
                )

    @staticmethod
    def _validate_condition(
        condition: Mapping[str, object],
        declared_features: set[str],
        label: str,
    ) -> None:
        selectors = [key for key in ("feature", "event", "risk") if key in condition]
        if len(selectors) != 1:
            raise StrategyValidationError(
                "CONDITION_INVALID", f"{label} requires exactly one feature, event, or risk selector"
            )
        feature = condition.get("feature")
        if feature is not None:
            if not isinstance(feature, str) or feature not in declared_features:
                raise StrategyValidationError(
                    "FEATURE_NOT_DECLARED", f"{label} references an undeclared feature: {feature}"
                )
        operator = condition.get("op")
        if operator is not None and operator not in _ALLOWED_OPERATORS:
            raise StrategyValidationError(
                "OPERATOR_NOT_ALLOWED", f"{label} uses unsupported operator: {operator}"
            )
        if "parameter" in condition and not isinstance(condition["parameter"], str):
            raise StrategyValidationError(
                "CONDITION_INVALID", f"{label}.parameter must be a string"
            )
        allowed = {
            "feature",
            "event",
            "risk",
            "op",
            "value",
            "parameter",
            "direction",
        }
        unknown = set(condition) - allowed
        if unknown:
            raise StrategyValidationError(
                "CONDITION_INVALID", f"{label} has unsupported keys: {sorted(unknown)}"
            )
