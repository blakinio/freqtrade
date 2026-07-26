from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from ai_platform.market_data.contracts import (
    ChannelFamily,
    Exchange,
    MarketType,
    canonical_sha256,
    validate_sha256,
)

SOURCE_CATALOG_PATH = Path(__file__).with_name("source-catalog-v1.json")
_ALLOWED_STATUS = "declared_not_implemented_not_validated"


@dataclass(frozen=True, slots=True)
class ChannelDeclaration:
    channel_family: ChannelFamily
    implementation_status: str
    validation_status: str
    source_acceptance: bool

    def __post_init__(self) -> None:
        if self.implementation_status != "not_implemented":
            raise ValueError("foundation channels must remain not_implemented")
        if self.validation_status != "not_validated":
            raise ValueError("foundation channels must remain not_validated")
        if self.source_acceptance:
            raise ValueError("a channel declaration is not source acceptance")

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "channel_family": self.channel_family.value,
            "implementation_status": self.implementation_status,
            "validation_status": self.validation_status,
            "source_acceptance": self.source_acceptance,
        }


def _channel_from_json(payload: dict[str, Any]) -> ChannelDeclaration:
    source_acceptance = payload["source_acceptance"]
    if not isinstance(source_acceptance, bool):
        raise TypeError("source_acceptance must be a boolean")
    return ChannelDeclaration(
        channel_family=ChannelFamily(str(payload["channel_family"])),
        implementation_status=str(payload["implementation_status"]),
        validation_status=str(payload["validation_status"]),
        source_acceptance=source_acceptance,
    )


@dataclass(frozen=True, slots=True)
class SourceDeclaration:
    source_id: str
    exchange: Exchange
    market_types: tuple[MarketType, ...]
    product_family: str
    channels: tuple[ChannelDeclaration, ...]
    declaration_status: str
    official_documentation_verification: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.product_family.strip():
            raise ValueError("source_id and product_family must be non-empty")
        if not self.market_types or len(set(self.market_types)) != len(self.market_types):
            raise ValueError("market_types must be non-empty and unique")
        if not self.channels:
            raise ValueError("channels must be non-empty")
        families = [item.channel_family for item in self.channels]
        if len(set(families)) != len(families):
            raise ValueError("channel declarations must be unique")
        if self.declaration_status != _ALLOWED_STATUS:
            raise ValueError("source declaration status is not fail-closed")
        verification = self.official_documentation_verification
        if verification != {
            "status": "not_performed_foundation_no_precise_claims",
            "verified_at": None,
            "sources": [],
        }:
            raise ValueError("foundation must not claim unperformed source verification")
        forbidden = {"orders", "account", "balances", "positions", "private_stream"}
        if forbidden.intersection(family.value for family in families):
            raise ValueError("account and trading channels are forbidden")

    def as_json_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "exchange": self.exchange.value,
            "market_types": [item.value for item in self.market_types],
            "product_family": self.product_family,
            "channels": [item.as_json_dict() for item in self.channels],
            "declaration_status": self.declaration_status,
            "official_documentation_verification": self.official_documentation_verification,
        }


@dataclass(frozen=True, slots=True)
class SourceCatalog:
    schema_version: int
    catalog_version: str
    classification: str
    sources: tuple[SourceDeclaration, ...]
    global_boundaries: dict[str, Any]
    catalog_sha256: str

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.catalog_version != "market-data-source-catalog-v1":
            raise ValueError("unsupported source catalog version")
        if self.classification != "declarations_only_not_source_acceptance":
            raise ValueError("catalog classification must remain declarations-only")
        source_ids = [item.source_id for item in self.sources]
        if len(self.sources) != 6 or len(set(source_ids)) != len(source_ids):
            raise ValueError("catalog must contain exactly six unique initial source declarations")
        expected_sources = {
            "binance-spot",
            "binance-usdm",
            "bybit-spot",
            "bybit-linear",
            "okx-spot",
            "okx-swap-futures",
        }
        if set(source_ids) != expected_sources:
            raise ValueError("catalog source set does not match the bounded initial venue set")
        required_boundaries = {
            "public_market_data_only": True,
            "trading_credentials_allowed": False,
            "account_endpoints_allowed": False,
            "order_endpoints_allowed": False,
            "source_acceptance_implied": False,
            "live_capture_implemented": False,
        }
        if self.global_boundaries != required_boundaries:
            raise ValueError("catalog global boundaries do not match foundation invariants")
        validate_sha256(self.catalog_sha256, field="catalog_sha256")
        if self.catalog_sha256 != canonical_sha256(self.hash_payload()):
            raise ValueError("catalog_sha256 does not match source catalog content")

    @classmethod
    def from_json_dict(cls, payload: dict[str, Any]) -> Self:
        try:
            sources = tuple(
                SourceDeclaration(
                    source_id=str(item["source_id"]),
                    exchange=Exchange(str(item["exchange"])),
                    market_types=tuple(MarketType(str(value)) for value in item["market_types"]),
                    product_family=str(item["product_family"]),
                    channels=tuple(
                        _channel_from_json(channel) for channel in item["channels"]
                    ),
                    declaration_status=str(item["declaration_status"]),
                    official_documentation_verification=dict(
                        item["official_documentation_verification"]
                    ),
                )
                for item in payload["sources"]
            )
            return cls(
                schema_version=int(payload["schema_version"]),
                catalog_version=str(payload["catalog_version"]),
                classification=str(payload["classification"]),
                sources=sources,
                global_boundaries=dict(payload["global_boundaries"]),
                catalog_sha256=str(payload["catalog_sha256"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid market-data source catalog") from exc

    def hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "catalog_version": self.catalog_version,
            "classification": self.classification,
            "sources": [item.as_json_dict() for item in self.sources],
            "global_boundaries": self.global_boundaries,
        }

    def as_json_dict(self) -> dict[str, Any]:
        return {**self.hash_payload(), "catalog_sha256": self.catalog_sha256}


def load_source_catalog(path: Path = SOURCE_CATALOG_PATH) -> SourceCatalog:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed source catalog JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("source catalog must contain a JSON object")
    return SourceCatalog.from_json_dict(payload)
