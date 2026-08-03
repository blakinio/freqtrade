from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Engine,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    inspect,
    select,
    text,
)
from sqlalchemy.sql.schema import CheckConstraint

from ai_platform.portal.control_plane.database import Base
from ai_platform.portal.database.model_registry import load_portal_models


EXPECTED_SCHEMA_REVISION = "20260803_01_portal_authoritative"
MIGRATION_TABLE_NAME = "portal_schema_migrations"
_POSTGRES_MIGRATION_LOCK_ID = 1_122_202_608_03

_migration_metadata = MetaData()
_schema_migrations = Table(
    MIGRATION_TABLE_NAME,
    _migration_metadata,
    Column("sequence", Integer, primary_key=True),
    Column("revision_id", String(128), nullable=False, unique=True),
    Column("dialect_name", String(64), nullable=False),
    Column("schema_fingerprint", String(64), nullable=False),
    Column("applied_at", DateTime(timezone=True), nullable=False),
)


@dataclass(frozen=True)
class HardRelation:
    name: str
    child_table: str
    parent_table: str
    orphan_count_sql: str


_HARD_RELATIONS = (
    HardRelation(
        name="bot_config_revision_to_bot",
        child_table="portal_bot_config_revisions",
        parent_table="portal_bots",
        orphan_count_sql="""
            SELECT COUNT(*)
            FROM portal_bot_config_revisions child
            LEFT JOIN portal_bots parent
              ON parent.tenant_id = child.tenant_id
             AND parent.bot_id = child.bot_id
            WHERE parent.bot_id IS NULL
        """,
    ),
    HardRelation(
        name="membership_to_principal",
        child_table="portal_tenant_memberships",
        parent_table="portal_identity_principals",
        orphan_count_sql="""
            SELECT COUNT(*)
            FROM portal_tenant_memberships child
            LEFT JOIN portal_identity_principals parent
              ON parent.principal_id = child.principal_id
            WHERE parent.principal_id IS NULL
        """,
    ),
    HardRelation(
        name="session_to_membership_identity",
        child_table="portal_identity_sessions",
        parent_table="portal_tenant_memberships",
        orphan_count_sql="""
            SELECT COUNT(*)
            FROM portal_identity_sessions child
            LEFT JOIN portal_tenant_memberships parent
              ON parent.membership_id = child.membership_id
             AND parent.principal_id = child.principal_id
            WHERE parent.membership_id IS NULL
        """,
    ),
    HardRelation(
        name="risk_decision_to_trade_intent",
        child_table="portal_risk_decisions",
        parent_table="portal_trade_intents",
        orphan_count_sql="""
            SELECT COUNT(*)
            FROM portal_risk_decisions child
            LEFT JOIN portal_trade_intents parent
              ON parent.tenant_id = child.tenant_id
             AND parent.trade_intent_id = child.trade_intent_id
            WHERE parent.trade_intent_id IS NULL
        """,
    ),
    HardRelation(
        name="model_slot_to_model_version",
        child_table="portal_model_promotion_slots",
        parent_table="portal_model_versions",
        orphan_count_sql="""
            SELECT COUNT(*)
            FROM portal_model_promotion_slots child
            LEFT JOIN portal_model_versions parent
              ON parent.tenant_id = child.tenant_id
             AND parent.model_version_id = child.current_model_version_id
            WHERE parent.model_version_id IS NULL
        """,
    ),
    HardRelation(
        name="bot_command_history_to_command",
        child_table="portal_bot_command_history",
        parent_table="portal_bot_commands",
        orphan_count_sql="""
            SELECT COUNT(*)
            FROM portal_bot_command_history child
            LEFT JOIN portal_bot_commands parent
              ON parent.scope_tenant_id = child.scope_tenant_id
             AND parent.command_id = child.command_id
            WHERE parent.command_id IS NULL
        """,
    ),
    HardRelation(
        name="bot_conflict_to_existing_command",
        child_table="portal_bot_command_idempotency_conflicts",
        parent_table="portal_bot_commands",
        orphan_count_sql="""
            SELECT COUNT(*)
            FROM portal_bot_command_idempotency_conflicts child
            LEFT JOIN portal_bot_commands parent
              ON parent.scope_tenant_id = child.scope_tenant_id
             AND parent.command_id = child.existing_command_id
            WHERE parent.command_id IS NULL
        """,
    ),
)


