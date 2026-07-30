from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from pydantic import ValidationError

from strategy_engine.domain.models import StrategyDefinition, ValidationReport
from strategy_engine.dsl.ast import Condition, ConditionGroup, ConditionOperator, DslReasonCode
from strategy_engine.registry import FeatureRegistry, RegistryError, SearchSpaceRegistry


class StrategyValidationError(ValueError):
    def __init__(self, reason_code: DslReasonCode | str, message: str) -> None:
        super().__init__(message)
        self.reason_code = (
            reason_code.value if isinstance(reason_code, DslReasonCode) else reason_code
        )


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
_ALLOWED_OPERATORS = frozenset(operator.value for operator in ConditionOperator)


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
            reason_code = DslReasonCode.DSL_SCHEMA_INVALID
            if any(error.get("loc", ())[-1:] == ("op",) for error in exc.errors()):
                reason_code = DslReasonCode.OPERATOR_NOT_ALLOWED
            raise StrategyValidationError(reason_code, str(exc)) from exc

        if parsed.execution.get("use_closed_bars_only") is not True:
            raise StrategyValidationError(
                DslReasonCode.CLOSED_BAR_POLICY_REQUIRED, "use_closed_bars_only must be true"
            )

        max_leverage = parsed.risk.get("max_leverage")
        if not isinstance(max_leverage, (int, float)) or isinstance(max_leverage, bool):
            raise StrategyValidationError(
                DslReasonCode.RISK_POLICY_INVALID, "max_leverage must be numeric"
            )
        if float(max_leverage) < 1.0:
            raise StrategyValidationError(
                DslReasonCode.RISK_POLICY_INVALID, "max_leverage must be >= 1"
            )

        self._validate_dca(parsed.risk)
        declared_features = {feature.id for feature in parsed.features}
        if len(declared_features) != len(parsed.features):
            raise StrategyValidationError(
                DslReasonCode.DUPLICATE_FEATURE, "feature IDs must be unique"
            )

        for feature in parsed.features:
            try:
                definition = self.registry.get(feature.id)
                resolved = self.registry.validate_parameters(feature.id, feature.params)
            except RegistryError as exc:
                raise StrategyValidationError(
                    DslReasonCode.FEATURE_REGISTRY_REJECTED, str(exc)
                ) from exc

            if generated_by_ai and not definition.approved_for_ai:
                raise StrategyValidationError(
                    DslReasonCode.FEATURE_NOT_APPROVED_FOR_AI,
                    f"feature is not approved for AI use: {feature.id}",
                )
            if feature.timeframe not in parsed.universe.timeframes:
                raise StrategyValidationError(
                    DslReasonCode.UNDECLARED_TIMEFRAME,
                    f"feature timeframe is not declared: {feature.timeframe}",
                )
            if feature.confirmation == "confirmed_htf" and "htf" not in definition.timestamp_policy:
                raise StrategyValidationError(
                    DslReasonCode.HTF_POLICY_MISMATCH,
                    f"feature does not declare confirmed HTF semantics: {feature.id}",
                )
            if resolved.get("compatibility_mode") == "legacy_bug_compatible":
                details = parsed.provenance.details
                if details.get("research_mode") is not True:
                    raise StrategyValidationError(
                        DslReasonCode.LEGACY_MODE_FORBIDDEN,
                        "legacy_bug_compatible is permitted only in explicit research_mode",
                    )
            if self.search_spaces is not None and feature.id in _FEATURE_SEARCH_SPACES:
                try:
                    self.search_spaces.get(_FEATURE_SEARCH_SPACES[feature.id]).validate_parameters(
                        feature.params
                    )
                except RegistryError as exc:
                    raise StrategyValidationError(
                        DslReasonCode.SEARCH_SPACE_REJECTED, str(exc)
                    ) from exc

        self._validate_condition_group(parsed.regime, declared_features, "regime", optional=True)
        self._validate_condition_group(parsed.entry_long, declared_features, "entry_long")
        self._validate_condition_group(
            parsed.entry_short, declared_features, "entry_short", optional=True
        )
        self._validate_condition_group(parsed.exit, declared_features, "exit")
        return parsed

    def validate_report(
        self,
        strategy: Mapping[str, object],
        *,
        generated_by_ai: bool = False,
        checked_at: datetime | None = None,
    ) -> ValidationReport:
        checked = checked_at or datetime.now(UTC)
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
        if (
            isinstance(position_size, Mapping)
            and position_size.get("type") == "dca"
            and risk.get("max_exposure") is None
        ):
            raise StrategyValidationError(
                DslReasonCode.DCA_REQUIRES_MAX_EXPOSURE, "DCA requires max_exposure"
            )

    def _validate_condition_group(
        self,
        group: ConditionGroup | None,
        declared_features: set[str],
        label: str,
        *,
        optional: bool = False,
    ) -> None:
        if group is None:
            if optional:
                return
            raise StrategyValidationError(
                DslReasonCode.CONDITION_GROUP_MISSING, f"{label} is required"
            )
        branches = group.branches()
        if not branches:
            raise StrategyValidationError(
                DslReasonCode.CONDITION_GROUP_EMPTY, f"{label} cannot be empty"
            )
        for group_name, conditions in branches:
            if not conditions:
                raise StrategyValidationError(
                    DslReasonCode.CONDITION_GROUP_EMPTY,
                    f"{label}.{group_name} cannot be empty",
                )
            for index, node in enumerate(conditions):
                child_label = f"{label}.{group_name}[{index}]"
                if isinstance(node, ConditionGroup):
                    self._validate_condition_group(node, declared_features, child_label)
                else:
                    self._validate_condition(node, declared_features, child_label)

    @staticmethod
    def _validate_condition(
        condition: Condition,
        declared_features: set[str],
        label: str,
    ) -> None:
        selectors = [
            name for name in ("feature", "event", "risk") if getattr(condition, name) is not None
        ]
        if len(selectors) != 1:
            raise StrategyValidationError(
                DslReasonCode.CONDITION_INVALID,
                f"{label} requires exactly one feature, event, or risk selector",
            )
        if condition.feature is not None and condition.feature not in declared_features:
            raise StrategyValidationError(
                DslReasonCode.FEATURE_NOT_DECLARED,
                f"{label} references an undeclared feature: {condition.feature}",
            )
        if condition.op is not None and condition.op not in _ALLOWED_OPERATORS:
            raise StrategyValidationError(
                DslReasonCode.OPERATOR_NOT_ALLOWED,
                f"{label} uses unsupported operator: {condition.op}",
            )
