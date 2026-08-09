from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Engine,
    ForeignKeyConstraint,
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


INITIAL_SCHEMA_REVISION = "20260803_01_portal_authoritative"
OIDC_SCHEMA_REVISION = "20260805_02_oidc_logout_replay"
EXPECTED_SCHEMA_REVISION = "20260808_03_runtime_generation_state"
MIGRATION_TABLE_NAME = "portal_schema_migrations"
OIDC_LOGOUT_REPLAY_TABLE_NAME = "portal_oidc_logout_replays"
RUNTIME_GENERATION_TABLE_NAMES = frozenset(
    {
        "portal_runtime_generations",
        "portal_runtime_generation_observations",
        "portal_bot_rollouts",
        "portal_command_idempotency",
    }
)
BOT_RUNTIME_STATE_COLUMNS = frozenset(
    {
        "latest_authored_revision_id",
        "desired_revision_id",
        "desired_runtime_generation_id",
        "observed_runtime_generation_id",
        "state_version",
    }
)
_POSTGRES_MIGRATION_LOCK_ID = 1_122_202_608_03
_POSTGRES_STRING_CAST_RE = re.compile(r"::(?:character varying|varchar|text)(?:\[\])?")
_POSTGRES_ANY_ARRAY_RE = re.compile(
    r"\b(?P<column>[a-z_][a-z0-9_]*)\s*=\s*any\s*"
    r"\(\s*array\[(?P<values>[^\]]+)\]\s*\)"
)

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
        "bot_config_revision_to_bot",
        "portal_bot_config_revisions",
        "portal_bots",
        """
        SELECT COUNT(*)
        FROM portal_bot_config_revisions child
        LEFT JOIN portal_bots parent
          ON parent.tenant_id = child.tenant_id
         AND parent.bot_id = child.bot_id
        WHERE parent.bot_id IS NULL
        """,
    ),
    HardRelation(
        "runtime_generation_to_bot",
        "portal_runtime_generations",
        "portal_bots",
        """
        SELECT COUNT(*)
        FROM portal_runtime_generations child
        LEFT JOIN portal_bots parent
          ON parent.tenant_id = child.tenant_id
         AND parent.bot_id = child.bot_id
        WHERE parent.bot_id IS NULL
        """,
    ),
    HardRelation(
        "rollout_to_generation",
        "portal_bot_rollouts",
        "portal_runtime_generations",
        """
        SELECT COUNT(*)
        FROM portal_bot_rollouts child
        LEFT JOIN portal_runtime_generations parent
          ON parent.generation_id = child.to_generation_id
        WHERE parent.generation_id IS NULL
        """,
    ),
    HardRelation(
        "runtime_observation_to_generation",
        "portal_runtime_generation_observations",
        "portal_runtime_generations",
        """
        SELECT COUNT(*)
        FROM portal_runtime_generation_observations child
        LEFT JOIN portal_runtime_generations parent
          ON parent.generation_id = child.generation_id
        WHERE parent.generation_id IS NULL
        """,
    ),
    HardRelation(
        "membership_to_principal",
        "portal_tenant_memberships",
        "portal_identity_principals",
        """
        SELECT COUNT(*)
        FROM portal_tenant_memberships child
        LEFT JOIN portal_identity_principals parent
          ON parent.principal_id = child.principal_id
        WHERE parent.principal_id IS NULL
        """,
    ),
    HardRelation(
        "session_to_membership_identity",
        "portal_identity_sessions",
        "portal_tenant_memberships",
        """
        SELECT COUNT(*)
        FROM portal_identity_sessions child
        LEFT JOIN portal_tenant_memberships parent
          ON parent.membership_id = child.membership_id
         AND parent.principal_id = child.principal_id
        WHERE parent.membership_id IS NULL
        """,
    ),
    HardRelation(
        "risk_decision_to_trade_intent",
        "portal_risk_decisions",
        "portal_trade_intents",
        """
        SELECT COUNT(*)
        FROM portal_risk_decisions child
        LEFT JOIN portal_trade_intents parent
          ON parent.tenant_id = child.tenant_id
         AND parent.trade_intent_id = child.trade_intent_id
        WHERE parent.trade_intent_id IS NULL
        """,
    ),
    HardRelation(
        "model_slot_to_model_version",
        "portal_model_promotion_slots",
        "portal_model_versions",
        """
        SELECT COUNT(*)
        FROM portal_model_promotion_slots child
        LEFT JOIN portal_model_versions parent
          ON parent.tenant_id = child.tenant_id
         AND parent.model_version_id = child.current_model_version_id
        WHERE parent.model_version_id IS NULL
        """,
    ),
    HardRelation(
        "bot_command_history_to_command",
        "portal_bot_command_history",
        "portal_bot_commands",
        """
        SELECT COUNT(*)
        FROM portal_bot_command_history child
        LEFT JOIN portal_bot_commands parent
          ON parent.scope_tenant_id = child.scope_tenant_id
         AND parent.command_id = child.command_id
        WHERE parent.command_id IS NULL
        """,
    ),
    HardRelation(
        "bot_conflict_to_existing_command",
        "portal_bot_command_idempotency_conflicts",
        "portal_bot_commands",
        """
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
    normalized = re.sub(r"\s+", " ", str(value).strip()).lower()
    while normalized.startswith("(") and normalized.endswith(")"):
        normalized = normalized[1:-1].strip()
    return normalized


def _canonical_check_sql(value: object | None) -> str | None:
    normalized = _canonical_sql(value)
    if normalized is None:
        return None
    normalized = _POSTGRES_STRING_CAST_RE.sub("", normalized)
    normalized = _POSTGRES_ANY_ARRAY_RE.sub(
        lambda match: f"{match.group('column')} in ({match.group('values')})",
        normalized,
    )
    normalized = normalized.replace(") or (", " or ")
    return re.sub(r"\s+", " ", normalized).strip()


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
                None
                if column.server_default is None
                else getattr(column.server_default, "arg", column.server_default)
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
            elements = list(constraint.elements)
            foreign_keys.append(
                {
                    "name": constraint.name,
                    "columns": [column.name for column in constraint.columns],
                    "referred_table": elements[0].column.table.name,
                    "referred_columns": [element.column.name for element in elements],
                    "ondelete": next(
                        (
                            element.ondelete.upper()
                            for element in elements
                            if element.ondelete is not None
                        ),
                        None,
                    ),
                }
            )
        elif isinstance(constraint, CheckConstraint):
            checks.append(
                {"name": constraint.name, "sql": _canonical_check_sql(constraint.sqltext)}
            )
    indexes = [
        {
            "name": index.name,
            "columns": [
                getattr(expression, "name", str(expression)) for expression in index.expressions
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
        "checks": sorted(
            checks,
            key=lambda item: (item["name"] or "", item["sql"] or ""),
        ),
        "indexes": sorted(
            indexes,
            key=lambda item: (item["name"] or "", tuple(item["columns"])),
        ),
    }


def _manifest_tables() -> tuple[Table, ...]:
    manifest = load_portal_models()
    ordered = tuple(table for table in Base.metadata.sorted_tables if table.name in manifest)
    ordered_names = {table.name for table in ordered}
    if ordered_names != set(manifest):
        raise RuntimeError(
            "Portal table manifest and SQLAlchemy dependency order differ: "
            f"missing={sorted(set(manifest) - ordered_names)}"
        )
    return ordered


def _expected_snapshot(engine: Engine) -> dict[str, Any]:
    return {
        table.name: _expected_table_snapshot(table, engine.dialect) for table in _manifest_tables()
    }


def _pre_runtime_generation_snapshot(engine: Engine) -> dict[str, Any]:
    snapshot = _expected_snapshot(engine)
    for table_name in RUNTIME_GENERATION_TABLE_NAMES:
        if table_name not in snapshot:
            raise RuntimeError(f"Runtime generation table is missing from manifest: {table_name}")
        snapshot.pop(table_name)
    bot_snapshot = snapshot.get("portal_bots")
    if bot_snapshot is None:
        raise RuntimeError("portal_bots is missing from the Portal model manifest")
    bot_snapshot["columns"] = [
        column
        for column in bot_snapshot["columns"]
        if column["name"] not in BOT_RUNTIME_STATE_COLUMNS
    ]
    return snapshot


def _initial_snapshot(engine: Engine) -> dict[str, Any]:
    snapshot = _pre_runtime_generation_snapshot(engine)
    if OIDC_LOGOUT_REPLAY_TABLE_NAME not in snapshot:
        raise RuntimeError("OIDC logout replay table is missing from the Portal model manifest")
    return {
        table_name: table_snapshot
        for table_name, table_snapshot in snapshot.items()
        if table_name != OIDC_LOGOUT_REPLAY_TABLE_NAME
    }


def _expected_revision_chain(engine: Engine) -> list[dict[str, Any]]:
    initial = _initial_snapshot(engine)
    oidc = _pre_runtime_generation_snapshot(engine)
    current = _expected_snapshot(engine)
    return [
        {
            "sequence": 1,
            "revision_id": INITIAL_SCHEMA_REVISION,
            "dialect_name": engine.dialect.name,
            "schema_fingerprint": _fingerprint(initial),
        },
        {
            "sequence": 2,
            "revision_id": OIDC_SCHEMA_REVISION,
            "dialect_name": engine.dialect.name,
            "schema_fingerprint": _fingerprint(oidc),
        },
        {
            "sequence": 3,
            "revision_id": EXPECTED_SCHEMA_REVISION,
            "dialect_name": engine.dialect.name,
            "schema_fingerprint": _fingerprint(current),
        },
    ]


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
            "ondelete": (
                str((constraint.get("options") or {}).get("ondelete")).upper()
                if (constraint.get("options") or {}).get("ondelete") is not None
                else None
            ),
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
            "sql": _canonical_check_sql(constraint.get("sqltext")),
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
        "checks": sorted(
            checks,
            key=lambda item: (item["name"] or "", item["sql"] or ""),
        ),
        "indexes": sorted(
            indexes,
            key=lambda item: (item["name"] or "", tuple(item["columns"])),
        ),
    }


def _actual_snapshot(connection: Any) -> dict[str, Any]:
    table_names = sorted(
        table_name
        for table_name in inspect(connection).get_table_names()
        if table_name.startswith("portal_") and table_name != MIGRATION_TABLE_NAME
    )
    return {
        table_name: _actual_table_snapshot(connection, table_name) for table_name in table_names
    }


def _fingerprint(snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _snapshot_differences(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    common = sorted(set(expected) & set(actual))
    return {
        "missing_tables": sorted(set(expected) - set(actual)),
        "unexpected_tables": sorted(set(actual) - set(expected)),
        "changed_tables": {
            table_name: {
                "expected": expected[table_name],
                "actual": actual[table_name],
            }
            for table_name in common
            if expected[table_name] != actual[table_name]
        },
    }


def _snapshot_matches(expected: dict[str, Any], actual: dict[str, Any]) -> bool:
    differences = _snapshot_differences(expected, actual)
    return not any(
        (
            differences["missing_tables"],
            differences["unexpected_tables"],
            differences["changed_tables"],
        )
    )


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
            "applied_at": (
                row["applied_at"].isoformat() if row["applied_at"] is not None else None
            ),
        }
        for row in rows
    ]


def _revisions_match(
    revisions: list[dict[str, Any]],
    expected_revisions: list[dict[str, Any]],
) -> bool:
    if len(revisions) != len(expected_revisions):
        return False
    return all(
        all(actual.get(key) == value for key, value in expected.items())
        for actual, expected in zip(revisions, expected_revisions, strict=True)
    )


def _schema_status_connection(connection: Any, engine: Engine) -> dict[str, Any]:
    expected = _expected_snapshot(engine)
    actual = _actual_snapshot(connection)
    expected_fingerprint = _fingerprint(expected)
    actual_fingerprint = _fingerprint(actual)
    differences = _snapshot_differences(expected, actual)
    revisions = _revision_rows(connection)
    expected_revisions = _expected_revision_chain(engine)
    expected_revision = expected_revisions[-1]
    revision_matches = _revisions_match(revisions, expected_revisions)
    sqlite_foreign_keys: bool | None = None
    if engine.dialect.name == "sqlite":
        sqlite_foreign_keys = connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
    schema_matches = _snapshot_matches(expected, actual)
    ready = revision_matches and schema_matches and sqlite_foreign_keys is not False
    return {
        "status": "ready" if ready else "not_ready",
        "expected_revision": expected_revision,
        "expected_revisions": expected_revisions,
        "applied_revisions": revisions,
        "expected_schema_fingerprint": expected_fingerprint,
        "actual_schema_fingerprint": actual_fingerprint,
        "table_count": len(expected),
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


def _scan_integrity_connection(connection: Any) -> dict[str, Any]:
    table_names = set(inspect(connection).get_table_names())
    relations: dict[str, Any] = {}
    for relation in _HARD_RELATIONS:
        if relation.child_table not in table_names or relation.parent_table not in table_names:
            relations[relation.name] = {
                "status": "not_applicable",
                "orphan_count": None,
            }
            continue
        orphan_count = int(connection.execute(text(relation.orphan_count_sql)).scalar_one())
        relations[relation.name] = {
            "status": "clean" if orphan_count == 0 else "orphaned",
            "orphan_count": orphan_count,
        }
    clean = all(item["orphan_count"] in {None, 0} for item in relations.values())
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


def scan_database_integrity(engine: Engine) -> dict[str, Any]:
    with engine.connect() as connection:
        return _scan_integrity_connection(connection)


def _insert_revision(
    connection: Any,
    *,
    revision: dict[str, Any],
    applied_at: datetime,
) -> None:
    connection.execute(
        _schema_migrations.insert().values(
            sequence=revision["sequence"],
            revision_id=revision["revision_id"],
            dialect_name=revision["dialect_name"],
            schema_fingerprint=revision["schema_fingerprint"],
            applied_at=applied_at,
        )
    )


def _create_oidc_revision(
    connection: Any,
    manifest_tables: tuple[Table, ...],
    revision: dict[str, Any],
) -> None:
    replay_table = next(
        table for table in manifest_tables if table.name == OIDC_LOGOUT_REPLAY_TABLE_NAME
    )
    replay_table.create(connection, checkfirst=False)
    _insert_revision(connection, revision=revision, applied_at=datetime.now(UTC))


def _create_runtime_generation_revision(
    connection: Any,
    manifest_tables: tuple[Table, ...],
    revision: dict[str, Any],
) -> None:
    connection.exec_driver_sql(
        "ALTER TABLE portal_bots ADD COLUMN latest_authored_revision_id VARCHAR(255)"
    )
    connection.exec_driver_sql(
        "ALTER TABLE portal_bots ADD COLUMN desired_revision_id VARCHAR(255)"
    )
    connection.exec_driver_sql(
        "ALTER TABLE portal_bots ADD COLUMN desired_runtime_generation_id VARCHAR(36)"
    )
    connection.exec_driver_sql(
        "ALTER TABLE portal_bots ADD COLUMN observed_runtime_generation_id VARCHAR(36)"
    )
    connection.exec_driver_sql("ALTER TABLE portal_bots ADD COLUMN state_version INTEGER")
    connection.execute(
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
    connection.execute(text("UPDATE portal_bots SET state_version = 1 WHERE state_version IS NULL"))
    for table in manifest_tables:
        if table.name in RUNTIME_GENERATION_TABLE_NAMES:
            table.create(connection, checkfirst=False)
    _insert_revision(connection, revision=revision, applied_at=datetime.now(UTC))


def migrate_database(engine: Engine) -> dict[str, Any]:
    manifest_tables = _manifest_tables()
    expected = {
        table.name: _expected_table_snapshot(table, engine.dialect) for table in manifest_tables
    }
    initial = _initial_snapshot(engine)
    oidc = _pre_runtime_generation_snapshot(engine)
    expected_revisions = _expected_revision_chain(engine)
    with engine.begin() as connection:
        _acquire_migration_lock(connection, engine)
        table_names = set(inspect(connection).get_table_names())
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
                    "integrity_scan": _scan_integrity_connection(connection),
                    "policy": "backup_scan_quarantine_rebuild_restore_validate",
                }
                raise UnversionedSchemaError(
                    "Existing Portal tables have no authoritative schema revision",
                    report,
                )
            _schema_migrations.create(connection, checkfirst=False)

        revisions = _revision_rows(connection)
        if revisions:
            actual = _actual_snapshot(connection)
            if _revisions_match(revisions, expected_revisions) and _snapshot_matches(
                expected,
                actual,
            ):
                return _schema_status_connection(connection, engine)

            if _revisions_match(revisions, expected_revisions[:1]) and _snapshot_matches(
                initial,
                actual,
            ):
                _create_oidc_revision(
                    connection,
                    manifest_tables,
                    expected_revisions[1],
                )
                revisions = _revision_rows(connection)
                actual = _actual_snapshot(connection)

            if _revisions_match(revisions, expected_revisions[:2]) and _snapshot_matches(
                oidc,
                actual,
            ):
                _create_runtime_generation_revision(
                    connection,
                    manifest_tables,
                    expected_revisions[2],
                )
                return _schema_status_connection(connection, engine)

            report = _schema_status_connection(connection, engine)
            raise SchemaMigrationError(
                "Applied Portal schema revision is divergent or unknown",
                report,
            )

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
        for table in manifest_tables:
            table.create(connection, checkfirst=False)
        applied_at = datetime.now(UTC)
        for revision in expected_revisions:
            _insert_revision(connection, revision=revision, applied_at=applied_at)
    return assert_schema_ready(engine)
