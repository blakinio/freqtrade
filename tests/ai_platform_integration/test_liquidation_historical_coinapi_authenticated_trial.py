from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "ai_platform"
    / "research"
    / "liquidations"
    / "historical"
    / "liquid20-coinapi-authenticated-trial-v1.json"
)
SCHEMA_PATH = CONTRACT_PATH.with_name("coinapi-authenticated-trial-v1.schema.json")
EXPECTED_TARGETS = {
    "BYBIT_PERP_BTC_USDT",
    "BYBIT_PERP_ETH_USDT",
    "BINANCEFTS_PERP_BTC_USDT",
    "BINANCEFTS_PERP_ETH_USDT",
}
SECRET_PATTERNS = (
    re.compile(r"X-CoinAPI-Key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\bCOINAPI_KEY\s*[:=]\s*[A-Za-z0-9-]{12,}", re.IGNORECASE),
    re.compile(
        r"\b(?:api[_-]?key|token|secret)\s*[:=]\s*[A-Za-z0-9_./+=-]{12,}",
        re.IGNORECASE,
    ),
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_strings(value: object) -> list[str]:
    values: list[str] = []
    if isinstance(value, str):
        values.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            values.extend(_walk_strings(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(_walk_strings(child))
    return values


def _validate_identity(contract: dict[str, Any]) -> None:
    canonical = json.dumps(
        contract["identity_material"],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    assert hashlib.sha256(canonical).hexdigest() == contract["identity_sha256"]


def test_coinapi_authenticated_trial_contract_validates() -> None:
    schema = _load(SCHEMA_PATH)
    contract = _load(CONTRACT_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(contract)
    _validate_identity(contract)


def test_trial_is_exactly_scoped_and_secret_safe() -> None:
    contract = _load(CONTRACT_PATH)
    assert {target["symbol_id"] for target in contract["targets"]} == EXPECTED_TARGETS
    assert contract["secret_handling"] == {
        "committed_to_git": False,
        "masked_in_logs": True,
        "present_in_actions": True,
        "raw_value_recorded": False,
        "repository_secret_name": "COINAPI_KEY",
    }
    for value in _walk_strings(contract):
        assert not any(pattern.search(value) for pattern in SECRET_PATTERNS)


def test_free_account_blocker_is_frozen() -> None:
    contract = _load(CONTRACT_PATH)
    statuses = contract["coverage_probe"]["per_target_http_statuses"]
    assert set(statuses) == EXPECTED_TARGETS
    assert all(
        status == {"metric_listing": 403, "symbol": 403}
        for status in statuses.values()
    )
    assert contract["coverage_probe"]["request_count"] == 8
    assert contract["coverage_probe"]["history_request_attempted"] is False

    quota = contract["quota_probe"]
    assert quota["http_status"] == 403
    assert quota["quota_key"] == "BA"
    assert quota["quota_name"] == "Insufficient Usage Credits or Subscription"
    assert quota["quota_type"] == "Organization Limit"
    assert quota["quota_value"] == 0
    assert quota["quota_value_current_usage"] == 0
    assert quota["quota_value_unit"] == "$"


def test_decision_cannot_claim_coinapi_replacement() -> None:
    contract = _load(CONTRACT_PATH)
    decision = contract["decision"]
    assert decision["coinapi_free_account_usable_for_liquid20_trial"] is False
    assert decision["coinapi_event_level_replacement_for_tardis"] is False
    assert decision["preferred_event_level_provider_remains"] == "tardis"
    assert decision["paid_probe_recommended_for_event_level_replacement"] is False


def test_secret_shaped_mutation_is_detected() -> None:
    contract = copy.deepcopy(_load(CONTRACT_PATH))
    contract["quota_probe"]["quota_value_adjustable"] = "COINAPI_KEY=actual-secret-value"
    with pytest.raises(AssertionError):
        for value in _walk_strings(contract):
            assert not any(pattern.search(value) for pattern in SECRET_PATTERNS)
