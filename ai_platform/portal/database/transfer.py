from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, Table, func, inspect, select, text

from ai_platform.portal.control_plane.database import Base, build_engine
from ai_platform.portal.database.model_registry import load_portal_models
from ai_platform.portal.database.schema import (
    INITIAL_SCHEMA_REVISION,
    MIGRATION_TABLE_NAME,
    OIDC_LOGOUT_REPLAY_TABLE_NAME,
    assert_schema_ready,
    scan_database_integrity,
    schema_status,
)


class PortalStateTransferError(RuntimeError):
    pass


# Frozen from the real authoritative public Portal SQLite snapshot on Synology
# and its deployed source revision 0e7825bf860cd8011e1bd9207fcb0765baf8d52a.
# This is deliberately an exact historical profile, not a generic old-schema
# escape hatch. Any extra/missing table, extra structural drift, or target
# revision change requires explicit revalidation and fails closed.
PUBLIC_OIDC_V1_UNVERSIONED_TABLES = frozenset(
    {
        "portal_audit_events",
        "portal_bot_config_revisions",
        "portal_bots",
        "portal_identity_audit_events",
        "portal_identity_principals",
        "portal_identity_sessions",
        "portal_oidc_login_flows",
        "portal_outbox_events",
        "portal_session_revocations",
        "portal_tenant_memberships",
    }
)
PUBLIC_OIDC_V1_MISSING_TABLES = frozenset(
    {
        "portal_bot_command_history",
        "portal_bot_command_idempotency_conflicts",
        "portal_bot_commands",
        "portal_bot_rollouts",
        "portal_command_idempotency",
        "portal_decision_snapshots",
        "portal_event_inbox",
        "portal_execution_submissions",
        "portal_grid_bot_configs",
        "portal_inference_drift_assessments",
        "portal_inference_telemetry_source_status",
        "portal_inference_telemetry_windows",
        "portal_learning_candidates",
        "portal_learning_experiments",
        "portal_learning_hypotheses",
        "portal_model_promotion_history",
        "portal_model_promotion_slots",
        "portal_model_versions",
        "portal_notification_preferences",
        "portal_oidc_logout_replays",
        "portal_operational_orders",
        "portal_operational_positions",
        "portal_operational_source_status",
        "portal_operational_trades",
        "portal_risk_decisions",
        "portal_risk_kill_switches",
        "portal_risk_policies",
        "portal_runtime_generation_observations",
        "portal_runtime_generations",
        "portal_signal_events",
        "portal_signal_wizard_previews",
        "portal_signal_wizard_submissions",
        "portal_strategy_lab_experiments",
        "portal_trade_analyses",
        "portal_trade_intents",
        "portal_trade_outcomes",
    }
)
PUBLIC_OIDC_V1_CHANGED_TABLES = frozenset(
    {
        "portal_bot_config_revisions",
        "portal_bots",
        "portal_identity_sessions",
        "portal_tenant_memberships",
    }
)
PUBLIC_OIDC_V1_MISSING_BOT_COLUMNS = frozenset(
    {
        "latest_authored_revision_id",
        "desired_revision_id",
        "desired_runtime_generation_id",
        "observed_runtime_generation_id",
        "state_version",
    }
)
PUBLIC_OIDC_V1_SUPPORTED_TARGET_REVISION = "20260809_04_runtime_isolation_binding"
PUBLIC_OIDC_V1_AUTHORITY = "unversioned_public_oidc_v1"


def _manifest_tables() -> tuple[Table, ...]:
    manifest = load_portal_models()
    return tuple(
        table
        for table in Base.metadata.sorted_tables
        if table.name in manifest and table.name != MIGRATION_TABLE_NAME
    )


def _without_named(items: list[dict[str, Any]], names: frozenset[str]) -> list[dict[str, Any]]:
    return [item for item in items if item.get("name") not in names]


def _public_oidc_v1_actual_from_current_expected(
    table_name: str,
    expected: dict[str, Any],
) -> dict[str, Any]:
    historical = copy.deepcopy(expected)
    if table_name == "portal_bots":
        historical["columns"] = [
            column
            for column in historical["columns"]
            if column["name"] not in PUBLIC_OIDC_V1_MISSING_BOT_COLUMNS
        ]
        historical["checks"] = _without_named(
            historical["checks"],
            frozenset({"ck_portal_bots_current_revision_positive"}),
        )
    elif table_name == "portal_bot_config_revisions":
        historical["checks"] = _without_named(
            historical["checks"],
            frozenset({"ck_portal_bot_config_revision_positive"}),
        )
        historical["foreign_keys"] = _without_named(
            historical["foreign_keys"],
            frozenset({"fk_portal_revision_bot"}),
        )
    elif table_name == "portal_tenant_memberships":
        historical["checks"] = _without_named(
            historical["checks"],
            frozenset({"ck_portal_membership_version_positive"}),
        )
        historical["foreign_keys"] = _without_named(
            historical["foreign_keys"],
            frozenset({"fk_portal_membership_principal"}),
        )
        historical["unique_constraints"] = _without_named(
            historical["unique_constraints"],
            frozenset({"uq_portal_membership_identity"}),
        )
    elif table_name == "portal_identity_sessions":
        historical["checks"] = _without_named(
            historical["checks"],
            frozenset({"ck_portal_session_membership_version_positive"}),
        )
        historical["foreign_keys"] = _without_named(
            historical["foreign_keys"],
            frozenset({"fk_portal_session_membership_identity"}),
        )
    else:
        raise PortalStateTransferError(
            "deployed public SQLite structural profile contains an unreviewed changed table"
        )
    return historical


