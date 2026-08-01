from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import shutil
import tempfile
import zipfile
from bisect import bisect_left
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ai_platform.research.liquidations.historical.manifests import sha256_file
from ai_platform.wickhunter.canonical import canonical_json, canonical_sha256
from ai_platform.wickhunter.production_dataset_materialization import (
    DATASET_DIR_NAME,
    verify_production_materialization,
)


REQUEST_SCHEMA_VERSION = "wickhunter-replay-price-path-request-v1"
MANIFEST_SCHEMA_VERSION = "wickhunter-replay-price-path-manifest-v1"
TRADE_SCHEMA_VERSION = "wickhunter-replay-aggregate-trade-v1"
REPORT_SCHEMA_VERSION = "wickhunter-replay-price-path-report-v1"
SOURCE_ID = "binance-usdm"
PROVIDER_ID = "binance-public-data"
DATA_KIND = "aggTrades"
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "verification-report.json"
REQUEST_NAME = "request.json"
CHECKSUM_INDEX_NAME = "artifact-sha256.txt"
TRADES_DIR_NAME = "trades"
MAX_CHECKSUM_BYTES = 4096
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
MAX_MEMBER_BYTES = 8 * 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200
MAX_ROWS_PER_SYMBOL = 25_000_000
_CHECKSUM_PATTERN = re.compile(r"^([0-9a-fA-F]{64})\s+[* ]?([^\s]+)$")
_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{3,32}$")
_CANONICAL_HEADER = (
    "agg_trade_id",
    "price",
    "quantity",
    "first_trade_id",
    "last_trade_id",
    "timestamp",
    "is_buyer_maker",
)
_VERBOSE_HEADER = (
    "aggregate_tradeid",
    "price",
    "quantity",
    "first_tradeid",
    "last_tradeid",
    "timestamp",
    "was_the_buyer_the_maker",
)


class ReplayPricePathError(RuntimeError):
    """Raised when exact replay price-path evidence cannot be accepted safely."""


def _decimal(value: object, *, field: str, positive: bool = False) -> Decimal:
    if isinstance(value, bool):
        raise ReplayPricePathError(f"{field} must be decimal-compatible")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ReplayPricePathError(f"{field} must be decimal-compatible") from exc
    if not parsed.is_finite() or (positive and parsed <= 0):
        raise ReplayPricePathError(f"{field} has an invalid value")
    return parsed


