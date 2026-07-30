from __future__ import annotations

from collections.abc import Iterator, Mapping
from enum import StrEnum
from typing import Annotated, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    SerializerFunctionWrapHandler,
    model_serializer,
)

NonEmptyStr = Annotated[str, Field(min_length=1)]


class DslReasonCode(StrEnum):
    DSL_SCHEMA_INVALID = "DSL_SCHEMA_INVALID"
    CLOSED_BAR_POLICY_REQUIRED = "CLOSED_BAR_POLICY_REQUIRED"
    RISK_POLICY_INVALID = "RISK_POLICY_INVALID"
    DCA_REQUIRES_MAX_EXPOSURE = "DCA_REQUIRES_MAX_EXPOSURE"
    DUPLICATE_FEATURE = "DUPLICATE_FEATURE"
    FEATURE_REGISTRY_REJECTED = "FEATURE_REGISTRY_REJECTED"
    FEATURE_NOT_APPROVED_FOR_AI = "FEATURE_NOT_APPROVED_FOR_AI"
    UNDECLARED_TIMEFRAME = "UNDECLARED_TIMEFRAME"
    HTF_POLICY_MISMATCH = "HTF_POLICY_MISMATCH"
    LEGACY_MODE_FORBIDDEN = "LEGACY_MODE_FORBIDDEN"
    SEARCH_SPACE_REJECTED = "SEARCH_SPACE_REJECTED"
    CONDITION_GROUP_MISSING = "CONDITION_GROUP_MISSING"
    CONDITION_GROUP_INVALID = "CONDITION_GROUP_INVALID"
    CONDITION_GROUP_EMPTY = "CONDITION_GROUP_EMPTY"
    CONDITION_INVALID = "CONDITION_INVALID"
    FEATURE_NOT_DECLARED = "FEATURE_NOT_DECLARED"
    OPERATOR_NOT_ALLOWED = "OPERATOR_NOT_ALLOWED"


class ConditionOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"
    IN_RANGE = "in_range"
    BARS_SINCE_LTE = "bars_since_lte"


class DslAstModel(BaseModel, Mapping[str, JsonValue]):
    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_serializer(mode="wrap")
    def serialize_without_unset_nulls(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        payload = handler(self)
        return {
            key: value
            for key, value in payload.items()
            if value is not None or key in self.model_fields_set
        }

    def _as_mapping(self) -> dict[str, JsonValue]:
        return cast(dict[str, JsonValue], self.model_dump(mode="json"))

    def __getitem__(self, key: str) -> JsonValue:
        return self._as_mapping()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._as_mapping())

    def __len__(self) -> int:
        return len(self._as_mapping())


class Condition(DslAstModel):
    feature: NonEmptyStr | None = None
    event: NonEmptyStr | None = None
    risk: NonEmptyStr | None = None
    op: ConditionOperator | None = None
    value: JsonValue = None
    parameter: NonEmptyStr | None = None
    direction: NonEmptyStr | None = None


class ConditionGroup(DslAstModel):
    all: tuple["ConditionNode", ...] | None = None
    any: tuple["ConditionNode", ...] | None = None
    none: tuple["ConditionNode", ...] | None = None

    def branches(self) -> tuple[tuple[str, tuple["ConditionNode", ...]], ...]:
        return tuple(
            (name, branch)
            for name in ("all", "any", "none")
            if (branch := getattr(self, name)) is not None
        )


ConditionNode = Condition | ConditionGroup
ConditionGroup.model_rebuild()

__all__ = [
    "Condition",
    "ConditionGroup",
    "ConditionNode",
    "ConditionOperator",
    "DslAstModel",
    "DslReasonCode",
]
