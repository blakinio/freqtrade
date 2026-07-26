from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.historical.contracts import validate_sha256


_SECRET_PATTERN = re.compile(
    r"(?:api[_-]?key|token|secret|authorization)\s*[:=]\s*\S+", re.IGNORECASE
)


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _non_empty(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must be non-empty")
    if _SECRET_PATTERN.search(normalized):
        raise ValueError(f"{field} must not contain secret-shaped content")
    return normalized


@dataclass(frozen=True, slots=True)
class RawFileDescriptor:
    relative_path: str
    sha256: str
    size_bytes: int
    provider_id: str
    provider_exchange: str
    symbol: str
    requested_date: str
    content_encoding: str
    parser_hint: str

    def __post_init__(self) -> None:
        for field_name in (
            "relative_path",
            "provider_id",
            "provider_exchange",
            "symbol",
            "requested_date",
            "content_encoding",
            "parser_hint",
        ):
            _non_empty(str(getattr(self, field_name)), field=field_name)
        if Path(self.relative_path).is_absolute() or ".." in Path(self.relative_path).parts:
            raise ValueError("relative_path must stay within the import root")
        validate_sha256(self.sha256, field="sha256")
        if self.size_bytes <= 0:
            raise ValueError("size_bytes must be > 0")

    def as_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class HistoricalImportManifest:
    schema_version: int
    import_run_id: str
    provider_id: str
    requested_start_ms: int
    requested_end_ms: int
    symbols: tuple[str, ...]
    source_commit_sha: str
    parser_version: str
    decision_contract_sha256: str
    license_classification: str
    license_reference: str
    storage_root: str
    raw_files: tuple[RawFileDescriptor, ...]
    protected_holdout_start_ms: int
    protected_holdout_excluded: bool
    created_at_utc: str

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        for field_name in (
            "import_run_id",
            "provider_id",
            "parser_version",
            "license_classification",
            "license_reference",
            "storage_root",
            "created_at_utc",
        ):
            _non_empty(str(getattr(self, field_name)), field=field_name)
        source_commit = self.source_commit_sha.strip().lower()
        if len(source_commit) != 40 or any(
            char not in "0123456789abcdef" for char in source_commit
        ):
            raise ValueError("source_commit_sha must be a 40-character lowercase Git SHA")
        validate_sha256(self.decision_contract_sha256, field="decision_contract_sha256")
        if self.requested_start_ms <= 0 or self.requested_end_ms <= self.requested_start_ms:
            raise ValueError("requested interval must be positive and non-empty")
        if not self.protected_holdout_excluded:
            raise ValueError("protected_holdout_excluded must be true")
        if self.requested_end_ms > self.protected_holdout_start_ms:
            raise ValueError("requested interval overlaps the protected final holdout")
        if not self.symbols or len(set(self.symbols)) != len(self.symbols):
            raise ValueError("symbols must be non-empty and unique")
        normalized_symbols = {symbol.upper() for symbol in self.symbols}
        for descriptor in self.raw_files:
            if descriptor.provider_id != self.provider_id:
                raise ValueError("raw file provider must match manifest provider")
            if descriptor.symbol.upper() not in normalized_symbols:
                raise ValueError("raw file symbol must be declared in manifest")

    @property
    def identity_material(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "import_run_id": self.import_run_id,
            "provider_id": self.provider_id,
            "requested_start_ms": self.requested_start_ms,
            "requested_end_ms": self.requested_end_ms,
            "symbols": sorted(self.symbols),
            "source_commit_sha": self.source_commit_sha,
            "parser_version": self.parser_version,
            "decision_contract_sha256": self.decision_contract_sha256,
            "license_classification": self.license_classification,
            "license_reference": self.license_reference,
            "storage_root": self.storage_root,
            "raw_files": [
                descriptor.as_json_dict()
                for descriptor in sorted(
                    self.raw_files, key=lambda item: item.relative_path
                )
            ],
            "protected_holdout_start_ms": self.protected_holdout_start_ms,
            "protected_holdout_excluded": self.protected_holdout_excluded,
        }

    @property
    def identity_sha256(self) -> str:
        canonical = json.dumps(
            self.identity_material,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    def as_json_dict(self) -> dict[str, Any]:
        payload = self.identity_material
        payload["created_at_utc"] = self.created_at_utc
        payload["identity_sha256"] = self.identity_sha256
        return payload
