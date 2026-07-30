from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from strategy_engine.domain import ConditionGroup, StrategyDefinition
from strategy_engine.dsl import ConditionOperator, DslReasonCode
from strategy_engine.dsl.validator import StrategyValidationError, StrategyValidator


class _Registry:
    def get(self, feature_id: str) -> SimpleNamespace:
        assert feature_id == "rsi.v1"
        return SimpleNamespace(approved_for_ai=True, timestamp_policy="closed_bar")

    def validate_parameters(self, feature_id: str, params: dict[str, object]) -> dict[str, object]:
        assert feature_id == "rsi.v1"
        return dict(params)


def _payload(*, schema_version: str = "1.0.0", operator: str = "gt") -> dict[str, object]:
    return {
        "schema_version": schema_version,
        "strategy_id": "typed-ast",
        "version": "1",
        "universe": {"symbols": ["BTC/USDT"], "timeframes": ["5m"]},
        "features": [
            {
                "id": "rsi.v1",
                "timeframe": "5m",
                "confirmation": "closed_bar",
            }
        ],
        "entry_long": {
            "all": [
                {"feature": "rsi.v1", "op": operator, "value": 50},
                {
                    "any": [
                        {"event": "liquidation.cluster", "op": "eq", "value": True},
                        {"risk": "drawdown_ok", "op": "eq", "value": True},
                    ]
                },
            ]
        },
        "exit": {"any": [{"risk": "stop", "op": "eq", "value": True}]},
        "risk": {"max_leverage": 1},
        "execution": {"use_closed_bars_only": True},
        "provenance": {"producer": "test", "source_event_id": "source-1"},
    }


def test_v1_payload_is_readable_as_typed_recursive_ast() -> None:
    strategy = StrategyDefinition.model_validate(_payload())

    assert strategy.schema_version == "1.0.0"
    assert isinstance(strategy.entry_long, ConditionGroup)
    assert strategy.entry_long.all is not None
    assert isinstance(strategy.entry_long.all[1], ConditionGroup)
    assert strategy.entry_long.all[0].op == ConditionOperator.GT
    assert strategy.model_dump(mode="json")["entry_long"] == _payload()["entry_long"]


def test_v1_migration_to_v2_is_deterministic() -> None:
    strategy = StrategyDefinition.model_validate(_payload())

    first = strategy.migrate_to_v2()
    second = strategy.migrate_to_v2()

    assert first.schema_version == "2.0.0"
    assert first.canonical_json() == second.canonical_json()
    assert first.canonical_sha256() == second.canonical_sha256()


def test_ast_rejects_arbitrary_code_fields() -> None:
    payload = _payload(schema_version="2.0.0")
    payload["entry_long"] = {"all": [{"python": "__import__('os')"}]}

    with pytest.raises(ValidationError):
        StrategyDefinition.model_validate(payload)


def test_validator_keeps_stable_operator_reason_code() -> None:
    payload = _payload(operator="eval")

    with pytest.raises(StrategyValidationError) as exc_info:
        StrategyValidator(_Registry()).validate(payload)  # type: ignore[arg-type]

    assert exc_info.value.reason_code == DslReasonCode.OPERATOR_NOT_ALLOWED.value


def test_v2_schema_accepts_typed_ast_and_rejects_code() -> None:
    schema_path = Path(__file__).resolve().parents[2] / "schemas/strategy-definition.v2.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    valid = StrategyDefinition.model_validate(_payload(schema_version="2.0.0")).model_dump(
        mode="json"
    )
    validator.validate(valid)

    invalid = json.loads(json.dumps(valid))
    invalid["entry_long"]["all"][0]["python"] = "eval(user_input)"
    assert list(validator.iter_errors(invalid))
