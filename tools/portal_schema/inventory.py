from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint

from ai_platform.portal.control_plane.database import Base
from ai_platform.portal.database.model_registry import load_portal_models


ROOT = Path(__file__).resolve().parents[2]
PORTAL_ROOT = ROOT / "ai_platform" / "portal"
CREATE_TABLE_RE = re.compile(
    r"\bCREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+[\"`\[]?([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
CREATE_ALL_RE = re.compile(r"\b(?:Base\.)?metadata\.create_all\s*\(")


def _column_payload(column: Any) -> dict[str, Any]:
    return {
        "name": column.name,
        "type": str(column.type),
        "nullable": bool(column.nullable),
        "primary_key": bool(column.primary_key),
        "unique": bool(column.unique),
        "index": bool(column.index),
        "server_default": None if column.server_default is None else str(column.server_default.arg),
    }


def _constraint_payload(constraint: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": constraint.name,
        "type": type(constraint).__name__,
        "columns": sorted(column.name for column in constraint.columns),
    }
    if isinstance(constraint, ForeignKeyConstraint):
        payload["references"] = sorted(
            f"{element.column.table.name}.{element.column.name}" for element in constraint.elements
        )
        payload["ondelete"] = sorted(
            {element.ondelete for element in constraint.elements if element.ondelete}
        )
        payload["onupdate"] = sorted(
            {element.onupdate for element in constraint.elements if element.onupdate}
        )
    elif isinstance(constraint, CheckConstraint):
        payload["sqltext"] = str(constraint.sqltext)
    elif isinstance(constraint, UniqueConstraint):
        payload["scope"] = sorted(column.name for column in constraint.columns)
    return payload


def _index_payload(index: Index) -> dict[str, Any]:
    return {
        "name": index.name,
        "columns": sorted(
            getattr(expression, "name", str(expression)) for expression in index.expressions
        ),
        "unique": bool(index.unique),
    }


def _orm_inventory() -> dict[str, Any]:
    load_portal_models()
    tables: dict[str, Any] = {}
    for table_name, table in sorted(Base.metadata.tables.items()):
        tables[table_name] = {
            "columns": [_column_payload(column) for column in table.columns],
            "constraints": sorted(
                (_constraint_payload(constraint) for constraint in table.constraints),
                key=lambda item: (
                    item["type"],
                    item["name"] or "",
                    tuple(item["columns"]),
                ),
            ),
            "indexes": sorted(
                (_index_payload(index) for index in table.indexes),
                key=lambda item: (item["name"] or "", tuple(item["columns"])),
            ),
        }
    return {"table_count": len(tables), "tables": tables}


def _migration_inventory() -> dict[str, Any]:
    files: dict[str, Any] = {}
    table_owners: dict[str, list[str]] = {}
    for path in sorted(PORTAL_ROOT.glob("**/migrations/*.sql")):
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        tables = sorted(set(CREATE_TABLE_RE.findall(text)))
        files[relative] = {
            "tables": tables,
            "sha256_input_bytes": len(text.encode("utf-8")),
        }
        for table in tables:
            table_owners.setdefault(table, []).append(relative)
    return {
        "file_count": len(files),
        "files": files,
        "table_count": len(table_owners),
        "table_owners": dict(sorted(table_owners.items())),
    }


def _create_all_inventory() -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for path in sorted(PORTAL_ROOT.glob("**/*.py")):
        relative = path.relative_to(ROOT).as_posix()
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if CREATE_ALL_RE.search(line):
                matches.append(
                    {
                        "path": relative,
                        "line": line_number,
                        "source": line.strip(),
                    }
                )
    return matches


def build_inventory() -> dict[str, Any]:
    orm = _orm_inventory()
    migrations = _migration_inventory()
    orm_tables = set(orm["tables"])
    migration_tables = set(migrations["table_owners"])
    return {
        "format_version": 1,
        "orm": orm,
        "migrations": migrations,
        "drift": {
            "orm_without_migration": sorted(orm_tables - migration_tables),
            "migration_without_orm": sorted(migration_tables - orm_tables),
            "duplicate_migration_owners": {
                table: owners
                for table, owners in migrations["table_owners"].items()
                if len(owners) != 1
            },
        },
        "create_all_calls": _create_all_inventory(),
        "safety": {
            "secret_values_recorded": False,
            "protected_production_mutated": False,
            "live_capital_authorized": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "orm_tables": payload["orm"]["table_count"],
                "migration_tables": payload["migrations"]["table_count"],
                "orm_without_migration": payload["drift"]["orm_without_migration"],
                "migration_without_orm": payload["drift"]["migration_without_orm"],
                "create_all_calls": payload["create_all_calls"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
