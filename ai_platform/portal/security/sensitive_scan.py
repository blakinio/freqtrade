from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ai_platform.portal.security.sensitive_data import (
    DEFAULT_MAX_DEPTH,
    DEFAULT_MAX_ITEMS,
    DEFAULT_MAX_SERIALIZED_LAYERS,
    DEFAULT_MAX_STRING_BYTES,
    SensitiveDataLimitError,
    classify_sensitive_key,
    classify_sensitive_text,
    decode_serialized_structure,
)


_SUPPORTED_SUFFIXES = frozenset({".db", ".json", ".jsonl", ".ndjson", ".sqlite", ".sqlite3"})
_EXCLUDED_DIRECTORIES = frozenset(
    {".git", ".mypy_cache", ".pytest_cache", "node_modules", "__pycache__"}
)
_EXCLUDED_FILENAMES = frozenset(
    {
        "package-lock.json",  # Generated dependency graph, not persisted Portal metadata.
    }
)
_DEFAULT_MAX_FILE_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class ScanFinding:
    source: str
    record_id: str
    path: str
    classification: str
    finding_type: str


@dataclass(frozen=True, slots=True)
class ScanReport:
    scanned_files: int
    findings: tuple[ScanFinding, ...]
    errors: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(
            {
                "scanned_files": self.scanned_files,
                "finding_count": len(self.findings),
                "findings": [asdict(finding) for finding in self.findings],
                "errors": list(self.errors),
            },
            indent=2,
            sort_keys=True,
        )


def scan_paths(
    paths: Sequence[Path],
    *,
    max_file_bytes: int = _DEFAULT_MAX_FILE_BYTES,
) -> ScanReport:
    findings: list[ScanFinding] = []
    errors: list[str] = []
    scanned_files = 0
    for path in _iter_supported_files(paths):
        scanned_files += 1
        try:
            if path.stat().st_size > max_file_bytes:
                errors.append(f"{path}: file_size_limit")
                continue
            if path.suffix.casefold() in {".db", ".sqlite", ".sqlite3"}:
                findings.extend(_scan_sqlite(path))
            else:
                findings.extend(_scan_json_file(path))
        except (OSError, sqlite3.Error, json.JSONDecodeError, UnicodeError) as exc:
            errors.append(f"{path}: {type(exc).__name__}")
    return ScanReport(
        scanned_files=scanned_files,
        findings=tuple(sorted(findings, key=lambda item: (item.source, item.record_id, item.path))),
        errors=tuple(sorted(errors)),
    )


def scan_value(
    value: Any,
    *,
    source: str,
    record_id: str,
    path: str = "payload",
) -> tuple[ScanFinding, ...]:
    findings: list[ScanFinding] = []
    _collect(
        value,
        source=source,
        record_id=record_id,
        path=path,
        depth=0,
        serialized_depth=0,
        budget=[0],
        active=set(),
        findings=findings,
    )
    return tuple(findings)


def _iter_supported_files(paths: Sequence[Path]) -> Iterator[Path]:
    seen: set[Path] = set()
    for root in paths:
        candidates: Iterator[Path]
        if root.is_file():
            candidates = iter((root,))
        elif root.is_dir():
            candidates = (
                candidate
                for candidate in root.rglob("*")
                if not any(part in _EXCLUDED_DIRECTORIES for part in candidate.parts)
            )
        else:
            continue
        for candidate in candidates:
            if (
                not candidate.is_file()
                or candidate.name in _EXCLUDED_FILENAMES
                or candidate.suffix.casefold() not in _SUPPORTED_SUFFIXES
            ):
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield candidate


def _scan_json_file(path: Path) -> tuple[ScanFinding, ...]:
    if path.suffix.casefold() in {".jsonl", ".ndjson"}:
        findings: list[ScanFinding] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                findings.extend(
                    scan_value(
                        value,
                        source=str(path),
                        record_id=f"line:{line_number}",
                    )
                )
        return tuple(findings)
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return scan_value(value, source=str(path), record_id="document")


