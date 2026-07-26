from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from ai_platform.market_data.contracts import validate_contract_payload
from ai_platform.market_data.source_catalog import SourceCatalog, load_source_catalog

CATALOG_PATH = Path("ai_platform/market_data/source-catalog-v1.json")


def test_source_catalog_is_bounded_declarative_and_schema_valid() -> None:
    catalog = load_source_catalog()
    assert catalog.catalog_version == "market-data-source-catalog-v1"
    assert catalog.classification == "declarations_only_not_source_acceptance"
    assert {item.source_id for item in catalog.sources} == {
        "binance-spot",
        "binance-usdm",
        "bybit-spot",
        "bybit-linear",
        "okx-spot",
        "okx-swap-futures",
    }
    for source in catalog.sources:
        assert source.declaration_status == "declared_not_implemented_not_validated"
        assert source.official_documentation_verification == {
            "status": "not_performed_foundation_no_precise_claims",
            "verified_at": None,
            "sources": [],
        }
        assert all(
            channel.implementation_status == "not_implemented"
            for channel in source.channels
        )
        assert all(
            channel.validation_status == "not_validated" for channel in source.channels
        )
        assert all(not channel.source_acceptance for channel in source.channels)
    validate_contract_payload("SourceCatalog", catalog.as_json_dict())


def test_source_catalog_self_hash_and_tamper_detection() -> None:
    catalog = load_source_catalog()
    assert catalog.catalog_sha256 == load_source_catalog().catalog_sha256
    with pytest.raises(ValueError, match="catalog_sha256"):
        replace(catalog, catalog_sha256="0" * 64)
    with pytest.raises(ValueError, match="catalog_sha256"):
        replace(
            catalog,
            classification="declarations_only_not_source_acceptance",
            sources=tuple(reversed(catalog.sources)),
        )


def test_source_catalog_rejects_malformed_json(tmp_path: Path) -> None:
    malformed = tmp_path / "source-catalog.json"
    malformed.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed source catalog JSON"):
        load_source_catalog(malformed)

    payload = json.loads(CATALOG_PATH.read_text())
    payload["global_boundaries"]["trading_credentials_allowed"] = True
    invalid = tmp_path / "invalid-source-catalog.json"
    invalid.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="global boundaries"):
        load_source_catalog(invalid)


def test_source_catalog_requires_boolean_source_acceptance() -> None:
    payload = json.loads(CATALOG_PATH.read_text())
    payload["sources"][0]["channels"][0]["source_acceptance"] = "false"
    with pytest.raises(ValueError, match="invalid market-data source catalog"):
        SourceCatalog.from_json_dict(payload)
