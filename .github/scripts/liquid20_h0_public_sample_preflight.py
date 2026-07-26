from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import time
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path("work")
TARGETS = {"BTCUSDT", "ETHUSDT"}
REQUIRED_HEADER = [
    "exchange",
    "symbol",
    "timestamp",
    "local_timestamp",
    "id",
    "side",
    "price",
    "amount",
]
SAMPLE_DATE = "2025/03/01"
CANDIDATE_START = "2025-02-20T00:00:00Z"
CANDIDATE_END = "2026-07-25T00:00:00Z"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download(url: str, path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "liquid20-h0-public-preflight/1"})
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
            path.write_bytes(payload)
            return payload
        except Exception as exc:  # noqa: BLE001 - bounded retry reports the final network failure
            last_error = exc
            if attempt < 3:
                time.sleep(2**attempt)
    raise RuntimeError(f"download failed for {url}: {last_error}")


def micros_to_iso(value: int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value / 1_000_000, tz=UTC).isoformat().replace("+00:00", "Z")


def compact_symbol_entries(value: object) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if value.get("id") in TARGETS:
            found.append(
                {
                    key: value.get(key)
                    for key in (
                        "id",
                        "type",
                        "availableSince",
                        "availableTo",
                        "dataTypes",
                    )
                    if key in value
                }
            )
        for child in value.values():
            found.extend(compact_symbol_entries(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(compact_symbol_entries(child))
    unique = {json.dumps(entry, sort_keys=True, separators=(",", ":")): entry for entry in found}
    return [unique[key] for key in sorted(unique)]


def compact_incidents(data: object) -> dict[str, Any]:
    incidents = data.get("incidents", []) if isinstance(data, dict) else []
    if not isinstance(incidents, list):
        return {"count": 0, "overlap_candidate_window": []}
    overlaps: list[dict[str, Any]] = []
    for incident in incidents:
        if not isinstance(incident, dict):
            continue
        start = str(incident.get("from") or incident.get("start") or incident.get("fromDate") or "")
        end = str(incident.get("to") or incident.get("end") or incident.get("toDate") or "")
        if start and start < CANDIDATE_END and (not end or end >= CANDIDATE_START):
            overlaps.append(
                {
                    key: incident.get(key)
                    for key in (
                        "from",
                        "to",
                        "start",
                        "end",
                        "fromDate",
                        "toDate",
                        "status",
                        "description",
                    )
                    if key in incident
                }
            )
    return {"count": len(incidents), "overlap_candidate_window": overlaps}


def inspect_metadata(exchange: str) -> dict[str, Any]:
    url = f"https://api.tardis.dev/v1/exchanges/{exchange}"
    payload = download(url, ROOT / "metadata" / f"{exchange}.json")
    data = json.loads(payload)
    datasets = data.get("datasets", {}) if isinstance(data, dict) else {}
    return {
        "kind": "metadata",
        "exchange": exchange,
        "source_url": url,
        "filename": f"{exchange}.json",
        "size_bytes": len(payload),
        "sha256": sha256(payload),
        "datasets_exported_from": datasets.get("exportedFrom") if isinstance(datasets, dict) else None,
        "datasets_exported_until": datasets.get("exportedUntil") if isinstance(datasets, dict) else None,
        "target_symbols": compact_symbol_entries(data),
        "incidents": compact_incidents(data),
    }


def inspect_sample(exchange: str, symbol: str) -> dict[str, Any]:
    filename = f"{exchange}_liquidations_2025-03-01_{symbol}.csv.gz"
    url = f"https://datasets.tardis.dev/v1/{exchange}/liquidations/{SAMPLE_DATE}/{symbol}.csv.gz"
    compressed = download(url, ROOT / "samples" / filename)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode="rb") as stream:
        uncompressed = stream.read()
    text = uncompressed.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    header = reader.fieldnames or []

    null_counts: Counter[str] = Counter()
    sides: Counter[str] = Counter()
    symbols: Counter[str] = Counter()
    exchanges: Counter[str] = Counter()
    exact_rows: Counter[tuple[str, ...]] = Counter()
    timestamps: list[int] = []
    local_timestamps: list[int] = []
    malformed_rows = 0
    non_positive_price_rows = 0
    non_positive_amount_rows = 0

    for row in rows:
        if set(row) != set(REQUIRED_HEADER) or None in row:
            malformed_rows += 1
        for key in REQUIRED_HEADER:
            if row.get(key, "") == "":
                null_counts[key] += 1
        sides[row.get("side", "")] += 1
        symbols[row.get("symbol", "")] += 1
        exchanges[row.get("exchange", "")] += 1
        exact_rows[tuple(row.get(key, "") for key in REQUIRED_HEADER)] += 1
        if row.get("timestamp"):
            timestamps.append(int(row["timestamp"]))
        if row.get("local_timestamp"):
            local_timestamps.append(int(row["local_timestamp"]))
        try:
            if float(row.get("price", "nan")) <= 0:
                non_positive_price_rows += 1
        except ValueError:
            non_positive_price_rows += 1
        try:
            if float(row.get("amount", "nan")) <= 0:
                non_positive_amount_rows += 1
        except ValueError:
            non_positive_amount_rows += 1

    return {
        "kind": "sample",
        "exchange": exchange,
        "symbol": symbol,
        "sample_date": "2025-03-01",
        "source_url": url,
        "filename": filename,
        "compression": "gzip",
        "format": "csv",
        "compressed_size_bytes": len(compressed),
        "uncompressed_size_bytes": len(uncompressed),
        "compressed_sha256": sha256(compressed),
        "uncompressed_sha256": sha256(uncompressed),
        "gzip_integrity": True,
        "header": header,
        "header_matches_contract": header == REQUIRED_HEADER,
        "row_count": len(rows),
        "exchanges": dict(sorted(exchanges.items())),
        "symbols": dict(sorted(symbols.items())),
        "sides": dict(sorted(sides.items())),
        "null_counts": dict(sorted(null_counts.items())),
        "malformed_rows": malformed_rows,
        "exact_duplicate_rows": sum(count - 1 for count in exact_rows.values() if count > 1),
        "non_positive_price_rows": non_positive_price_rows,
        "non_positive_amount_rows": non_positive_amount_rows,
        "timestamp_unit": "microseconds_since_unix_epoch",
        "timestamp_timezone": "UTC",
        "timestamp_min": micros_to_iso(min(timestamps) if timestamps else None),
        "timestamp_max": micros_to_iso(max(timestamps) if timestamps else None),
        "local_timestamp_min": micros_to_iso(min(local_timestamps) if local_timestamps else None),
        "local_timestamp_max": micros_to_iso(max(local_timestamps) if local_timestamps else None),
        "provider_capture_timestamp_present_rows": len(local_timestamps),
        "provider_capture_timestamp_missing_rows": len(rows) - len(local_timestamps),
        "local_before_exchange_timestamp_rows": sum(
            1
            for row in rows
            if row.get("timestamp")
            and row.get("local_timestamp")
            and int(row["local_timestamp"]) < int(row["timestamp"])
        ),
    }


def main() -> None:
    results: list[dict[str, Any]] = []
    for exchange in ("bybit", "binance-futures"):
        results.append(inspect_metadata(exchange))
    for exchange in ("bybit", "binance-futures"):
        for symbol in ("BTCUSDT", "ETHUSDT"):
            results.append(inspect_sample(exchange, symbol))
    for result in results:
        print("LIQUID20_H0_RESULT=" + json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
