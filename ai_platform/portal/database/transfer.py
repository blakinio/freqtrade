from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, func, inspect, select, text

from ai_platform.portal.control_plane.database import Base, build_engine
from ai_platform.portal.database.model_registry import load_portal_models
from ai_platform.portal.database.schema import (
    INITIAL_SCHEMA_REVISION,
    OIDC_LOGOUT_REPLAY_TABLE_NAME,
    assert_schema_ready,
    scan_database_integrity,
    schema_status,
)


class PortalStateTransferError(RuntimeError):
    pass


def _manifest_tables():
    manifest = load_portal_models()
    return tuple(table for table in Base.metadata.sorted_tables if table.name in manifest)


def _source_authority(source: Engine) -> tuple[str, dict[str, Any], frozenset[str]]:
    if source.dialect.name != "sqlite":
        raise PortalStateTransferError("Portal state transfer source must be SQLite")

    status = schema_status(source)
    source_tables = frozenset(
        table_name
        for table_name in inspect(source).get_table_names()
        if table_name.startswith("portal_")
    )
    if status["status"] == "ready":
        authority = "versioned_current"
    else:
        differences = status["differences"]
        missing_tables = differences["missing_tables"]
        unexpected_tables = differences["unexpected_tables"]
        changed_tables = differences["changed_tables"]
        revisions = status["applied_revisions"]
        structurally_safe = not unexpected_tables and not changed_tables
        if structurally_safe and not missing_tables and not revisions:
            authority = "unversioned_structural_current"
        elif (
            structurally_safe
            and missing_tables == [OIDC_LOGOUT_REPLAY_TABLE_NAME]
            and (
                not revisions
                or (
                    len(revisions) == 1
                    and revisions[0]["revision_id"] == INITIAL_SCHEMA_REVISION
                    and revisions[0]["dialect_name"] == "sqlite"
                )
            )
        ):
            authority = "structural_pre_logout_replay"
        else:
            raise PortalStateTransferError(
                "legacy SQLite schema is divergent; backup, quarantine and explicit recovery are required"
            )

    integrity = scan_database_integrity(source)
    if integrity["status"] != "clean":
        raise PortalStateTransferError(
            "legacy SQLite integrity scan requires quarantine before state transfer"
        )
    return authority, status, source_tables


def _target_row_counts(target: Engine) -> dict[str, int]:
    counts: dict[str, int] = {}
    with target.connect() as connection:
        for table in _manifest_tables():
            counts[table.name] = int(
                connection.execute(select(func.count()).select_from(table)).scalar_one()
            )
    return counts


def _reset_postgresql_sequences(connection: Any) -> None:
    for table in _manifest_tables():
        for column in table.primary_key.columns:
            if not getattr(column, "autoincrement", False):
                continue
            sequence = connection.execute(
                text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
                {"table_name": table.name, "column_name": column.name},
            ).scalar_one_or_none()
            if not sequence:
                continue
            maximum = connection.execute(select(func.max(column))).scalar_one_or_none()
            if maximum is None:
                continue
            connection.execute(
                text("SELECT setval(CAST(:sequence AS regclass), :value, true)"),
                {"sequence": sequence, "value": int(maximum)},
            )


def transfer_portal_state(source: Engine, target: Engine) -> dict[str, Any]:
    if target.dialect.name != "postgresql":
        raise PortalStateTransferError("Portal state transfer target must be PostgreSQL")

    authority, source_status, source_tables = _source_authority(source)
    target_status = assert_schema_ready(target)
    existing_target_counts = _target_row_counts(target)
    nonempty_target = sorted(
        table_name for table_name, row_count in existing_target_counts.items() if row_count
    )
    if nonempty_target:
        raise PortalStateTransferError(
            "target PostgreSQL contains Portal rows; refusing non-idempotent state transfer"
        )

    copied_counts: dict[str, int] = {}
    with source.connect() as source_connection, target.begin() as target_connection:
        for table in _manifest_tables():
            if table.name not in source_tables:
                if table.name == OIDC_LOGOUT_REPLAY_TABLE_NAME:
                    copied_counts[table.name] = 0
                    continue
                raise PortalStateTransferError(
                    f"legacy SQLite source is missing required table {table.name}"
                )
            result = source_connection.execute(select(table)).mappings()
            copied = 0
            batch: list[dict[str, Any]] = []
            for row in result:
                batch.append(dict(row))
                if len(batch) >= 500:
                    target_connection.execute(table.insert(), batch)
                    copied += len(batch)
                    batch.clear()
            if batch:
                target_connection.execute(table.insert(), batch)
                copied += len(batch)
            copied_counts[table.name] = copied
        _reset_postgresql_sequences(target_connection)

    target_counts = _target_row_counts(target)
    mismatches = {
        table_name: {"copied": copied_counts[table_name], "target": target_counts[table_name]}
        for table_name in copied_counts
        if copied_counts[table_name] != target_counts[table_name]
    }
    if mismatches:
        raise PortalStateTransferError("PostgreSQL row-count verification failed after state transfer")

    target_integrity = scan_database_integrity(target)
    if target_integrity["status"] != "clean":
        raise PortalStateTransferError("PostgreSQL integrity verification failed after state transfer")

    return {
        "status": "transferred",
        "source_authority": authority,
        "source_revision": (
            source_status["applied_revisions"][-1]["revision_id"]
            if source_status["applied_revisions"]
            else None
        ),
        "target_revision": target_status["expected_revision"]["revision_id"],
        "tables_copied": len(copied_counts),
        "rows_copied": sum(copied_counts.values()),
        "row_counts": copied_counts,
        "integrity": "clean",
        "safety": {
            "row_values_recorded": False,
            "secret_values_recorded": False,
            "protected_production_mutated": False,
            "live_capital_authorized": False,
        },
    }


def _write_report(report: dict[str, Any], output: Path | None) -> None:
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline value-preserving Portal SQLite to PostgreSQL state transfer"
    )
    parser.add_argument("--source-sqlite", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    source_path = args.source_sqlite.resolve()
    if not source_path.is_file():
        raise PortalStateTransferError("legacy SQLite snapshot file is missing")
    target_url = os.environ.get("PORTAL_DATABASE_URL", "").strip()
    if not target_url:
        raise PortalStateTransferError("PORTAL_DATABASE_URL is required")

    source = build_engine(f"sqlite+pysqlite:///{source_path}")
    target = build_engine(target_url)
    try:
        report = transfer_portal_state(source, target)
        _write_report(report, args.output)
        return 0
    finally:
        source.dispose()
        target.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