def _integer(value: object, *, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ReplayPricePathError(f"{field} must be an integer")
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ReplayPricePathError(f"{field} must be an integer") from exc
    if parsed < minimum:
        raise ReplayPricePathError(f"{field} must be >= {minimum}")
    return parsed


def _text(value: object, *, field: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ReplayPricePathError(f"{field} must be non-empty")
    return normalized


def _sha256(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise ReplayPricePathError(f"{field} must be a lowercase SHA-256 digest")
    return normalized


def _git_sha(value: object, *, field: str) -> str:
    normalized = _text(value, field=field).lower()
    if len(normalized) != 40 or any(char not in "0123456789abcdef" for char in normalized):
        raise ReplayPricePathError(f"{field} must be a lowercase 40-character Git SHA")
    return normalized


def _boolean(value: object, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise ReplayPricePathError(f"{field} must be a boolean")
    return value


def _bool_text(value: object, *, field: str) -> bool:
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ReplayPricePathError(f"{field} must be true or false")


def _canonical_bytes(value: object) -> bytes:
    return canonical_json(value).encode("utf-8")


def _write_new(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ReplayPricePathError(f"refusing to overwrite {path}")
    with path.open("xb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_json(path: Path, payload: object) -> None:
    _write_new(path, _canonical_bytes(payload) + b"\n")


def _write_jsonl(path: Path, payloads: Iterable[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ReplayPricePathError(f"refusing to overwrite {path}")
    with path.open("xb") as handle:
        for payload in payloads:
            handle.write(_canonical_bytes(payload) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())


def _load_json(path: Path, *, field: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ReplayPricePathError(f"{field} must be a regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReplayPricePathError(f"unable to read {field}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReplayPricePathError(f"{field} must contain an object")
    return payload


def _safe_member(root: Path, logical_name: str) -> Path:
    relative = Path(logical_name)
    if (
        not logical_name
        or relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ReplayPricePathError("artifact path must remain relative")
    resolved_root = root.resolve(strict=True)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ReplayPricePathError("artifact path traverses a symlink")
    try:
        current.resolve(strict=True).relative_to(resolved_root)
    except (FileNotFoundError, ValueError) as exc:
        raise ReplayPricePathError("artifact path escapes input root or is missing") from exc
    if not current.is_file():
        raise ReplayPricePathError("artifact path is not a regular file")
    return current


def _normalize_header(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized.replace("aggregate_trade_id", "agg_trade_id")


def _is_header(row: Sequence[str]) -> bool:
    normalized = tuple(_normalize_header(value) for value in row)
    if normalized == _CANONICAL_HEADER:
        return True
    verbose = tuple(value.replace("_", "") for value in normalized)
    expected_verbose = tuple(value.replace("_", "") for value in _VERBOSE_HEADER)
    return verbose == expected_verbose


@dataclass(frozen=True, slots=True)
class ReplayArchiveInput:
    symbol: str
    archive_relative_path: str
    checksum_relative_path: str

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if self.symbol != symbol or not _SYMBOL_PATTERN.fullmatch(symbol):
            raise ReplayPricePathError("archive symbol must be uppercase and valid")
        for value, field in (
            (self.archive_relative_path, "archive_relative_path"),
            (self.checksum_relative_path, "checksum_relative_path"),
        ):
            relative = Path(value)
            if not value or relative.is_absolute() or ".." in relative.parts:
                raise ReplayPricePathError(f"{field} must remain relative")
        expected_archive = f"{symbol}-aggTrades-"
        if not Path(self.archive_relative_path).name.startswith(expected_archive):
            raise ReplayPricePathError("archive filename does not match symbol and data kind")
        if Path(self.checksum_relative_path).name != (
            Path(self.archive_relative_path).name + ".CHECKSUM"
        ):
            raise ReplayPricePathError("checksum filename must match archive filename")


@dataclass(frozen=True, slots=True)
class ReplayPricePathRequest:
    schema_version: str
    package_id: str
    dataset_id: str
    dataset_manifest_sha256: str
    market_manifest_sha256: str
    source_commit_sha: str
    requested_date: str
    requested_start_ms: int
    requested_end_ms: int
    label_horizon_ms: int
    protected_holdout_start_ms: int
    symbols: tuple[str, ...]
    archives: tuple[ReplayArchiveInput, ...]
    public_only: bool
    protected_holdout_excluded: bool
    replay_authorized: bool
    model_execution_authorized: bool
    performance_research_authorized: bool
    execution_enabled: bool
    live_capital_authorized: bool
    trading_credentials_present: bool
    orders_submitted: int

    def __post_init__(self) -> None:  # noqa: C901
        if self.schema_version != REQUEST_SCHEMA_VERSION:
            raise ReplayPricePathError(f"schema_version must be {REQUEST_SCHEMA_VERSION}")
        for value, field in (
            (self.package_id, "package_id"),
            (self.dataset_id, "dataset_id"),
        ):
            _text(value, field=field)
        _sha256(self.dataset_manifest_sha256, field="dataset_manifest_sha256")
        _sha256(self.market_manifest_sha256, field="market_manifest_sha256")
        _git_sha(self.source_commit_sha, field="source_commit_sha")
        try:
            requested_day = date.fromisoformat(self.requested_date)
        except ValueError as exc:
            raise ReplayPricePathError("requested_date must be ISO YYYY-MM-DD") from exc
        day_start = int(datetime.combine(requested_day, time.min, tzinfo=UTC).timestamp() * 1000)
        day_end = day_start + 86_400_000
        if self.requested_start_ms < day_start or self.requested_end_ms > day_end:
            raise ReplayPricePathError("requested interval must remain within requested UTC date")
        if self.requested_start_ms <= 0 or self.requested_end_ms <= self.requested_start_ms:
            raise ReplayPricePathError("requested interval must be positive and non-empty")
        if self.label_horizon_ms <= 0:
            raise ReplayPricePathError("label_horizon_ms must be > 0")
        if self.requested_end_ms >= self.protected_holdout_start_ms:
            raise ReplayPricePathError("requested interval overlaps protected holdout")
        if not self.protected_holdout_excluded:
            raise ReplayPricePathError("protected_holdout_excluded must be true")
        normalized_symbols = tuple(sorted({symbol.strip().upper() for symbol in self.symbols}))
        if not normalized_symbols or normalized_symbols != self.symbols:
            raise ReplayPricePathError("symbols must be non-empty, unique and sorted uppercase")
        if any(not _SYMBOL_PATTERN.fullmatch(symbol) for symbol in self.symbols):
            raise ReplayPricePathError("request contains an invalid symbol")
        archive_symbols = tuple(item.symbol.strip().upper() for item in self.archives)
        if archive_symbols != self.symbols:
            raise ReplayPricePathError("archives must provide exactly one sorted file per symbol")
        for item in self.archives:
            expected_name = f"{item.symbol.upper()}-aggTrades-{self.requested_date}.zip"
            if Path(item.archive_relative_path).name != expected_name:
                raise ReplayPricePathError("archive filename does not match requested date")
        if not self.public_only:
            raise ReplayPricePathError("replay path source must remain public-only")
        authority_values = (
            self.replay_authorized,
            self.model_execution_authorized,
            self.performance_research_authorized,
            self.execution_enabled,
            self.live_capital_authorized,
            self.trading_credentials_present,
        )
        if any(authority_values) or self.orders_submitted != 0:
            raise ReplayPricePathError("request contains unsafe authority")

    @property
    def request_sha256(self) -> str:
        return canonical_sha256(self)


@dataclass(frozen=True, slots=True)
class ReplayAggregateTrade:
    schema_version: str
    source: str
    symbol: str
    aggregate_trade_id: int
    price: Decimal
    quantity: Decimal
    first_trade_id: int
    last_trade_id: int
    occurred_at_ms: int
    buyer_is_maker: bool
    archive_sha256: str
    raw_row_number: int

    def __post_init__(self) -> None:
        if self.schema_version != TRADE_SCHEMA_VERSION:
            raise ReplayPricePathError(f"trade schema must be {TRADE_SCHEMA_VERSION}")
        if self.source != SOURCE_ID:
            raise ReplayPricePathError(f"trade source must be {SOURCE_ID}")
        if not _SYMBOL_PATTERN.fullmatch(self.symbol):
            raise ReplayPricePathError("trade symbol is invalid")
        for value, field in (
            (self.aggregate_trade_id, "aggregate_trade_id"),
            (self.first_trade_id, "first_trade_id"),
            (self.last_trade_id, "last_trade_id"),
            (self.occurred_at_ms, "occurred_at_ms"),
            (self.raw_row_number, "raw_row_number"),
        ):
            minimum = 1 if field in {"occurred_at_ms", "raw_row_number"} else 0
            if value < minimum:
                raise ReplayPricePathError(f"{field} must be >= {minimum}")
        if self.first_trade_id > self.last_trade_id:
            raise ReplayPricePathError("first_trade_id must not exceed last_trade_id")
        _decimal(self.price, field="price", positive=True)
        _decimal(self.quantity, field="quantity", positive=True)
        _sha256(self.archive_sha256, field="archive_sha256")

    @property
    def trade_sha256(self) -> str:
        return canonical_sha256(self)

    def as_json_dict(self) -> dict[str, object]:
        payload = json.loads(canonical_json(self))
        payload["trade_sha256"] = self.trade_sha256
        return payload


@dataclass(frozen=True, slots=True)
class ArchiveEvidence:
    symbol: str
    archive_relative_path: str
    archive_sha256: str
    archive_size_bytes: int
    checksum_relative_path: str
    checksum_file_sha256: str
    checksum_claimed_sha256: str
    csv_member_name: str
    csv_member_size_bytes: int
    raw_row_count: int
    selected_row_count: int
    first_raw_timestamp_ms: int
    last_raw_timestamp_ms: int
    first_selected_timestamp_ms: int
    last_selected_timestamp_ms: int


@dataclass(frozen=True, slots=True)
class TradePartition:
    symbol: str
    relative_path: str
    row_count: int
    first_timestamp_ms: int
    last_timestamp_ms: int
    first_aggregate_trade_id: int
    last_aggregate_trade_id: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ReplayPricePathManifest:
    schema_version: str
    package_id: str
    request_sha256: str
    dataset_id: str
    dataset_manifest_sha256: str
    market_manifest_sha256: str
    source_commit_sha: str
    provider_id: str
    source: str
    data_kind: str
    requested_date: str
    requested_start_ms: int
    requested_end_ms: int
    label_horizon_ms: int
    protected_holdout_start_ms: int
    symbols: tuple[str, ...]
    decision_count: int
    archive_evidence: tuple[ArchiveEvidence, ...]
    partitions: tuple[TradePartition, ...]
    total_trade_rows: int
    maximum_entry_delay_ms: int
    public_only: bool
    protected_holdout_accessed: bool
    immutable_inputs_mutated: bool
    replay_authorized: bool
    model_execution_authorized: bool
    performance_research_authorized: bool
    execution_enabled: bool
    live_capital_authorized: bool
    trading_credentials_present: bool
    orders_submitted: int

    def __post_init__(self) -> None:
        if self.schema_version != MANIFEST_SCHEMA_VERSION:
            raise ReplayPricePathError(f"manifest schema must be {MANIFEST_SCHEMA_VERSION}")
        if self.provider_id != PROVIDER_ID or self.source != SOURCE_ID:
            raise ReplayPricePathError("manifest provider/source identity mismatch")
        if self.data_kind != DATA_KIND:
            raise ReplayPricePathError("manifest data kind mismatch")
        _sha256(self.request_sha256, field="request_sha256")
        _sha256(self.dataset_manifest_sha256, field="dataset_manifest_sha256")
        _sha256(self.market_manifest_sha256, field="market_manifest_sha256")
        _git_sha(self.source_commit_sha, field="source_commit_sha")
        if self.decision_count <= 0 or self.total_trade_rows <= 0:
            raise ReplayPricePathError("manifest requires decisions and trade rows")
        if self.maximum_entry_delay_ms < 0:
            raise ReplayPricePathError("maximum_entry_delay_ms must be >= 0")
        if tuple(item.symbol for item in self.archive_evidence) != self.symbols:
            raise ReplayPricePathError("archive evidence symbol coverage mismatch")
        if tuple(item.symbol for item in self.partitions) != self.symbols:
            raise ReplayPricePathError("partition symbol coverage mismatch")
        if sum(item.row_count for item in self.partitions) != self.total_trade_rows:
            raise ReplayPricePathError("partition row counts do not match total")
        if not self.public_only:
            raise ReplayPricePathError("manifest must remain public-only")
        if (
            self.protected_holdout_accessed
            or self.immutable_inputs_mutated
            or self.replay_authorized
            or self.model_execution_authorized
            or self.performance_research_authorized
            or self.execution_enabled
            or self.live_capital_authorized
            or self.trading_credentials_present
            or self.orders_submitted != 0
        ):
            raise ReplayPricePathError("manifest contains unsafe authority")

    @property
    def manifest_sha256(self) -> str:
        return canonical_sha256(self)

    def as_json_dict(self) -> dict[str, object]:
        payload = json.loads(canonical_json(self))
        payload["manifest_sha256"] = self.manifest_sha256
        return payload


def request_from_json(payload: Mapping[str, object]) -> ReplayPricePathRequest:
    raw_archives = payload.get("archives")
    raw_symbols = payload.get("symbols")
    if not isinstance(raw_archives, list) or not isinstance(raw_symbols, list):
        raise ReplayPricePathError("request archives and symbols must be lists")
    if payload.get("public_only") is not True:
        raise ReplayPricePathError("request public_only must be true")
    if payload.get("protected_holdout_excluded") is not True:
        raise ReplayPricePathError("request protected_holdout_excluded must be true")
    for key in (
        "replay_authorized",
        "model_execution_authorized",
        "performance_research_authorized",
        "execution_enabled",
        "live_capital_authorized",
        "trading_credentials_present",
    ):
        if payload.get(key) is not False:
            raise ReplayPricePathError(f"request {key} must be false")
    if payload.get("orders_submitted") != 0:
        raise ReplayPricePathError("request orders_submitted must be zero")
    try:
        return ReplayPricePathRequest(
            schema_version=str(payload["schema_version"]),
            package_id=str(payload["package_id"]),
            dataset_id=str(payload["dataset_id"]),
            dataset_manifest_sha256=str(payload["dataset_manifest_sha256"]),
            market_manifest_sha256=str(payload["market_manifest_sha256"]),
            source_commit_sha=str(payload["source_commit_sha"]),
            requested_date=str(payload["requested_date"]),
            requested_start_ms=_integer(
                payload["requested_start_ms"], field="requested_start_ms", minimum=1
            ),
            requested_end_ms=_integer(
                payload["requested_end_ms"], field="requested_end_ms", minimum=1
            ),
            label_horizon_ms=_integer(
                payload["label_horizon_ms"], field="label_horizon_ms", minimum=1
            ),
            protected_holdout_start_ms=_integer(
                payload["protected_holdout_start_ms"],
                field="protected_holdout_start_ms",
                minimum=1,
            ),
            symbols=tuple(str(item) for item in raw_symbols),
            archives=tuple(
                ReplayArchiveInput(
                    symbol=str(item["symbol"]),
                    archive_relative_path=str(item["archive_relative_path"]),
                    checksum_relative_path=str(item["checksum_relative_path"]),
                )
                for item in raw_archives
                if isinstance(item, dict)
            ),
            public_only=payload.get("public_only") is True,
            protected_holdout_excluded=payload.get("protected_holdout_excluded") is True,
            replay_authorized=payload.get("replay_authorized") is True,
            model_execution_authorized=payload.get("model_execution_authorized") is True,
            performance_research_authorized=(
                payload.get("performance_research_authorized") is True
            ),
            execution_enabled=payload.get("execution_enabled") is True,
            live_capital_authorized=payload.get("live_capital_authorized") is True,
            trading_credentials_present=payload.get("trading_credentials_present") is True,
            orders_submitted=_integer(
                payload.get("orders_submitted", -1),
                field="orders_submitted",
                minimum=0,
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ReplayPricePathError):
            raise
        raise ReplayPricePathError("invalid replay price-path request") from exc


def load_request(path: Path) -> ReplayPricePathRequest:
    return request_from_json(_load_json(path, field="replay price-path request"))


def _read_checksum(path: Path, archive_name: str) -> tuple[str, str]:
    if path.stat().st_size > MAX_CHECKSUM_BYTES:
        raise ReplayPricePathError("checksum file exceeds bounded size")
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    except (OSError, UnicodeDecodeError) as exc:
        raise ReplayPricePathError("unable to read checksum file") from exc
    non_empty = [line for line in lines if line]
    if len(non_empty) != 1:
        raise ReplayPricePathError("checksum file must contain exactly one non-empty line")
    match = _CHECKSUM_PATTERN.fullmatch(non_empty[0])
    if match is None:
        raise ReplayPricePathError("checksum line has an invalid format")
    digest = match.group(1).lower()
    filename = Path(match.group(2)).name
    if filename != archive_name or match.group(2) != archive_name:
        raise ReplayPricePathError("checksum filename does not match archive")
    return _sha256(digest, field="checksum digest"), sha256_file(path)


def _parse_archive(  # noqa: C901
    *,
    input_root: Path,
    descriptor: ReplayArchiveInput,
    request: ReplayPricePathRequest,
) -> tuple[list[ReplayAggregateTrade], ArchiveEvidence]:
    archive_path = _safe_member(input_root, descriptor.archive_relative_path)
    checksum_path = _safe_member(input_root, descriptor.checksum_relative_path)
    archive_size = archive_path.stat().st_size
    if archive_size <= 0 or archive_size > MAX_ARCHIVE_BYTES:
        raise ReplayPricePathError("archive size is outside the bounded range")
    claimed_digest, checksum_file_sha256 = _read_checksum(checksum_path, archive_path.name)
    actual_digest = sha256_file(archive_path)
    if actual_digest != claimed_digest:
        raise ReplayPricePathError("archive SHA-256 does not match CHECKSUM")

    expected_member = archive_path.name.removesuffix(".zip") + ".csv"
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = [item for item in archive.infolist() if not item.is_dir()]
            if len(members) != 1:
                raise ReplayPricePathError("archive must contain exactly one CSV member")
            member = members[0]
            member_path = Path(member.filename)
            if (
                member_path.is_absolute()
                or any(part in {"", ".", ".."} for part in member_path.parts)
                or member_path.name != expected_member
                or member.flag_bits & 0x1
            ):
                raise ReplayPricePathError("archive member identity or encryption is invalid")
            if member.file_size <= 0 or member.file_size > MAX_MEMBER_BYTES:
                raise ReplayPricePathError("CSV member size is outside the bounded range")
            if member.compress_size <= 0:
                raise ReplayPricePathError("CSV member compressed size is invalid")
            if member.file_size > member.compress_size * MAX_COMPRESSION_RATIO:
                raise ReplayPricePathError("archive compression ratio exceeds safety bound")

            selected: list[ReplayAggregateTrade] = []
            raw_count = 0
            first_raw_timestamp: int | None = None
            last_raw_timestamp: int | None = None
            previous_order: tuple[int, int] | None = None
            with archive.open(member, "r") as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                reader = csv.reader(text)
                for row_number, row in enumerate(reader, 1):
                    if row_number > MAX_ROWS_PER_SYMBOL:
                        raise ReplayPricePathError("archive row count exceeds safety bound")
                    if row_number == 1 and _is_header(row):
                        continue
                    if len(row) != 7:
                        raise ReplayPricePathError(
                            f"aggregate trade row {row_number} must have seven columns"
                        )
                    aggregate_id = _integer(row[0], field="aggregate_trade_id", minimum=0)
                    price = _decimal(row[1], field="price", positive=True)
                    quantity = _decimal(row[2], field="quantity", positive=True)
                    first_trade_id = _integer(row[3], field="first_trade_id", minimum=0)
                    last_trade_id = _integer(row[4], field="last_trade_id", minimum=0)
                    timestamp_ms = _integer(row[5], field="timestamp", minimum=1)
                    buyer_is_maker = _bool_text(row[6], field="is_buyer_maker")
                    order = (timestamp_ms, aggregate_id)
                    if previous_order is not None and order <= previous_order:
                        raise ReplayPricePathError(
                            "aggregate trades must be strictly ordered by timestamp and ID"
                        )
                    previous_order = order
                    if first_trade_id > last_trade_id:
                        raise ReplayPricePathError("aggregate trade first ID exceeds last ID")
                    raw_count += 1
                    first_raw_timestamp = (
                        timestamp_ms if first_raw_timestamp is None else first_raw_timestamp
                    )
                    last_raw_timestamp = timestamp_ms
                    if request.requested_start_ms <= timestamp_ms <= request.requested_end_ms:
                        selected.append(
                            ReplayAggregateTrade(
                                schema_version=TRADE_SCHEMA_VERSION,
                                source=SOURCE_ID,
                                symbol=descriptor.symbol.upper(),
                                aggregate_trade_id=aggregate_id,
                                price=price,
                                quantity=quantity,
                                first_trade_id=first_trade_id,
                                last_trade_id=last_trade_id,
                                occurred_at_ms=timestamp_ms,
                                buyer_is_maker=buyer_is_maker,
                                archive_sha256=actual_digest,
                                raw_row_number=row_number,
                            )
                        )
    except (OSError, UnicodeDecodeError, csv.Error, zipfile.BadZipFile) as exc:
        raise ReplayPricePathError("unable to parse aggregate-trade archive") from exc

    if (
        raw_count <= 0
        or first_raw_timestamp is None
        or last_raw_timestamp is None
        or first_raw_timestamp > request.requested_start_ms
        or last_raw_timestamp < request.requested_end_ms
    ):
        raise ReplayPricePathError("archive does not cover the requested interval")
    if not selected:
        raise ReplayPricePathError("archive produced no selected aggregate trades")
    evidence = ArchiveEvidence(
        symbol=descriptor.symbol.upper(),
        archive_relative_path=descriptor.archive_relative_path,
        archive_sha256=actual_digest,
        archive_size_bytes=archive_size,
        checksum_relative_path=descriptor.checksum_relative_path,
        checksum_file_sha256=checksum_file_sha256,
        checksum_claimed_sha256=claimed_digest,
        csv_member_name=member.filename,
        csv_member_size_bytes=member.file_size,
        raw_row_count=raw_count,
        selected_row_count=len(selected),
        first_raw_timestamp_ms=first_raw_timestamp,
        last_raw_timestamp_ms=last_raw_timestamp,
        first_selected_timestamp_ms=selected[0].occurred_at_ms,
        last_selected_timestamp_ms=selected[-1].occurred_at_ms,
    )
    return selected, evidence


def _load_dataset_decisions(  # noqa: C901
    dataset_root: Path,
    *,
    expected_manifest_sha256: str,
    label_horizon_ms: int,
    protected_holdout_start_ms: int,
) -> tuple[dict[str, tuple[int, ...]], dict[str, Any]]:
    if dataset_root.is_symlink() or not dataset_root.is_dir():
        raise ReplayPricePathError("dataset root must be a regular directory")
    manifest = _load_json(dataset_root / "manifest.json", field="dataset manifest")
    claimed_manifest = manifest.get("manifest_sha256")
    seed = dict(manifest)
    seed.pop("manifest_sha256", None)
    if claimed_manifest != expected_manifest_sha256 or canonical_sha256(seed) != claimed_manifest:
        raise ReplayPricePathError("dataset manifest identity mismatch")
    partitions = manifest.get("partitions")
    if not isinstance(partitions, list) or not partitions:
        raise ReplayPricePathError("dataset partitions are missing")
    decisions: dict[str, set[int]] = {}
    total_rows = 0
    for raw_partition in partitions:
        if not isinstance(raw_partition, dict):
            raise ReplayPricePathError("dataset partition is invalid")
        relative_path = str(raw_partition.get("relative_path", ""))
        path = _safe_member(dataset_root, relative_path)
        if sha256_file(path) != raw_partition.get("sha256"):
            raise ReplayPricePathError("dataset partition hash mismatch")
        row_count = 0
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    raise ReplayPricePathError("dataset partition contains a blank line")
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ReplayPricePathError("dataset row is invalid JSON") from exc
                if not isinstance(row, dict):
                    raise ReplayPricePathError("dataset row must be an object")
                claimed_row = row.get("row_sha256")
                row_seed = dict(row)
                row_seed.pop("row_sha256", None)
                if not isinstance(claimed_row, str) or canonical_sha256(row_seed) != claimed_row:
                    raise ReplayPricePathError(
                        f"dataset row hash mismatch at {relative_path}:{line_number}"
                    )
                symbol = str(row.get("symbol", "")).upper()
                decision_ms = _integer(
                    row.get("decision_timestamp_ms"),
                    field="decision_timestamp_ms",
                    minimum=1,
                )
                if decision_ms + label_horizon_ms >= protected_holdout_start_ms:
                    raise ReplayPricePathError("dataset decision horizon overlaps holdout")
                decisions.setdefault(symbol, set()).add(decision_ms)
                row_count += 1
                total_rows += 1
        if row_count != raw_partition.get("row_count"):
            raise ReplayPricePathError("dataset partition row count mismatch")
    if total_rows != manifest.get("total_rows"):
        raise ReplayPricePathError("dataset total row count mismatch")
    if sum(len(values) for values in decisions.values()) != total_rows:
        raise ReplayPricePathError("dataset contains duplicate symbol-decision keys")
    normalized = {symbol: tuple(sorted(values)) for symbol, values in sorted(decisions.items())}
    if not normalized:
        raise ReplayPricePathError("dataset contains no decisions")
    return normalized, manifest


def _verify_decision_coverage(
    *,
    trades_by_symbol: Mapping[str, Sequence[ReplayAggregateTrade]],
    decisions_by_symbol: Mapping[str, Sequence[int]],
    label_horizon_ms: int,
) -> int:
    maximum_entry_delay = 0
    for symbol, decisions in decisions_by_symbol.items():
        trades = trades_by_symbol.get(symbol)
        if not trades:
            raise ReplayPricePathError(f"missing trade path for dataset symbol {symbol}")
        timestamps = [item.occurred_at_ms for item in trades]
        for decision_ms in decisions:
            entry_index = bisect_left(timestamps, decision_ms)
            if entry_index >= len(trades):
                raise ReplayPricePathError("decision has no trade at or after decision time")
            entry_delay = trades[entry_index].occurred_at_ms - decision_ms
            maximum_entry_delay = max(maximum_entry_delay, entry_delay)
            horizon_end = decision_ms + label_horizon_ms
            horizon_index = bisect_left(timestamps, horizon_end)
            if horizon_index >= len(trades):
                raise ReplayPricePathError("decision path does not reach label horizon")
            if entry_index == horizon_index:
                raise ReplayPricePathError("decision horizon contains no aggregate trade")
    return maximum_entry_delay


def build_replay_price_path_package(
    *,
    input_root: Path,
    materialization_root: Path,
    output_root: Path,
    request: ReplayPricePathRequest,
) -> dict[str, object]:
    if output_root.exists() or output_root.is_symlink():
        return verify_replay_price_path_package(
            output_root=output_root,
            materialization_root=materialization_root,
            input_root=input_root,
        )
    if input_root.is_symlink() or not input_root.is_dir():
        raise ReplayPricePathError("input root must be a regular directory")
    input_root = input_root.resolve(strict=True)
    materialization_root = materialization_root.resolve(strict=True)
    verify_production_materialization(materialization_root)
    dataset_root = materialization_root / DATASET_DIR_NAME
    decisions, dataset_manifest = _load_dataset_decisions(
        dataset_root,
        expected_manifest_sha256=request.dataset_manifest_sha256,
        label_horizon_ms=request.label_horizon_ms,
        protected_holdout_start_ms=request.protected_holdout_start_ms,
    )
    if materialization_root.name != request.dataset_id:
        raise ReplayPricePathError("materialization root identity does not match request")
    if tuple(decisions) != request.symbols:
        raise ReplayPricePathError("request symbols do not match dataset decisions")
    earliest_decision = min(values[0] for values in decisions.values())
    latest_horizon = max(values[-1] + request.label_horizon_ms for values in decisions.values())
    if request.requested_start_ms > earliest_decision or request.requested_end_ms < latest_horizon:
        raise ReplayPricePathError("request interval does not cover every dataset horizon")

    trades_by_symbol: dict[str, list[ReplayAggregateTrade]] = {}
    archive_evidence: list[ArchiveEvidence] = []
    for descriptor in request.archives:
        trades, evidence = _parse_archive(
            input_root=input_root,
            descriptor=descriptor,
            request=request,
        )
        trades_by_symbol[descriptor.symbol.upper()] = trades
        archive_evidence.append(evidence)
    maximum_entry_delay = _verify_decision_coverage(
        trades_by_symbol=trades_by_symbol,
        decisions_by_symbol=decisions,
        label_horizon_ms=request.label_horizon_ms,
    )

    output_root = output_root.resolve()
    output_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.", dir=output_root.parent))
    try:
        partitions: list[TradePartition] = []
        for symbol in request.symbols:
            trades = trades_by_symbol[symbol]
            path = staging / TRADES_DIR_NAME / f"{symbol}.jsonl"
            _write_jsonl(path, (trade.as_json_dict() for trade in trades))
            partitions.append(
                TradePartition(
                    symbol=symbol,
                    relative_path=path.relative_to(staging).as_posix(),
                    row_count=len(trades),
                    first_timestamp_ms=trades[0].occurred_at_ms,
                    last_timestamp_ms=trades[-1].occurred_at_ms,
                    first_aggregate_trade_id=trades[0].aggregate_trade_id,
                    last_aggregate_trade_id=trades[-1].aggregate_trade_id,
                    sha256=sha256_file(path),
                )
            )
        manifest = ReplayPricePathManifest(
            schema_version=MANIFEST_SCHEMA_VERSION,
            package_id=request.package_id,
            request_sha256=request.request_sha256,
            dataset_id=request.dataset_id,
            dataset_manifest_sha256=request.dataset_manifest_sha256,
            market_manifest_sha256=request.market_manifest_sha256,
            source_commit_sha=request.source_commit_sha,
            provider_id=PROVIDER_ID,
            source=SOURCE_ID,
            data_kind=DATA_KIND,
            requested_date=request.requested_date,
            requested_start_ms=request.requested_start_ms,
            requested_end_ms=request.requested_end_ms,
            label_horizon_ms=request.label_horizon_ms,
            protected_holdout_start_ms=request.protected_holdout_start_ms,
            symbols=request.symbols,
            decision_count=sum(len(values) for values in decisions.values()),
            archive_evidence=tuple(archive_evidence),
            partitions=tuple(partitions),
            total_trade_rows=sum(len(values) for values in trades_by_symbol.values()),
            maximum_entry_delay_ms=maximum_entry_delay,
            public_only=True,
            protected_holdout_accessed=False,
            immutable_inputs_mutated=False,
            replay_authorized=False,
            model_execution_authorized=False,
            performance_research_authorized=False,
            execution_enabled=False,
            live_capital_authorized=False,
            trading_credentials_present=False,
            orders_submitted=0,
        )
        _write_json(staging / REQUEST_NAME, json.loads(canonical_json(request)))
        _write_json(staging / MANIFEST_NAME, manifest.as_json_dict())
        _write_json(
            staging / REPORT_NAME,
            {
                "schema_version": REPORT_SCHEMA_VERSION,
                "status": "verified",
                "outcome": "accepted",
                "package_id": request.package_id,
                "manifest_sha256": manifest.manifest_sha256,
                "dataset_manifest_sha256": dataset_manifest["manifest_sha256"],
                "decision_count": manifest.decision_count,
                "total_trade_rows": manifest.total_trade_rows,
                "maximum_entry_delay_ms": manifest.maximum_entry_delay_ms,
                "exact_trade_sequence_available": True,
                "protected_holdout_accessed": False,
                "immutable_inputs_mutated": False,
                "replay_authorized": False,
                "model_execution_authorized": False,
                "performance_research_authorized": False,
                "execution_enabled": False,
                "live_capital_authorized": False,
                "trading_credentials_present": False,
                "orders_submitted": 0,
            },
        )
        checksum_paths = [
            staging / REQUEST_NAME,
            staging / MANIFEST_NAME,
            staging / REPORT_NAME,
            *(staging / item.relative_path for item in manifest.partitions),
        ]
        checksum_lines = [
            f"{sha256_file(path)}  {path.relative_to(staging).as_posix()}"
            for path in sorted(checksum_paths)
        ]
        _write_new(
            staging / CHECKSUM_INDEX_NAME,
            ("\n".join(checksum_lines) + "\n").encode("utf-8"),
        )
        verify_replay_price_path_package(
            output_root=staging,
            materialization_root=materialization_root,
            input_root=input_root,
        )
        staging.replace(output_root)
        return verify_replay_price_path_package(
            output_root=output_root,
            materialization_root=materialization_root,
            input_root=input_root,
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _trade_from_json(payload: Mapping[str, object]) -> ReplayAggregateTrade:
    try:
        trade = ReplayAggregateTrade(
            schema_version=str(payload["schema_version"]),
            source=str(payload["source"]),
            symbol=str(payload["symbol"]),
            aggregate_trade_id=_integer(
                payload["aggregate_trade_id"], field="aggregate_trade_id", minimum=0
            ),
            price=_decimal(payload["price"], field="price", positive=True),
            quantity=_decimal(payload["quantity"], field="quantity", positive=True),
            first_trade_id=_integer(payload["first_trade_id"], field="first_trade_id", minimum=0),
            last_trade_id=_integer(payload["last_trade_id"], field="last_trade_id", minimum=0),
            occurred_at_ms=_integer(payload["occurred_at_ms"], field="occurred_at_ms", minimum=1),
            buyer_is_maker=_boolean(payload["buyer_is_maker"], field="buyer_is_maker"),
            archive_sha256=str(payload["archive_sha256"]),
            raw_row_number=_integer(payload["raw_row_number"], field="raw_row_number", minimum=1),
        )
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ReplayPricePathError):
            raise
        raise ReplayPricePathError("invalid normalized aggregate trade") from exc
    if payload.get("trade_sha256") != trade.trade_sha256:
        raise ReplayPricePathError("normalized trade hash mismatch")
    return trade


def verify_replay_price_path_package(  # noqa: C901
    *,
    output_root: Path,
    materialization_root: Path,
    input_root: Path | None = None,
) -> dict[str, object]:
    if output_root.is_symlink() or not output_root.is_dir():
        raise ReplayPricePathError("price-path root must be a regular directory")
    request = load_request(output_root / REQUEST_NAME)
    manifest_payload = _load_json(output_root / MANIFEST_NAME, field="price-path manifest")
    claimed_manifest = manifest_payload.get("manifest_sha256")
    seed = dict(manifest_payload)
    seed.pop("manifest_sha256", None)
    if not isinstance(claimed_manifest, str) or canonical_sha256(seed) != claimed_manifest:
        raise ReplayPricePathError("price-path manifest self hash mismatch")
    if request.request_sha256 != manifest_payload.get("request_sha256"):
        raise ReplayPricePathError("price-path request identity mismatch")
    if (
        request.package_id != manifest_payload.get("package_id")
        or request.dataset_id != manifest_payload.get("dataset_id")
        or request.dataset_manifest_sha256 != manifest_payload.get("dataset_manifest_sha256")
        or request.market_manifest_sha256 != manifest_payload.get("market_manifest_sha256")
    ):
        raise ReplayPricePathError("price-path request binding mismatch")
    symbols = manifest_payload.get("symbols")
    partitions = manifest_payload.get("partitions")
    archives = manifest_payload.get("archive_evidence")
    if (
        not isinstance(symbols, list)
        or not isinstance(partitions, list)
        or not isinstance(archives, list)
    ):
        raise ReplayPricePathError("price-path manifest lists are invalid")

    materialization_root = materialization_root.resolve(strict=True)
    verify_production_materialization(materialization_root)
    dataset_root = materialization_root / DATASET_DIR_NAME
    decisions, dataset_manifest = _load_dataset_decisions(
        dataset_root,
        expected_manifest_sha256=str(manifest_payload["dataset_manifest_sha256"]),
        label_horizon_ms=_integer(
            manifest_payload["label_horizon_ms"], field="label_horizon_ms", minimum=1
        ),
        protected_holdout_start_ms=_integer(
            manifest_payload["protected_holdout_start_ms"],
            field="protected_holdout_start_ms",
            minimum=1,
        ),
    )
    if tuple(decisions) != tuple(str(item) for item in symbols):
        raise ReplayPricePathError("verified dataset symbols do not match manifest")

    archive_by_symbol: dict[str, dict[str, object]] = {}
    for raw_archive in archives:
        if not isinstance(raw_archive, dict):
            raise ReplayPricePathError("archive evidence is invalid")
        symbol = str(raw_archive.get("symbol", ""))
        if symbol in archive_by_symbol:
            raise ReplayPricePathError("duplicate archive evidence symbol")
        archive_by_symbol[symbol] = raw_archive
    if tuple(sorted(archive_by_symbol)) != tuple(str(item) for item in symbols):
        raise ReplayPricePathError("archive evidence symbol coverage mismatch")

    trades_by_symbol: dict[str, list[ReplayAggregateTrade]] = {}
    total_rows = 0
    for raw_partition in partitions:
        if not isinstance(raw_partition, dict):
            raise ReplayPricePathError("price-path partition is invalid")
        symbol = str(raw_partition.get("symbol", ""))
        if symbol in trades_by_symbol:
            raise ReplayPricePathError("duplicate price-path partition symbol")
        path = _safe_member(output_root, str(raw_partition.get("relative_path", "")))
        if sha256_file(path) != raw_partition.get("sha256"):
            raise ReplayPricePathError("price-path partition hash mismatch")
        trades: list[ReplayAggregateTrade] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    raise ReplayPricePathError("price-path partition contains a blank line")
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ReplayPricePathError("normalized trade is invalid JSON") from exc
                if not isinstance(payload, dict):
                    raise ReplayPricePathError("normalized trade must be an object")
                trade = _trade_from_json(payload)
                if trade.symbol != symbol:
                    raise ReplayPricePathError("partition symbol mismatch")
                if trade.archive_sha256 != archive_by_symbol[symbol].get("archive_sha256"):
                    raise ReplayPricePathError("normalized trade archive identity mismatch")
                if trades and (
                    trade.occurred_at_ms,
                    trade.aggregate_trade_id,
                ) <= (
                    trades[-1].occurred_at_ms,
                    trades[-1].aggregate_trade_id,
                ):
                    raise ReplayPricePathError("normalized trades are not strictly ordered")
                trades.append(trade)
        if len(trades) != raw_partition.get("row_count") or not trades:
            raise ReplayPricePathError("price-path partition row count mismatch")
        expected_partition_values = {
            "first_timestamp_ms": trades[0].occurred_at_ms,
            "last_timestamp_ms": trades[-1].occurred_at_ms,
            "first_aggregate_trade_id": trades[0].aggregate_trade_id,
            "last_aggregate_trade_id": trades[-1].aggregate_trade_id,
        }
        for key, value in expected_partition_values.items():
            if raw_partition.get(key) != value:
                raise ReplayPricePathError(f"price-path partition {key} mismatch")
        trades_by_symbol[symbol] = trades
        total_rows += len(trades)
    if total_rows != manifest_payload.get("total_trade_rows"):
        raise ReplayPricePathError("price-path total trade count mismatch")

    maximum_entry_delay = _verify_decision_coverage(
        trades_by_symbol=trades_by_symbol,
        decisions_by_symbol=decisions,
        label_horizon_ms=_integer(
            manifest_payload["label_horizon_ms"], field="label_horizon_ms", minimum=1
        ),
    )
    if maximum_entry_delay != manifest_payload.get("maximum_entry_delay_ms"):
        raise ReplayPricePathError("maximum entry delay evidence mismatch")

    if input_root is not None:
        resolved_input = input_root.resolve(strict=True)
        for raw in archive_by_symbol.values():
            archive = _safe_member(resolved_input, str(raw.get("archive_relative_path", "")))
            checksum = _safe_member(resolved_input, str(raw.get("checksum_relative_path", "")))
            if sha256_file(archive) != raw.get("archive_sha256"):
                raise ReplayPricePathError("source archive hash changed")
            if sha256_file(checksum) != raw.get("checksum_file_sha256"):
                raise ReplayPricePathError("source checksum file hash changed")

    checksum_path = output_root / CHECKSUM_INDEX_NAME
    if checksum_path.is_symlink() or not checksum_path.is_file():
        raise ReplayPricePathError("artifact checksum index is missing")
    checksum_lines = checksum_path.read_text(encoding="utf-8").splitlines()
    if not checksum_lines:
        raise ReplayPricePathError("artifact checksum index is empty")
    expected_logical_names = {
        REQUEST_NAME,
        MANIFEST_NAME,
        REPORT_NAME,
        *(str(item["relative_path"]) for item in partitions),
    }
    observed_logical_names: set[str] = set()
    for line in checksum_lines:
        digest, separator, logical_name = line.partition("  ")
        if (
            not separator
            or logical_name in observed_logical_names
            or sha256_file(_safe_member(output_root, logical_name)) != digest
        ):
            raise ReplayPricePathError("artifact checksum index mismatch")
        observed_logical_names.add(logical_name)
    if observed_logical_names != expected_logical_names:
        raise ReplayPricePathError("artifact checksum index coverage mismatch")

    report = _load_json(output_root / REPORT_NAME, field="verification report")
    if (
        report.get("outcome") != "accepted"
        or report.get("exact_trade_sequence_available") is not True
        or report.get("manifest_sha256") != claimed_manifest
    ):
        raise ReplayPricePathError("verification report terminal state mismatch")
    for payload, field in ((manifest_payload, "manifest"), (report, "verification report")):
        if payload.get("protected_holdout_accessed") is not False:
            raise ReplayPricePathError(f"{field} accessed protected holdout")
        if payload.get("immutable_inputs_mutated") is not False:
            raise ReplayPricePathError(f"{field} mutated immutable inputs")
        for key in (
            "replay_authorized",
            "model_execution_authorized",
            "performance_research_authorized",
            "execution_enabled",
            "live_capital_authorized",
            "trading_credentials_present",
        ):
            if payload.get(key) is not False:
                raise ReplayPricePathError(f"{field} enables unsafe authority: {key}")
        if payload.get("orders_submitted") != 0:
            raise ReplayPricePathError(f"{field} submitted orders")

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "verified",
        "outcome": "accepted",
        "package_id": manifest_payload["package_id"],
        "manifest_sha256": claimed_manifest,
        "dataset_manifest_sha256": dataset_manifest["manifest_sha256"],
        "decision_count": manifest_payload["decision_count"],
        "symbol_count": len(symbols),
        "total_trade_rows": total_rows,
        "maximum_entry_delay_ms": maximum_entry_delay,
        "exact_trade_sequence_available": True,
        "protected_holdout_accessed": False,
        "immutable_inputs_mutated": False,
        "replay_authorized": False,
        "model_execution_authorized": False,
        "performance_research_authorized": False,
        "execution_enabled": False,
        "live_capital_authorized": False,
        "trading_credentials_present": False,
        "orders_submitted": 0,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WickHunter replay price-path importer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    materialize = subparsers.add_parser("materialize")
    materialize.add_argument("--request", type=Path, required=True)
    materialize.add_argument("--input-root", type=Path, required=True)
    materialize.add_argument("--materialization-root", type=Path, required=True)
    materialize.add_argument("--output-root", type=Path, required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--output-root", type=Path, required=True)
    verify.add_argument("--materialization-root", type=Path, required=True)
    verify.add_argument("--input-root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        result = build_replay_price_path_package(
            input_root=args.input_root,
            materialization_root=args.materialization_root,
            output_root=args.output_root,
            request=load_request(args.request),
        )
    else:
        result = verify_replay_price_path_package(
            output_root=args.output_root,
            materialization_root=args.materialization_root,
            input_root=args.input_root,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
