from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, text


class SchemaIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Migration:
    position: int
    migration_id: str
    path: Path
    sha256: str


MIGRATION_PATHS: tuple[str, ...] = (
    "control_plane/migrations/0001_control_plane.sql",
    "identity/migrations/0001_identity_lifecycle.sql",
    "risk/migrations/0001_risk_core.sql",
    "bot_operations/migrations/0001_bot_operations.sql",
    "intelligence/migrations/0001_trade_intelligence.sql",
    "intelligence/migrations/0002_tenant_relational_integrity.sql",
    "events/migrations/0001_event_inbox.sql",
    "execution_submission/migrations/0001_private_dry_run_submission.sql",
    "learning/migrations/0001_learning_loop.sql",
    "model_control/migrations/0001_model_control.sql",
    "operations/migrations/0001_operational_read_models.sql",
    "operations/migrations/0002_private_runtime_reconciliation.sql",
    "product/migrations/0001_product_capabilities.sql",
    "signal_wizard/migrations/0001_signal_wizard.sql",
    "signal_wizard/migrations/0002_semantic_hardening.sql",
    "strategy_lab/migrations/0001_strategy_lab.sql",
    "telemetry/migrations/0001_inference_drift_telemetry.sql",
    "control_plane/migrations/0002_orm_type_alignment.sql",
)

_SCHEMA_LOCK_ID = 1122
_SCHEMA_TABLE = "portal_schema_migrations"


def _portal_root() -> Path:
    return Path(__file__).resolve().parents[1]


def migration_manifest() -> tuple[Migration, ...]:
    portal_root = _portal_root()
    migrations: list[Migration] = []
    for position, relative in enumerate(MIGRATION_PATHS, start=1):
        path = portal_root / relative
        if not path.is_file():
            raise SchemaIntegrityError(f"declared migration is missing: {relative}")
        raw = path.read_bytes()
        migrations.append(
            Migration(
                position=position,
                migration_id=relative.removesuffix(".sql").replace("/migrations/", ":"),
                path=path,
                sha256=hashlib.sha256(raw).hexdigest(),
            )
        )
    discovered = {
        path.relative_to(portal_root).as_posix()
        for path in portal_root.rglob("migrations/*.sql")
    }
    declared = set(MIGRATION_PATHS)
    if discovered != declared:
        missing = sorted(declared - discovered)
        undeclared = sorted(discovered - declared)
        raise SchemaIntegrityError(
            "migration manifest differs from repository files: "
            f"missing={missing}, undeclared={undeclared}"
        )
    return tuple(migrations)


def expected_revision() -> str:
    migration = migration_manifest()[-1]
    return f"{migration.position}:{migration.migration_id}:{migration.sha256[:12]}"


def split_sql_statements(raw: str) -> tuple[str, ...]:
    statements: list[str] = []
    current: list[str] = []
    index = 0
    single_quote = False
    double_quote = False
    dollar_tag: str | None = None
    line_comment = False
    block_comment = False

    while index < len(raw):
        char = raw[index]
        following = raw[index + 1] if index + 1 < len(raw) else ""

        if line_comment:
            current.append(char)
            if char == "\n":
                line_comment = False
            index += 1
            continue

        if block_comment:
            current.append(char)
            if char == "*" and following == "/":
                current.append(following)
                block_comment = False
                index += 2
            else:
                index += 1
            continue

        if dollar_tag is not None:
            if raw.startswith(dollar_tag, index):
                current.append(dollar_tag)
                index += len(dollar_tag)
                dollar_tag = None
            else:
                current.append(char)
                index += 1
            continue

        if single_quote:
            current.append(char)
            if char == "'":
                if following == "'":
                    current.append(following)
                    index += 2
                    continue
                single_quote = False
            index += 1
            continue

        if double_quote:
            current.append(char)
            if char == '"':
                if following == '"':
                    current.append(following)
                    index += 2
                    continue
                double_quote = False
            index += 1
            continue

        if char == "-" and following == "-":
            current.extend((char, following))
            line_comment = True
            index += 2
            continue
        if char == "/" and following == "*":
            current.extend((char, following))
            block_comment = True
            index += 2
            continue
        if char == "'":
            current.append(char)
            single_quote = True
            index += 1
            continue
        if char == '"':
            current.append(char)
            double_quote = True
            index += 1
            continue
        if char == "$":
            closing = raw.find("$", index + 1)
            if closing != -1:
                candidate = raw[index : closing + 1]
                inner = candidate[1:-1]
                if not inner or inner.replace("_", "a").isalnum():
                    current.append(candidate)
                    dollar_tag = candidate
                    index = closing + 1
                    continue
        if char == ";":
            statement = "".join(current).strip()
            if statement and statement.upper() not in {"BEGIN", "BEGIN TRANSACTION", "COMMIT"}:
                statements.append(statement)
            current.clear()
            index += 1
            continue

        current.append(char)
        index += 1

    if single_quote or double_quote or dollar_tag is not None or block_comment:
        raise SchemaIntegrityError("migration SQL contains an unterminated lexical construct")
    statement = "".join(current).strip()
    if statement and statement.upper() not in {"BEGIN", "BEGIN TRANSACTION", "COMMIT"}:
        statements.append(statement)
    return tuple(statements)


