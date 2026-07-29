from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias

from pydantic import JsonValue

from strategy_engine.domain.models import Action, Side, StrategyDefinition

SnapshotValue: TypeAlias = JsonValue | Mapping[str, JsonValue]  # noqa: UP040


class DslEvaluationError(ValueError):
    pass


class DecisionSection(StrEnum):
    REGIME = "regime"
    ENTRY_LONG = "entry_long"
    ENTRY_SHORT = "entry_short"
    EXIT = "exit"
    NONE = "none"


@dataclass(frozen=True)
class DslDecision:
    side: Side
    action: Action
    section: DecisionSection
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationSnapshot:
    features: Mapping[str, SnapshotValue]
    previous_features: Mapping[str, SnapshotValue]
    events: Mapping[str, JsonValue]
    risk: Mapping[str, JsonValue]


class StrategyEvaluator:
    def evaluate(
        self,
        strategy: StrategyDefinition,
        snapshot: EvaluationSnapshot,
        *,
        position_side: Side = Side.FLAT,
    ) -> DslDecision:
        regime_matches = strategy.regime is None or self._evaluate_group(
            strategy.regime, snapshot, "regime"
        )
        exit_matches = self._evaluate_group(strategy.exit, snapshot, "exit")
        if position_side is not Side.FLAT and exit_matches:
            return DslDecision(
                side=position_side,
                action=Action.EXIT,
                section=DecisionSection.EXIT,
                reason_codes=("DSL_EXIT_MATCHED",),
            )
        if not regime_matches:
            return DslDecision(
                side=Side.FLAT,
                action=Action.HOLD,
                section=DecisionSection.REGIME,
                reason_codes=("DSL_REGIME_REJECTED",),
            )
        if position_side is not Side.FLAT:
            return DslDecision(
                side=position_side,
                action=Action.HOLD,
                section=DecisionSection.NONE,
                reason_codes=("DSL_POSITION_HELD",),
            )
        if self._evaluate_group(strategy.entry_long, snapshot, "entry_long"):
            return DslDecision(
                side=Side.LONG,
                action=Action.ENTER,
                section=DecisionSection.ENTRY_LONG,
                reason_codes=("DSL_ENTRY_LONG_MATCHED",),
            )
        if strategy.entry_short is not None and self._evaluate_group(
            strategy.entry_short, snapshot, "entry_short"
        ):
            return DslDecision(
                side=Side.SHORT,
                action=Action.ENTER,
                section=DecisionSection.ENTRY_SHORT,
                reason_codes=("DSL_ENTRY_SHORT_MATCHED",),
            )
        return DslDecision(
            side=Side.FLAT,
            action=Action.HOLD,
            section=DecisionSection.NONE,
            reason_codes=("DSL_NO_ENTRY_MATCHED",),
        )

    def _evaluate_group(
        self,
        group: Mapping[str, JsonValue],
        snapshot: EvaluationSnapshot,
        label: str,
    ) -> bool:
        results: list[bool] = []
        for operator in ("all", "any", "none"):
            raw_conditions = group.get(operator)
            if raw_conditions is None:
                continue
            if not isinstance(raw_conditions, list):
                raise DslEvaluationError(f"{label}.{operator} must be a list")
            condition_results = [
                self._evaluate_node(condition, snapshot, f"{label}.{operator}[{index}]")
                for index, condition in enumerate(raw_conditions)
            ]
            if operator == "all":
                results.append(all(condition_results))
            elif operator == "any":
                results.append(any(condition_results))
            else:
                results.append(not any(condition_results))
        if not results:
            raise DslEvaluationError(f"{label} contains no supported condition group")
        return all(results)

    def _evaluate_node(
        self,
        raw_node: JsonValue,
        snapshot: EvaluationSnapshot,
        label: str,
    ) -> bool:
        if not isinstance(raw_node, dict):
            raise DslEvaluationError(f"{label} must be an object")
        node = raw_node
        if set(node) & {"all", "any", "none"}:
            return self._evaluate_group(node, snapshot, label)
        if "feature" in node:
            return self._evaluate_feature(node, snapshot, label)
        if "event" in node:
            return self._evaluate_named(node, snapshot.events, "event", label)
        if "risk" in node:
            return self._evaluate_named(node, snapshot.risk, "risk", label)
        raise DslEvaluationError(f"{label} has no selector")

    def _evaluate_feature(
        self,
        node: Mapping[str, JsonValue],
        snapshot: EvaluationSnapshot,
        label: str,
    ) -> bool:
        feature_id = node.get("feature")
        if not isinstance(feature_id, str):
            raise DslEvaluationError(f"{label}.feature must be a string")
        if feature_id not in snapshot.features:
            raise DslEvaluationError(f"missing feature value: {feature_id}")
        current = self._select_parameter(
            snapshot.features[feature_id], node.get("parameter"), label
        )
        previous = None
        if feature_id in snapshot.previous_features:
            previous = self._select_parameter(
                snapshot.previous_features[feature_id], node.get("parameter"), label
            )
        return self._compare(node, current, previous, label)

    def _evaluate_named(
        self,
        node: Mapping[str, JsonValue],
        values: Mapping[str, JsonValue],
        selector: str,
        label: str,
    ) -> bool:
        name = node.get(selector)
        if not isinstance(name, str):
            raise DslEvaluationError(f"{label}.{selector} must be a string")
        if name not in values:
            raise DslEvaluationError(f"missing {selector} value: {name}")
        current = values[name]
        direction = node.get("direction")
        if direction is not None:
            return current == direction
        if "op" not in node:
            return bool(current)
        return self._compare(node, current, None, label)

    @staticmethod
    def _select_parameter(
        value: SnapshotValue,
        raw_parameter: JsonValue | None,
        label: str,
    ) -> JsonValue:
        if raw_parameter is None:
            if isinstance(value, Mapping):
                if "value" not in value:
                    raise DslEvaluationError(
                        f"{label} requires parameter for a structured feature value"
                    )
                return value["value"]
            return value
        if not isinstance(raw_parameter, str):
            raise DslEvaluationError(f"{label}.parameter must be a string")
        if not isinstance(value, Mapping) or raw_parameter not in value:
            raise DslEvaluationError(f"{label} missing feature parameter {raw_parameter}")
        return value[raw_parameter]

    @staticmethod
    def _compare(
        node: Mapping[str, JsonValue],
        current: JsonValue,
        previous: JsonValue | None,
        label: str,
    ) -> bool:
        operator = node.get("op", "eq")
        expected = node.get("value", True)
        if operator == "eq":
            return current == expected
        if operator == "ne":
            return current != expected
        if operator in {"gt", "gte", "lt", "lte"}:
            left, right = _numeric_pair(current, expected, label)
            if operator == "gt":
                return left > right
            if operator == "gte":
                return left >= right
            if operator == "lt":
                return left < right
            return left <= right
        if operator in {"crosses_above", "crosses_below"}:
            if previous is None:
                return False
            current_number, threshold = _numeric_pair(current, expected, label)
            previous_number, _ = _numeric_pair(previous, expected, label)
            if operator == "crosses_above":
                return previous_number <= threshold < current_number
            return previous_number >= threshold > current_number
        if operator == "in_range":
            if not isinstance(expected, Sequence) or isinstance(expected, (str, bytes)):
                raise DslEvaluationError(f"{label}.value must be a two-value range")
            values = list(expected)
            if len(values) != 2:
                raise DslEvaluationError(f"{label}.value must be a two-value range")
            number, low = _numeric_pair(current, values[0], label)
            _, high = _numeric_pair(current, values[1], label)
            return low <= number <= high
        if operator == "bars_since_lte":
            number, maximum = _numeric_pair(current, expected, label)
            return number >= 0 and number <= maximum
        raise DslEvaluationError(f"unsupported operator: {operator}")


def _numeric_pair(left: JsonValue, right: JsonValue, label: str) -> tuple[float, float]:
    if (
        not isinstance(left, (int, float))
        or isinstance(left, bool)
        or not isinstance(right, (int, float))
        or isinstance(right, bool)
    ):
        raise DslEvaluationError(f"{label} requires numeric operands")
    return float(left), float(right)