class SchemaMigrationError(RuntimeError):
    def __init__(self, message: str, report: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.report = report or {}


class SchemaReadinessError(SchemaMigrationError):
    pass


class UnversionedSchemaError(SchemaMigrationError):
    pass


def _canonical_sql(value: object | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", str(value).strip()).lower()


def _type_token(column_type: Any, dialect: Any) -> str:
    try:
        compiled = column_type.compile(dialect=dialect)
    except Exception:
        compiled = str(column_type)
    return re.sub(r"\s+", " ", str(compiled).strip()).upper()


def _expected_table_snapshot(table: Table, dialect: Any) -> dict[str, Any]:
    primary_key = [column.name for column in table.primary_key.columns]
    primary_key_set = set(primary_key)
    columns = [
        {
            "name": column.name,
            "type": _type_token(column.type, dialect),
            "nullable": False if column.name in primary_key_set else bool(column.nullable),
            "default": _canonical_sql(
                None if column.server_default is None else column.server_default.arg
            ),
        }
        for column in table.columns
    ]
    unique_constraints: list[dict[str, Any]] = []
    foreign_keys: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            unique_constraints.append(
                {
                    "name": constraint.name,
                    "columns": [column.name for column in constraint.columns],
                }
            )
        elif isinstance(constraint, ForeignKeyConstraint):
            foreign_keys.append(
                {
                    "name": constraint.name,
                    "columns": [column.name for column in constraint.columns],
                    "referred_table": next(
                        iter(constraint.elements)
                    ).column.table.name,
                    "referred_columns": [
                        element.column.name for element in constraint.elements
                    ],
                    "ondelete": next(
                        (
                            element.ondelete
                            for element in constraint.elements
                            if element.ondelete is not None
                        ),
                        None,
                    ),
                }
            )
        elif isinstance(constraint, CheckConstraint):
            checks.append(
                {
                    "name": constraint.name,
                    "sql": _canonical_sql(constraint.sqltext),
                }
            )
    indexes = [
        {
            "name": index.name,
            "columns": [
                getattr(expression, "name", str(expression))
                for expression in index.expressions
            ],
            "unique": bool(index.unique),
        }
        for index in table.indexes
    ]
    return {
        "columns": columns,
        "primary_key": primary_key,
        "unique_constraints": sorted(
            unique_constraints,
            key=lambda item: (item["name"] or "", tuple(item["columns"])),
        ),
        "foreign_keys": sorted(
            foreign_keys,
            key=lambda item: (item["name"] or "", tuple(item["columns"])),
        ),
        "checks": sorted(checks, key=lambda item: (item["name"] or "", item["sql"] or "")),
        "indexes": sorted(indexes, key=lambda item: (item["name"] or "", tuple(item["columns"]))),
    }


def _expected_snapshot(engine: Engine) -> dict[str, Any]:
    load_portal_models()
    return {
        table.name: _expected_table_snapshot(table, engine.dialect)
        for table in sorted(Base.metadata.tables.values(), key=lambda item: item.name)
    }


def _actual_table_snapshot(connection: Any, table_name: str) -> dict[str, Any]:
    inspector = inspect(connection)
    primary_key = list(
        (inspector.get_pk_constraint(table_name) or {}).get("constrained_columns") or []
    )
    primary_key_set = set(primary_key)
    columns = [
        {
            "name": column["name"],
            "type": _type_token(column["type"], connection.dialect),
            "nullable": False
            if column["name"] in primary_key_set
            else bool(column.get("nullable", True)),
            "default": _canonical_sql(column.get("default")),
        }
        for column in inspector.get_columns(table_name)
    ]
    unique_constraints = [
        {
            "name": constraint.get("name"),
            "columns": list(constraint.get("column_names") or []),
        }
        for constraint in inspector.get_unique_constraints(table_name)
        if constraint.get("column_names")
    ]
    foreign_keys = [
        {
            "name": constraint.get("name"),
            "columns": list(constraint.get("constrained_columns") or []),
            "referred_table": constraint.get("referred_table"),
            "referred_columns": list(constraint.get("referred_columns") or []),
            "ondelete": (constraint.get("options") or {}).get("ondelete"),
        }
        for constraint in inspector.get_foreign_keys(table_name)
    ]
    try:
        reflected_checks = inspector.get_check_constraints(table_name)
    except NotImplementedError:
        reflected_checks = []
    checks = [
        {
            "name": constraint.get("name"),
            "sql": _canonical_sql(constraint.get("sqltext")),
        }
        for constraint in reflected_checks
    ]
    indexes = [
        {
            "name": index.get("name"),
            "columns": list(index.get("column_names") or []),
            "unique": bool(index.get("unique")),
        }
        for index in inspector.get_indexes(table_name)
        if not index.get("duplicates_constraint") and index.get("column_names")
    ]
    return {
        "columns": columns,
        "primary_key": primary_key,
        "unique_constraints": sorted(
            unique_constraints,
            key=lambda item: (item["name"] or "", tuple(item["columns"])),
        ),
        "foreign_keys": sorted(
            foreign_keys,
            key=lambda item: (item["name"] or "", tuple(item["columns"])),
        ),
        "checks": sorted(checks, key=lambda item: (item["name"] or "", item["sql"] or "")),
        "indexes": sorted(indexes, key=lambda item: (item["name"] or "", tuple(item["columns"]))),
    }


def _actual_snapshot(connection: Any) -> dict[str, Any]:
    inspector = inspect(connection)
    table_names = sorted(
        table_name
        for table_name in inspector.get_table_names()
        if table_name.startswith("portal_") and table_name != MIGRATION_TABLE_NAME
    )
    return {
        table_name: _actual_table_snapshot(connection, table_name)
        for table_name in table_names
    }


def _fingerprint(snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _snapshot_differences(
    expected: dict[str, Any], actual: dict[str, Any]
) -> dict[str, Any]:
    missing_tables = sorted(set(expected) - set(actual))
    unexpected_tables = sorted(set(actual) - set(expected))
    changed_tables = {
        table_name: {
            "expected": expected[table_name],
            "actual": actual[table_name],
        }
        for table_name in sorted(set(expected) & set(actual))
        if expected[table_name] != actual[table_name]
    }
    return {
        "missing_tables": missing_tables,
        "unexpected_tables": unexpected_tables,
        "changed_tables": changed_tables,
    }


def _revision_rows(connection: Any) -> list[dict[str, Any]]:
    if MIGRATION_TABLE_NAME not in inspect(connection).get_table_names():
        return []
    rows = connection.execute(
        select(
            _schema_migrations.c.sequence,
            _schema_migrations.c.revision_id,
            _schema_migrations.c.dialect_name,
            _schema_migrations.c.schema_fingerprint,
            _schema_migrations.c.applied_at,
        ).order_by(_schema_migrations.c.sequence)
    ).mappings()
    return [
        {
            "sequence": row["sequence"],
            "revision_id": row["revision_id"],
            "dialect_name": row["dialect_name"],
            "schema_fingerprint": row["schema_fingerprint"],
            "applied_at": row["applied_at"].isoformat()
            if row["applied_at"] is not None
            else None,
        }
        for row in rows
    ]


def _schema_status_connection(connection: Any, engine: Engine) -> dict[str, Any]:
    expected = _expected_snapshot(engine)
    actual = _actual_snapshot(connection)
    expected_fingerprint = _fingerprint(expected)
    actual_fingerprint = _fingerprint(actual)
    differences = _snapshot_differences(expected, actual)
    revisions = _revision_rows(connection)
    expected_revision = {
        "sequence": 1,
        "revision_id": EXPECTED_SCHEMA_REVISION,
        "dialect_name": engine.dialect.name,
        "schema_fingerprint": expected_fingerprint,
    }
    revision_matches = len(revisions) == 1 and all(
        revisions[0].get(key) == value for key, value in expected_revision.items()
    )
    sqlite_foreign_keys: bool | None = None
    if engine.dialect.name == "sqlite":
        sqlite_foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
    schema_matches = not any(
        (
            differences["missing_tables"],
            differences["unexpected_tables"],
            differences["changed_tables"],
        )
    )
    ready = revision_matches and schema_matches and sqlite_foreign_keys is not False
    return {
        "status": "ready" if ready else "not_ready",
        "expected_revision": expected_revision,
        "applied_revisions": revisions,
        "expected_schema_fingerprint": expected_fingerprint,
        "actual_schema_fingerprint": actual_fingerprint,
        "differences": differences,
        "sqlite_foreign_keys": sqlite_foreign_keys,
        "safety": {
            "secret_values_recorded": False,
            "protected_production_mutated": False,
            "live_capital_authorized": False,
        },
    }


def schema_status(engine: Engine) -> dict[str, Any]:
    with engine.connect() as connection:
        return _schema_status_connection(connection, engine)


def assert_schema_ready(engine: Engine) -> dict[str, Any]:
    report = schema_status(engine)
    if report["status"] != "ready":
        raise SchemaReadinessError("Portal schema is not at the expected revision", report)
    return report


def _acquire_migration_lock(connection: Any, engine: Engine) -> None:
    if engine.dialect.name == "postgresql":
        connection.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": _POSTGRES_MIGRATION_LOCK_ID},
        )


def scan_database_integrity(engine: Engine) -> dict[str, Any]:
    with engine.connect() as connection:
        table_names = set(inspect(connection).get_table_names())
        relations: dict[str, Any] = {}
        for relation in _HARD_RELATIONS:
            if relation.child_table not in table_names or relation.parent_table not in table_names:
                relations[relation.name] = {
                    "status": "not_applicable",
                    "orphan_count": None,
                }
                continue
            orphan_count = int(
                connection.execute(text(relation.orphan_count_sql)).scalar_one()
            )
            relations[relation.name] = {
                "status": "clean" if orphan_count == 0 else "orphaned",
                "orphan_count": orphan_count,
            }
        clean = all(
            item["orphan_count"] in {None, 0} for item in relations.values()
        )
        return {
            "status": "clean" if clean else "quarantine_required",
            "relations": relations,
            "policy": "fail_closed_no_reassignment_no_deletion",
            "safety": {
                "row_values_recorded": False,
                "secret_values_recorded": False,
                "protected_production_mutated": False,
                "live_capital_authorized": False,
            },
        }


def migrate_database(engine: Engine) -> dict[str, Any]:
    expected = _expected_snapshot(engine)
    expected_fingerprint = _fingerprint(expected)
    with engine.begin() as connection:
        _acquire_migration_lock(connection, engine)
        inspector = inspect(connection)
        table_names = set(inspector.get_table_names())
        revision_table_exists = MIGRATION_TABLE_NAME in table_names
        existing_portal_tables = sorted(
            table_name
            for table_name in table_names
            if table_name.startswith("portal_") and table_name != MIGRATION_TABLE_NAME
        )
        if not revision_table_exists:
            if existing_portal_tables:
                report = {
                    "status": "unversioned_schema",
                    "existing_portal_tables": existing_portal_tables,
                    "integrity_scan": scan_database_integrity(engine),
                    "policy": "backup_scan_quarantine_rebuild_restore_validate",
                }
                raise UnversionedSchemaError(
                    "Existing Portal tables have no authoritative schema revision",
                    report,
                )
            _schema_migrations.create(connection, checkfirst=False)
        revisions = _revision_rows(connection)
        if revisions:
            report = _schema_status_connection(connection, engine)
            if report["status"] != "ready":
                raise SchemaMigrationError(
                    "Applied Portal schema revision is divergent or unknown",
                    report,
                )
            return report
        partial_tables = sorted(
            table_name
            for table_name in inspect(connection).get_table_names()
            if table_name.startswith("portal_") and table_name != MIGRATION_TABLE_NAME
        )
        if partial_tables:
            raise SchemaMigrationError(
                "Partial unversioned Portal schema detected",
                {
                    "status": "partial_unversioned_schema",
                    "existing_portal_tables": partial_tables,
                    "policy": "fail_closed_restore_last_known_backup",
                },
            )
        for table in Base.metadata.sorted_tables:
            table.create(connection, checkfirst=False)
        connection.execute(
            _schema_migrations.insert().values(
                sequence=1,
                revision_id=EXPECTED_SCHEMA_REVISION,
                dialect_name=engine.dialect.name,
                schema_fingerprint=expected_fingerprint,
                applied_at=datetime.now(timezone.utc),
            )
        )
    return assert_schema_ready(engine)
