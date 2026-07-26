from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from ai_platform.market_data.capture import (
    CaptureManifest,
    CaptureRequest,
    GapMarker,
    SegmentManifest,
    assert_order_book_reconstructible,
)
from ai_platform.market_data.common import (
    SCHEMA_VERSION,
    AvailabilityTimestampKind,
    ChannelFamily,
    CompressionPolicy,
    EventType,
    Exchange,
    FrozenJsonObject,
    GapReason,
    MarketType,
    OutputImmutabilityState,
    canonical_instrument_id,
    canonical_json_bytes,
    canonical_sha256,
    decimal_text,
    decimal_value,
    raw_payload_sha256,
    refuse_trading_credentials,
    validate_commit,
    validate_sha256,
)
from ai_platform.market_data.events import (
    InstrumentSnapshot,
    RawMarketEventEnvelope,
    UniverseDecision,
    UniverseSnapshot,
)

__all__ = [
    "SCHEMA_VERSION",
    "AvailabilityTimestampKind",
    "CaptureManifest",
    "CaptureRequest",
    "ChannelFamily",
    "CompressionPolicy",
    "EventType",
    "Exchange",
    "FrozenJsonObject",
    "GapMarker",
    "GapReason",
    "InstrumentSnapshot",
    "MarketType",
    "OutputImmutabilityState",
    "RawMarketEventEnvelope",
    "SegmentManifest",
    "UniverseDecision",
    "UniverseSnapshot",
    "assert_order_book_reconstructible",
    "canonical_instrument_id",
    "canonical_json_bytes",
    "canonical_sha256",
    "decimal_text",
    "decimal_value",
    "load_and_validate_contract_json",
    "raw_payload_sha256",
    "refuse_trading_credentials",
    "validate_commit",
    "validate_contract_payload",
    "validate_sha256",
]

CONTRACT_SCHEMA_PATH = Path(__file__).with_name("market-data-foundation-v1.schema.json")


def _contract_schema(contract_name: str, *, schema_path: Path) -> dict[str, Any]:
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON schema: {schema_path}") from exc
    if not isinstance(schema, dict):
        raise ValueError("contract schema must be a JSON object")
    definitions = schema.get("$defs")
    if not isinstance(definitions, dict) or contract_name not in definitions:
        raise KeyError(f"unknown contract schema: {contract_name}")
    definition = definitions[contract_name]
    if not isinstance(definition, dict):
        raise ValueError(f"contract schema {contract_name} must be an object")
    return {
        "$schema": schema.get("$schema"),
        "$defs": definitions,
        "$ref": f"#/$defs/{contract_name}",
    }


def validate_contract_payload(
    contract_name: str,
    payload: Mapping[str, object],
    *,
    schema_path: Path = CONTRACT_SCHEMA_PATH,
) -> None:
    Draft202012Validator(_contract_schema(contract_name, schema_path=schema_path)).validate(
        payload
    )


def load_and_validate_contract_json(
    path: Path,
    *,
    contract_name: str,
    schema_path: Path = CONTRACT_SCHEMA_PATH,
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("contract JSON must contain an object")
    validate_contract_payload(contract_name, payload, schema_path=schema_path)
    return payload