def _require_postgresql(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        raise SchemaIntegrityError(
            "public Portal schema authority requires PostgreSQL; "
            f"received dialect={engine.dialect.name}"
        )


def _create_revision_table(connection: Any) -> None:
    connection.exec_driver_sql(
        f"""
        CREATE TABLE IF NOT EXISTS {_SCHEMA_TABLE} (
            position INTEGER PRIMARY KEY,
            migration_id VARCHAR(255) NOT NULL UNIQUE,
            sha256 VARCHAR(64) NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT ck_portal_schema_migration_position CHECK (position > 0),
            CONSTRAINT ck_portal_schema_migration_sha256 CHECK (length(sha256) = 64)
        )
        """
    )


def _read_applied(connection: Any) -> tuple[dict[str, Any], ...]:
    rows = connection.execute(
        text(
            f"SELECT position, migration_id, sha256, applied_at "
            f"FROM {_SCHEMA_TABLE} ORDER BY position"
        )
    ).mappings()
    return tuple(dict(row) for row in rows)


def _verify_applied(
    applied: tuple[dict[str, Any], ...],
    manifest: tuple[Migration, ...],
) -> None:
    if len(applied) > len(manifest):
        raise SchemaIntegrityError("database contains migration positions beyond this image")
    for expected_position, row in enumerate(applied, start=1):
        migration = manifest[expected_position - 1]
        if row["position"] != expected_position:
            raise SchemaIntegrityError("database migration positions are not contiguous")
        if row["migration_id"] != migration.migration_id:
            raise SchemaIntegrityError(
                "database migration identity diverges at position "
                f"{expected_position}: {row['migration_id']} != {migration.migration_id}"
            )
        if row["sha256"] != migration.sha256:
            raise SchemaIntegrityError(
                f"applied migration checksum diverges: {migration.migration_id}"
            )


def apply_migrations(engine: Engine) -> dict[str, Any]:
    _require_postgresql(engine)
    manifest = migration_manifest()
    applied_count = 0
    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT pg_advisory_lock(%s)", (_SCHEMA_LOCK_ID,))
        connection.commit()
        try:
            with connection.begin():
                _create_revision_table(connection)
                applied = _read_applied(connection)
                _verify_applied(applied, manifest)

            for migration in manifest[len(applied) :]:
                raw = migration.path.read_text(encoding="utf-8")
                statements = split_sql_statements(raw)
                if not statements:
                    raise SchemaIntegrityError(
                        f"migration contains no executable statements: {migration.migration_id}"
                    )
                with connection.begin():
                    for statement in statements:
                        connection.exec_driver_sql(statement)
                    connection.execute(
                        text(
                            f"INSERT INTO {_SCHEMA_TABLE} "
                            "(position, migration_id, sha256) "
                            "VALUES (:position, :migration_id, :sha256)"
                        ),
                        {
                            "position": migration.position,
                            "migration_id": migration.migration_id,
                            "sha256": migration.sha256,
                        },
                    )
                applied_count += 1

            with connection.begin():
                final_applied = _read_applied(connection)
                _verify_applied(final_applied, manifest)
                if len(final_applied) != len(manifest):
                    raise SchemaIntegrityError("database migration chain is incomplete")
        finally:
            connection.exec_driver_sql("SELECT pg_advisory_unlock(%s)", (_SCHEMA_LOCK_ID,))
            connection.commit()

    return {
        "dialect": "postgresql",
        "expected_revision": expected_revision(),
        "migration_count": len(manifest),
        "applied_now": applied_count,
        "ready": True,
    }


def schema_status(engine: Engine) -> dict[str, Any]:
    _require_postgresql(engine)
    manifest = migration_manifest()
    with engine.connect() as connection:
        table_exists = connection.execute(
            text("SELECT to_regclass(:table_name) IS NOT NULL"),
            {"table_name": _SCHEMA_TABLE},
        ).scalar_one()
        if not table_exists:
            connection.rollback()
            return {
                "dialect": "postgresql",
                "expected_revision": expected_revision(),
                "current_revision": None,
                "migration_count": 0,
                "expected_migration_count": len(manifest),
                "ready": False,
                "reason": "revision_table_missing",
            }
        applied = _read_applied(connection)
        connection.rollback()
    try:
        _verify_applied(applied, manifest)
    except SchemaIntegrityError as exc:
        return {
            "dialect": "postgresql",
            "expected_revision": expected_revision(),
            "current_revision": None,
            "migration_count": len(applied),
            "expected_migration_count": len(manifest),
            "ready": False,
            "reason": str(exc),
        }
    ready = len(applied) == len(manifest)
    current_revision = None
    if applied:
        migration = manifest[len(applied) - 1]
        current_revision = (
            f"{migration.position}:{migration.migration_id}:{migration.sha256[:12]}"
        )
    return {
        "dialect": "postgresql",
        "expected_revision": expected_revision(),
        "current_revision": current_revision,
        "migration_count": len(applied),
        "expected_migration_count": len(manifest),
        "ready": ready,
        "reason": "ready" if ready else "pending_migrations",
    }


def assert_schema_ready(engine: Engine) -> dict[str, Any]:
    status = schema_status(engine)
    if not status["ready"]:
        raise SchemaIntegrityError(
            "Portal schema is not at the exact expected revision: "
            f"reason={status['reason']} current={status['current_revision']} "
            f"expected={status['expected_revision']}"
        )
    return status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("migrate", "check", "status"))
    parser.add_argument("--database-url", required=True)
    args = parser.parse_args()

    from ai_platform.portal.control_plane.database import build_engine

    engine = build_engine(args.database_url)
    try:
        if args.action == "migrate":
            result = apply_migrations(engine)
        elif args.action == "check":
            result = assert_schema_ready(engine)
        else:
            result = schema_status(engine)
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("ready") else 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
