from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    ROOT
    / "ai_platform"
    / "research"
    / "liquidations"
    / "historical"
    / "liquid20-provider-decision-v1.json"
)
SCHEMA_PATH = CONTRACT_PATH.with_name("provider-decision-v1.schema.json")
PROTECTED_HOLDOUT_START = datetime(2026, 8, 1, tzinfo=UTC)
ALLOWED_SEMANTIC_ERAS = {
    "bybit-all-liquidation-exchange-contract-from-2025-02-20",
    "bybit-tardis-all-liquidation-v1-from-2025-02-26",
    "binance-force-order-realtime-before-2021-04-27",
    "binance-force-order-snapshot-1s-from-2021-04-27",
}
REQUIRED_TOP_LEVEL = {
    "$schema",
    "schema_version",
    "decision_package_id",
    "identity_material",
    "identity_sha256",
    "verification",
    "decision_status",
    "preferred_provider",
    "requested_date_range",
    "recommended_import_request",
    "source_decisions",
    "public_sample_evidence",
    "owner_decisions",
    "provider_dependency_risks",
    "source_urls",
}
SECRET_PATTERNS = (
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
    re.compile(r"\bCG-API-KEY\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\b(?:api[_-]?key|token|secret)\s*[:=]\s*[A-Za-z0-9_./+=-]{12,}", re.IGNORECASE),
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"timestamp must use a Z suffix: {value!r}")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.tzinfo != UTC:
        raise ValueError(f"timestamp must be UTC: {value!r}")
    return parsed


def _walk_strings(value: object) -> list[str]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            strings.extend(_walk_strings(child))
    elif isinstance(value, list):
        for child in value:
            strings.extend(_walk_strings(child))
    return strings


def _validate_contract(contract: dict[str, Any]) -> None:
    missing = REQUIRED_TOP_LEVEL - set(contract)
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    if contract["schema_version"] != 1:
        raise ValueError("schema_version must be 1")

    requested = contract["requested_date_range"]
    requested_start = _parse_utc(requested["start_inclusive"])
    requested_end = _parse_utc(requested["end_exclusive"])
    if requested_start >= requested_end:
        raise ValueError("requested date range must be increasing")

    recommended = contract["recommended_import_request"]
    recommended_start = _parse_utc(recommended["start_inclusive"])
    recommended_end = _parse_utc(recommended["end_exclusive"])
    if recommended_start >= recommended_end:
        raise ValueError("recommended date range must be increasing")
    if recommended_end > PROTECTED_HOLDOUT_START:
        raise ValueError("recommended range touches the protected final holdout")
    if not recommended["protected_final_holdout_excluded"]:
        raise ValueError("protected final holdout must remain excluded")

    semantic_eras: list[str] = []
    for dataset in recommended["exchange_datasets"]:
        semantic_eras.extend(dataset["semantic_eras"])
    for source in contract["source_decisions"]:
        semantic_eras.extend(era["id"] for era in source["semantic_eras"])
        for era in source["semantic_eras"]:
            if "start_inclusive" in era:
                _parse_utc(era["start_inclusive"])
            if "end_exclusive" in era:
                _parse_utc(era["end_exclusive"])
    invalid_eras = set(semantic_eras) - ALLOWED_SEMANTIC_ERAS
    if invalid_eras:
        raise ValueError(f"invalid semantic eras: {sorted(invalid_eras)}")

    for value in _walk_strings(contract):
        if any(pattern.search(value) for pattern in SECRET_PATTERNS):
            raise ValueError("secret-shaped value is forbidden")

    canonical_identity = json.dumps(
        contract["identity_material"],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    observed_hash = hashlib.sha256(canonical_identity).hexdigest()
    if observed_hash != contract["identity_sha256"]:
        raise ValueError("identity_sha256 does not match canonical identity material")


def test_provider_decision_contract_validates() -> None:
    contract = _load(CONTRACT_PATH)
    _validate_contract(contract)


def test_schema_validates_contract_and_requires_contract_fields() -> None:
    schema = _load(SCHEMA_PATH)
    contract = _load(CONTRACT_PATH)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert set(schema["required"]) == REQUIRED_TOP_LEVEL
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)


def test_contract_serialization_and_identity_hash_are_deterministic() -> None:
    contract = _load(CONTRACT_PATH)
    first = json.dumps(contract, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    second = json.dumps(_load(CONTRACT_PATH), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    assert first == second

    identity = json.dumps(
        contract["identity_material"],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    assert hashlib.sha256(identity).hexdigest() == contract["identity_sha256"]


def test_missing_required_field_is_rejected() -> None:
    contract = _load(CONTRACT_PATH)
    del contract["preferred_provider"]
    with pytest.raises(ValueError, match="missing required fields"):
        _validate_contract(contract)


def test_invalid_timestamp_is_rejected() -> None:
    contract = _load(CONTRACT_PATH)
    contract["recommended_import_request"]["start_inclusive"] = "2025-02-26"
    with pytest.raises(ValueError, match="Z suffix"):
        _validate_contract(contract)


def test_invalid_semantic_era_is_rejected() -> None:
    contract = _load(CONTRACT_PATH)
    contract["recommended_import_request"]["exchange_datasets"][0]["semantic_eras"] = [
        "fabricated-era"
    ]
    with pytest.raises(ValueError, match="invalid semantic eras"):
        _validate_contract(contract)


def test_secret_shaped_value_is_rejected() -> None:
    contract = copy.deepcopy(_load(CONTRACT_PATH))
    contract["owner_decisions"][0]["decision"] = "Bearer actual-secret-value"
    with pytest.raises(ValueError, match="secret-shaped"):
        _validate_contract(contract)