def _matches_public_oidc_v1(
    status: dict[str, Any],
    source_tables: frozenset[str],
) -> bool:
    differences = status["differences"]
    if status["applied_revisions"]:
        return False
    if source_tables != PUBLIC_OIDC_V1_UNVERSIONED_TABLES:
        return False
    if frozenset(differences["missing_tables"]) != PUBLIC_OIDC_V1_MISSING_TABLES:
        return False
    if differences["unexpected_tables"]:
        return False
    changed_tables = differences["changed_tables"]
    if frozenset(changed_tables) != PUBLIC_OIDC_V1_CHANGED_TABLES:
        return False
    return all(
        changed_tables[table_name]["actual"]
        == _public_oidc_v1_actual_from_current_expected(
            table_name,
            changed_tables[table_name]["expected"],
        )
        for table_name in PUBLIC_OIDC_V1_CHANGED_TABLES
    )


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
        elif _matches_public_oidc_v1(status, source_tables):
            authority = PUBLIC_OIDC_V1_AUTHORITY
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
                "legacy SQLite schema is divergent; backup, quarantine and explicit "
                "recovery are required"
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


def _assert_transfer_target_revision(authority: str, target_status: dict[str, Any]) -> None:
    if authority != PUBLIC_OIDC_V1_AUTHORITY:
        return
    expected_revision = target_status.get("expected_revision", {}).get("revision_id")
    if expected_revision != PUBLIC_OIDC_V1_SUPPORTED_TARGET_REVISION:
        raise PortalStateTransferError(
            "deployed public SQLite transfer target revision requires explicit revalidation"
        )


def _missing_table_is_transferable(authority: str, table_name: str) -> bool:
    if authority == "structural_pre_logout_replay":
        return table_name == OIDC_LOGOUT_REPLAY_TABLE_NAME
    if authority == PUBLIC_OIDC_V1_AUTHORITY:
        return table_name in PUBLIC_OIDC_V1_MISSING_TABLES
    return False


def _source_rows(source_connection: Any, table: Table) -> Any:
    source_column_names = {
        column["name"] for column in inspect(source_connection).get_columns(table.name)
    }
    selected_columns = [column for column in table.columns if column.name in source_column_names]
    if not selected_columns:
        raise PortalStateTransferError(
            f"legacy SQLite source table {table.name} has no transferable columns"
        )
    return source_connection.execute(select(*selected_columns)).mappings()


def _backfill_public_oidc_v1_target(target_connection: Any) -> None:
    """Reproduce the canonical runtime-generation migration for historical Bot rows."""

    target_connection.execute(
        text(
            """
            UPDATE portal_bots
               SET latest_authored_revision_id = (
                   SELECT revision.revision_id
                     FROM portal_bot_config_revisions revision
                    WHERE revision.tenant_id = portal_bots.tenant_id
                      AND revision.bot_id = portal_bots.bot_id
                      AND revision.revision = portal_bots.current_revision
               )
             WHERE latest_authored_revision_id IS NULL
            """
        )
    )
    target_connection.execute(
        text("UPDATE portal_bots SET state_version = 1 WHERE state_version IS NULL")
    )


def _copy_source_tables(
    authority: str,
    source_tables: frozenset[str],
    source_connection: Any,
    target_connection: Any,
) -> dict[str, int]:
    copied_counts: dict[str, int] = {}
    for table in _manifest_tables():
        if table.name not in source_tables:
            if _missing_table_is_transferable(authority, table.name):
                copied_counts[table.name] = 0
                continue
            raise PortalStateTransferError(
                f"legacy SQLite source is missing required table {table.name}"
            )
        result = _source_rows(source_connection, table)
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

    if authority == PUBLIC_OIDC_V1_AUTHORITY:
        _backfill_public_oidc_v1_target(target_connection)
    _reset_postgresql_sequences(target_connection)
    return copied_counts


def _verify_copied_counts(target_connection: Any, copied_counts: dict[str, int]) -> None:
    for table in _manifest_tables():
        target_count = int(
            target_connection.execute(select(func.count()).select_from(table)).scalar_one()
        )
        if target_count != copied_counts[table.name]:
            raise PortalStateTransferError(
                "PostgreSQL row-count verification failed during state transfer"
            )


def transfer_portal_state(source: Engine, target: Engine) -> dict[str, Any]:
    if target.dialect.name != "postgresql":
        raise PortalStateTransferError("Portal state transfer target must be PostgreSQL")

    authority, source_status, source_tables = _source_authority(source)
    target_status = assert_schema_ready(target)
    _assert_transfer_target_revision(authority, target_status)
    existing_target_counts = _target_row_counts(target)
    nonempty_target = {
        table_name: row_count
        for table_name, row_count in sorted(existing_target_counts.items())
        if row_count
    }
    if nonempty_target:
        raise PortalStateTransferError(
            "target PostgreSQL contains Portal business rows; refusing non-idempotent state "
            f"transfer; nonempty_table_counts={json.dumps(nonempty_target, sort_keys=True)}"
        )

    with source.connect() as source_connection, target.begin() as target_connection:
        copied_counts = _copy_source_tables(
            authority,
            source_tables,
            source_connection,
            target_connection,
        )
        _verify_copied_counts(target_connection, copied_counts)

    target_integrity = scan_database_integrity(target)
    if target_integrity["status"] != "clean":
        raise PortalStateTransferError(
            "PostgreSQL integrity verification failed after state transfer"
        )

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
        "schema_metadata_transfer": "excluded_dialect_specific_authority",
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
