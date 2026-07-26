from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from typing import Any


def utc_ms(value: str) -> int:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.timestamp() * 1000)


@dataclass(frozen=True, slots=True)
class SemanticEra:
    era_id: str
    provider_id: str
    source: str
    start_ms: int
    end_ms: int | None
    native_channel: str
    publication_semantics: str

    def __post_init__(self) -> None:
        for field_name in (
            "era_id",
            "provider_id",
            "source",
            "native_channel",
            "publication_semantics",
        ):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} must be non-empty")
        if self.start_ms <= 0:
            raise ValueError("start_ms must be > 0")
        if self.end_ms is not None and self.end_ms <= self.start_ms:
            raise ValueError("end_ms must be greater than start_ms")

    def contains(self, timestamp_ms: int) -> bool:
        return self.start_ms <= timestamp_ms and (
            self.end_ms is None or timestamp_ms < self.end_ms
        )

    def as_json_dict(self) -> dict[str, Any]:
        return asdict(self)


class SemanticEraRegistry:
    def __init__(self, eras: tuple[SemanticEra, ...]) -> None:
        if not eras:
            raise ValueError("semantic era registry must not be empty")
        self._eras = tuple(
            sorted(eras, key=lambda era: (era.provider_id, era.source, era.start_ms))
        )
        for index, left in enumerate(self._eras):
            for right in self._eras[index + 1 :]:
                if (left.provider_id, left.source) != (right.provider_id, right.source):
                    continue
                left_end = left.end_ms if left.end_ms is not None else 2**63 - 1
                right_end = right.end_ms if right.end_ms is not None else 2**63 - 1
                if left.start_ms < right_end and right.start_ms < left_end:
                    raise ValueError(
                        f"overlapping semantic eras: {left.era_id} and {right.era_id}"
                    )

    @property
    def eras(self) -> tuple[SemanticEra, ...]:
        return self._eras

    def resolve(self, *, provider_id: str, source: str, timestamp_ms: int) -> SemanticEra:
        matches = [
            era
            for era in self._eras
            if era.provider_id == provider_id
            and era.source == source
            and era.contains(timestamp_ms)
        ]
        if len(matches) != 1:
            raise LookupError(
                f"expected one semantic era for {provider_id}/{source} at {timestamp_ms}, "
                f"found {len(matches)}"
            )
        return matches[0]

    def as_json_dict(self) -> dict[str, Any]:
        eras = [era.as_json_dict() for era in self._eras]
        canonical = json.dumps(
            eras, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        )
        return {
            "schema_version": 1,
            "eras": eras,
            "identity_sha256": sha256(canonical.encode("utf-8")).hexdigest(),
        }


DEFAULT_SEMANTIC_ERAS = SemanticEraRegistry(
    (
        SemanticEra(
            era_id="tardis-bybit-all-liquidation-v1",
            provider_id="tardis",
            source="bybit-linear",
            start_ms=utc_ms("2025-02-26T00:00:00Z"),
            end_ms=utc_ms("2026-07-25T00:00:00Z"),
            native_channel="allLiquidation",
            publication_semantics="all liquidation updates; provider local timestamp retained",
        ),
        SemanticEra(
            era_id="tardis-binance-force-order-snapshot-v1",
            provider_id="tardis",
            source="binance-usdm",
            start_ms=utc_ms("2021-04-27T00:00:00Z"),
            end_ms=utc_ms("2026-07-25T00:00:00Z"),
            native_channel="forceOrder",
            publication_semantics="maximum latest liquidation snapshot per symbol per 1000 ms",
        ),
        SemanticEra(
            era_id="first-party-bybit-liquid20-live-v1",
            provider_id="first-party",
            source="bybit-linear",
            start_ms=utc_ms("2026-07-25T00:00:00Z"),
            end_ms=None,
            native_channel="allLiquidation",
            publication_semantics="first-party collector receive timestamp",
        ),
        SemanticEra(
            era_id="first-party-binance-liquid20-live-v1",
            provider_id="first-party",
            source="binance-usdm",
            start_ms=utc_ms("2026-07-25T00:00:00Z"),
            end_ms=None,
            native_channel="forceOrder",
            publication_semantics="first-party collector receive timestamp",
        ),
    )
)
