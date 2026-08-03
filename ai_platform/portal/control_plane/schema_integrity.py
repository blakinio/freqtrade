from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, Table, UniqueConstraint

from ai_platform.portal.control_plane.database import Base


_CREATE_TABLE_RE = re.compile(
    r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`\[]?(?P<table>[A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)


def _portal_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _package_root() -> Path:
    return Path(__file__).resolve().parents[3]


def discover_model_modules() -> tuple[str, ...]:
    portal_root = _portal_root()
    package_root = _package_root()
    modules: list[str] = []
    for path in sorted(portal_root.rglob("models.py")):
        relative = path.relative_to(package_root).with_suffix("")
        modules.append(".".join(relative.parts))
    return tuple(modules)


def import_model_modules() -> tuple[str, ...]:
    modules = discover_model_modules()
    for module in modules:
        importlib.import_module(module)
    return modules


def _column_payload(table: Table) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for column in table.columns:
        result.append(
            {
                "name": column.name,
                "type": str(column.type),
                "nullable": bool(column.nullable),
                "primary_key": bool(column.primary_key),
                "unique": bool(column.unique),
                "index": bool(column.index),
            }
        )
    return result


def _constraint_payload(table: Table) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for constraint in sorted(
        table.constraints,
        key=lambda item: (
            item.__class__.__name__,
            item.name or "",
            tuple(column.name for column in getattr(item, "columns", ())),
        ),
    ):
        payload: dict[str, Any] = {
            "kind": constraint.__class__.__name__,
            "name": constraint.name,
            "columns": [column.name for column in getattr(constraint, "columns", ())],
        }
        if isinstance(constraint, ForeignKeyConstraint):
            payload["references"] = [
                {
                    "column": element.parent.name,
                    "target": element.target_fullname,
                    "ondelete": element.ondelete,
                    "onupdate": element.onupdate,
                }
                for element in constraint.elements
            ]
        elif isinstance(constraint, CheckConstraint):
            payload["sqltext"] = str(constraint.sqltext)
        elif isinstance(constraint, UniqueConstraint):
            payload["unique"] = True
        result.append(payload)
    return result


def _index_payload(table: Table) -> list[dict[str, Any]]:
    return [
        {
            "name": index.name,
            "columns": [column.name for column in index.columns],
            "unique": bool(index.unique),
        }
        for index in sorted(table.indexes, key=lambda item: item.name or "")
        if isinstance(index, Index)
    ]


def orm_inventory() -> dict[str, Any]:
    modules = import_model_modules()
    tables: dict[str, Any] = {}
    for table in sorted(Base.metadata.tables.values(), key=lambda item: item.name):
        tables[table.name] = {
            "columns": _column_payload(table),
            "constraints": _constraint_payload(table),
            "indexes": _index_payload(table),
        }
    return {"modules": list(modules), "tables": tables}


def migration_inventory() -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    table_owners: dict[str, list[str]] = {}
    for path in sorted(_portal_root().rglob("migrations/*.sql")):
        raw = path.read_text(encoding="utf-8")
        relative = path.relative_to(_package_root()).as_posix()
        tables = sorted({match.group("table") for match in _CREATE_TABLE_RE.finditer(raw)})
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        files.append(
            {
                "path": relative,
                "sha256": digest,
                "tables": tables,
            }
        )
        for table in tables:
            table_owners.setdefault(table, []).append(relative)
    return {
        "files": files,
        "tables": {name: owners for name, owners in sorted(table_owners.items())},
    }


def build_inventory() -> dict[str, Any]:
    orm = orm_inventory()
    migrations = migration_inventory()
    orm_tables = set(orm["tables"])
    migration_tables = set(migrations["tables"])
    return {
        "schema_inventory_version": 1,
        "orm": orm,
        "migrations": migrations,
        "summary": {
            "model_modules": len(orm["modules"]),
            "orm_tables": len(orm_tables),
            "migration_files": len(migrations["files"]),
            "migration_tables": len(migration_tables),
            "orm_tables_without_migration": sorted(orm_tables - migration_tables),
            "migration_tables_without_orm": sorted(migration_tables - orm_tables),
            "duplicate_migration_table_owners": {
                table: owners
                for table, owners in migrations["tables"].items()
                if len(owners) > 1
            },
        },
    }


def render_markdown(inventory: dict[str, Any]) -> str:
    summary = inventory["summary"]
    lines = [
        "# Portal schema inventory",
        "",
        f"- Model modules: **{summary['model_modules']}**",
        f"- ORM tables: **{summary['orm_tables']}**",
        f"- Migration files: **{summary['migration_files']}**",
        f"- Migration-owned tables: **{summary['migration_tables']}**",
        "",
        "## ORM tables without migration",
        "",
    ]
    missing = summary["orm_tables_without_migration"]
    lines.extend(f"- `{table}`" for table in missing)
    if not missing:
        lines.append("- none")
    lines.extend(["", "## Migration tables without ORM model", ""])
    extra = summary["migration_tables_without_orm"]
    lines.extend(f"- `{table}`" for table in extra)
    if not extra:
        lines.append("- none")
    lines.extend(["", "## Migration files", ""])
    for item in inventory["migrations"]["files"]:
        rendered_tables = ", ".join(f"`{table}`" for table in item["tables"]) or "none"
        lines.append(f"- `{item['path']}`: {rendered_tables}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--fail-on-table-drift", action="store_true")
    args = parser.parse_args()

    inventory = build_inventory()
    if args.format == "json":
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print(render_markdown(inventory), end="")

    summary = inventory["summary"]
    if args.fail_on_table_drift and (
        summary["orm_tables_without_migration"]
        or summary["duplicate_migration_table_owners"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
