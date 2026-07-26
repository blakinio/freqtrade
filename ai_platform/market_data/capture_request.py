from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_platform.market_data.common import (
    SCHEMA_VERSION,
    ChannelFamily,
    CompressionPolicy,
    Exchange,
    FrozenJsonObject,
    MarketType,
    _require_text,
    canonical_sha256,
    validate_commit,
)


@dataclass(frozen=True, slots=True)
class CaptureRequest:
    schema_version: int
    source_catalog_version: str
    universe_snapshot_ids: tuple[str, ...]
    exchanges: tuple[Exchange, ...]
    market_types: tuple[MarketType, ...]
    channel_families: tuple[ChannelFamily, ...]
    start_condition: FrozenJsonObject
    end_condition: FrozenJsonObject | None
    raw_segment_policy: FrozenJsonObject
    compression_policy: CompressionPolicy
    clock_policy: FrozenJsonObject
    gap_policy: FrozenJsonObject
    credential_policy: str
    output_root_identity: str
    code_commit: str

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        _require_text(self.source_catalog_version, field="source_catalog_version")
        for field_name, values in (
            ("universe_snapshot_ids", self.universe_snapshot_ids),
            ("exchanges", self.exchanges),
            ("market_types", self.market_types),
            ("channel_families", self.channel_families),
        ):
            if not values or len(set(values)) != len(values):
                raise ValueError(f"{field_name} must be non-empty and unique")
        if self.credential_policy != "public_market_data_only_no_trading_credentials":
            raise ValueError("credential_policy must forbid trading credentials")
        _require_text(self.output_root_identity, field="output_root_identity")
        validate_commit(self.code_commit, field="code_commit")
        for field_name, value in (
            ("start_condition", self.start_condition),
            ("raw_segment_policy", self.raw_segment_policy),
            ("clock_policy", self.clock_policy),
            ("gap_policy", self.gap_policy),
        ):
            if not value.to_dict():
                raise ValueError(f"{field_name} must be non-empty")

    @property
    def request_sha256(self) -> str:
        return canonical_sha256(self.hash_payload())

    def hash_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_catalog_version": self.source_catalog_version,
            "universe_snapshot_ids": list(self.universe_snapshot_ids),
            "exchanges": [item.value for item in self.exchanges],
            "market_types": [item.value for item in self.market_types],
            "channel_families": [item.value for item in self.channel_families],
            "start_condition": self.start_condition.to_dict(),
            "end_condition": (
                None if self.end_condition is None else self.end_condition.to_dict()
            ),
            "raw_segment_policy": self.raw_segment_policy.to_dict(),
            "compression_policy": self.compression_policy.value,
            "clock_policy": self.clock_policy.to_dict(),
            "gap_policy": self.gap_policy.to_dict(),
            "credential_policy": self.credential_policy,
            "output_root_identity": self.output_root_identity,
            "code_commit": self.code_commit,
        }

    def as_json_dict(self) -> dict[str, Any]:
        return {**self.hash_payload(), "request_sha256": self.request_sha256}