def _scan_sqlite(path: Path) -> tuple[ScanFinding, ...]:
    findings: list[ScanFinding] = []
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    try:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for (table_name,) in tables:
            quoted_table = _quote_identifier(str(table_name))
            columns = connection.execute(f"PRAGMA table_info({quoted_table})").fetchall()
            column_names = [str(column[1]) for column in columns]
            if not column_names:
                continue
            query_columns = ", ".join(_quote_identifier(name) for name in column_names)
            cursor = connection.execute(f"SELECT rowid, {query_columns} FROM {quoted_table}")
            for row in cursor:
                record_id = f"{table_name}:rowid:{row[0]}"
                for column_name, value in zip(column_names, row[1:], strict=True):
                    field_path = f"{table_name}.{column_name}"
                    match = classify_sensitive_key(column_name)
                    if match is not None:
                        findings.append(
                            ScanFinding(
                                source=str(path),
                                record_id=record_id,
                                path=field_path,
                                classification=match.kind.value,
                                finding_type="field",
                            )
                        )
                        continue
                    if isinstance(value, str):
                        decoded: Any = value
                        stripped = value.strip()
                        if stripped[:1] in {"{", "["}:
                            try:
                                decoded = json.loads(stripped)
                            except json.JSONDecodeError:
                                decoded = value
                        findings.extend(
                            scan_value(
                                decoded,
                                source=str(path),
                                record_id=record_id,
                                path=field_path,
                            )
                        )
    finally:
        connection.close()
    return tuple(findings)


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _collect(
    value: Any,
    *,
    source: str,
    record_id: str,
    path: str,
    depth: int,
    serialized_depth: int,
    budget: list[int],
    active: set[int],
    findings: list[ScanFinding],
) -> None:
    if depth > DEFAULT_MAX_DEPTH:
        findings.append(_structural_finding(source, record_id, path, "depth_limit"))
        return
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in active:
            findings.append(_structural_finding(source, record_id, path, "cycle"))
            return
        active.add(identity)
        try:
            for key, child in value.items():
                if not isinstance(key, str):
                    findings.append(_structural_finding(source, record_id, path, "non_string_key"))
                    continue
                child_path = f"{path}.{key}"
                if not _consume_budget(source, record_id, child_path, budget, findings):
                    return
                match = classify_sensitive_key(key)
                if match is not None:
                    findings.append(
                        ScanFinding(
                            source=source,
                            record_id=record_id,
                            path=child_path,
                            classification=match.kind.value,
                            finding_type="field",
                        )
                    )
                    continue
                _collect(
                    child,
                    source=source,
                    record_id=record_id,
                    path=child_path,
                    depth=depth + 1,
                    serialized_depth=serialized_depth,
                    budget=budget,
                    active=active,
                    findings=findings,
                )
        finally:
            active.remove(identity)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        identity = id(value)
        if identity in active:
            findings.append(_structural_finding(source, record_id, path, "cycle"))
            return
        active.add(identity)
        try:
            for index, child in enumerate(value):
                child_path = f"{path}[{index}]"
                if not _consume_budget(source, record_id, child_path, budget, findings):
                    return
                _collect(
                    child,
                    source=source,
                    record_id=record_id,
                    path=child_path,
                    depth=depth + 1,
                    serialized_depth=serialized_depth,
                    budget=budget,
                    active=active,
                    findings=findings,
                )
        finally:
            active.remove(identity)
        return
    if isinstance(value, str):
        if len(value.encode("utf-8")) > DEFAULT_MAX_STRING_BYTES:
            findings.append(_structural_finding(source, record_id, path, "string_byte_limit"))
            return
        value_match = classify_sensitive_text(value)
        if value_match is not None:
            findings.append(
                ScanFinding(
                    source=source,
                    record_id=record_id,
                    path=path,
                    classification=value_match.kind.value,
                    finding_type="value",
                )
            )
            return
        if serialized_depth < DEFAULT_MAX_SERIALIZED_LAYERS:
            try:
                decoded = decode_serialized_structure(value, max_items=DEFAULT_MAX_ITEMS)
            except SensitiveDataLimitError:
                findings.append(_structural_finding(source, record_id, path, "serialized_limit"))
                return
            if decoded is not None:
                encoding, structured = decoded
                _collect(
                    structured,
                    source=source,
                    record_id=record_id,
                    path=f"{path}#{encoding}",
                    depth=depth + 1,
                    serialized_depth=serialized_depth + 1,
                    budget=budget,
                    active=active,
                    findings=findings,
                )
        return
    if isinstance(value, (set, frozenset, bytes, bytearray)):
        findings.append(_structural_finding(source, record_id, path, "unsupported_type"))


def _consume_budget(
    source: str,
    record_id: str,
    path: str,
    budget: list[int],
    findings: list[ScanFinding],
) -> bool:
    budget[0] += 1
    if budget[0] <= DEFAULT_MAX_ITEMS:
        return True
    findings.append(_structural_finding(source, record_id, path, "item_limit"))
    return False


def _structural_finding(source: str, record_id: str, path: str, classification: str) -> ScanFinding:
    return ScanFinding(
        source=source,
        record_id=record_id,
        path=path,
        classification=classification,
        finding_type="unsafe_structure",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan Portal JSON/JSONL/SQLite artifacts without printing protected values."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--allow-findings", action="store_true")
    parser.add_argument("--max-file-bytes", type=int, default=_DEFAULT_MAX_FILE_BYTES)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = scan_paths(args.paths, max_file_bytes=args.max_file_bytes)
    serialized = report.to_json()
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)
    if report.errors:
        return 2
    if report.findings and not args.allow_findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
