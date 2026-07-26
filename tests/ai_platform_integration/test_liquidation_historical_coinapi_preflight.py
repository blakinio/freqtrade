from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT_PATH = (
    ROOT
    / "ai_platform"
    / "research"
    / "liquidations"
    / "historical"
    / "liquid20-coinapi-provider-preflight-v1.json"
)
SCHEMA_PATH = PREFLIGHT_PATH.with_name("coinapi-provider-preflight-v1.schema.json")
EXPECTED_SYMBOLS = {
    "BYBIT_PERP_BTC_USDT",
    "BYBIT_PERP_ETH_USDT",
    "BINANCEFTS_PERP_BTC_USDT",
    "BINANCEFTS_PERP_ETH_USDT",
}
HISTORICAL_BUCKET_FIELDS = {
    "time_period_start",
    "time_period_end",
    "time_open",
    "time_close",
    "first",
    "last",
    "min",
    "max",
    "count",
    "sum",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_coinapi_preflight_schema_validates() -> None:
    schema = _load(SCHEMA_PATH)
    preflight = _load(PREFLIGHT_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(preflight)


def test_coinapi_is_not_accepted_as_event_level_replay() -> None:
    preflight = _load(PREFLIGHT_PATH)
    decision = preflight["decision"]
    assert decision["event_level_replay"] == "rejected"
    assert decision["aggregate_feature_source"] == "conditional"
    assert decision["preferred_provider_unchanged"] == "tardis"


def test_target_and_documented_metric_coverage_are_explicit() -> None:
    preflight = _load(PREFLIGHT_PATH)
    assert set(preflight["target"]["symbols"]) == EXPECTED_SYMBOLS
    assert {
        "LIQUIDATION_PRICE",
        "LIQUIDATION_QUANTITY",
        "LIQUIDATION_SIDE",
        "LIQUIDATION_SYMBOL",
        "LIQUIDATION_TIME",
    } <= set(preflight["documented_metrics"]["BYBIT"])
    assert {
        "LIQUIDATION_PRICE",
        "LIQUIDATION_QUANTITY",
        "LIQUIDATION_SYMBOL",
        "LIQUIDATION_ORDER_TRADE_TIME",
    } <= set(preflight["documented_metrics"]["BINANCEFTS"])


def test_historical_contract_fails_event_replay_requirements() -> None:
    historical = _load(PREFLIGHT_PATH)["historical_contract"]
    assert historical["default_period_id"] == "1SEC"
    assert set(historical["response_fields"]) == HISTORICAL_BUCKET_FIELDS
    assert historical["historical_provider_receive_time_available"] is False
    assert historical["event_identifier_available"] is False
    assert historical["separate_metric_series_require_join"] is True
    assert historical["multi_event_bucket_pairing_proven_safe"] is False


def test_runtime_probe_is_non_secret_and_bounded() -> None:
    probe = _load(PREFLIGHT_PATH)["runtime_probe"]
    assert probe["credential"] == "documented-public-sample-placeholder"
    assert probe["http_status"] == 401
    assert probe["response_keys"] == ["error"]
    assert probe["raw_records_emitted"] is False
    serialized = json.dumps(probe, sort_keys=True)
    assert "THIS-IS-SAMPLE-KEY" not in serialized
    assert "X-CoinAPI-Key" not in serialized
