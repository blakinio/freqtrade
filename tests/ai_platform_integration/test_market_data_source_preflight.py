from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / "docs/ai_platform/market_data/source-and-instrument-catalog-preflight-v1.json"
SCHEMA = ROOT / "ai_platform/market_data/source-and-instrument-catalog-preflight-v1.schema.json"
FOUNDATION = ROOT / "ai_platform/market_data/source-catalog-v1.json"

EXPECTED_SOURCES = {
    "binance-spot",
    "binance-usdm",
    "bybit-spot",
    "bybit-linear",
    "okx-spot",
    "okx-swap-futures",
}


def _load(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _canonical_sha256(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def test_preflight_schema_and_self_hash() -> None:
    schema = _load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    payload = _load(PREFLIGHT)
    Draft202012Validator(schema).validate(payload)

    claimed = payload.pop("document_sha256")
    assert isinstance(claimed, str)
    assert claimed == _canonical_sha256(payload)


def test_preflight_is_bound_to_exact_foundation_catalog() -> None:
    payload = _load(PREFLIGHT)
    foundation = _load(FOUNDATION)
    binding = payload["foundation_catalog"]
    assert isinstance(binding, dict)
    assert binding["version"] == foundation["catalog_version"]
    assert binding["sha256"] == foundation["catalog_sha256"]

    sources = payload["sources"]
    assert isinstance(sources, list)
    source_ids = {item["source_id"] for item in sources}
    foundation_ids = {item["source_id"] for item in foundation["sources"]}
    assert source_ids == EXPECTED_SOURCES == foundation_ids


def test_preflight_remains_public_only_and_non_accepting() -> None:
    payload = _load(PREFLIGHT)
    assert payload["boundaries"] == {
        "accounts": False,
        "adapters_included": False,
        "broad_capture": False,
        "credentials": False,
        "live_requests": False,
        "orders": False,
        "public_only": True,
        "raw_records": False,
        "source_acceptance": False,
    }
    sources = payload["sources"]
    assert isinstance(sources, list)
    assert all(item["sample_evidence"] == "official_documentation_example" for item in sources)


def test_source_specific_adapter_gates_fail_closed() -> None:
    payload = _load(PREFLIGHT)
    decision = payload["decision"]
    assert decision["status"] == "partial_pass"
    assert set(decision["ready"]) == EXPECTED_SOURCES - {"binance-usdm"}
    assert decision["blocked"] == ["binance-usdm"]

    sources = {item["source_id"]: item for item in payload["sources"]}
    binance_usdm = sources["binance-usdm"]["mapping"]
    assert binance_usdm["status"] == "blocked"
    assert binance_usdm["contract_value"] is None
    assert binance_usdm["contract_value_unit"] is None
    assert {
        "explicit_contract_value",
        "explicit_contract_value_unit",
    }.issubset(binance_usdm["unresolved"])

    bybit_linear = sources["bybit-linear"]["mapping"]
    assert bybit_linear["contract_value"] == "1"
    assert bybit_linear["contract_value_unit"] == "base_asset"

    okx = sources["okx-swap-futures"]["mapping"]
    assert okx["contract_value"] == "ctVal"
    assert okx["contract_value_unit"] == "ctValCcy"
    assert okx["unresolved"] == ["reject_unrepresentable_non_unit_ctMult"]


def test_next_package_is_bounded() -> None:
    payload = _load(PREFLIGHT)
    assert payload["next_package"] == {
        "broad_capture": False,
        "name": "bounded_instrument_snapshot_adapters_v1",
        "scope": "ready_sources_only_binance_usdm_fail_closed",
    }
