from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Integer,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    Text,
    inspect,
)
from sqlalchemy.engine import Engine
from sqlalchemy.sql.type_api import TypeEngine

from ai_platform.portal.control_plane.database import Base, build_engine
from ai_platform.portal.control_plane.schema_integrity import import_model_modules


_SCHEMA_CONTRACT_VERSION = 1
_REVISION_TABLE = "portal_schema_migrations"
_WHITESPACE_RE = re.compile(r"\s+")


class SchemaContractError(RuntimeError):
    pass


def _normalize_sql(value: str | None) -> str | None:
    if value is None:
        return None
    return _WHITESPACE_RE.sub(" ", value.strip())


def _type_contract(value: TypeEngine[Any]) -> dict[str, Any]:
    if isinstance(value, Text):
        return {"family": "text"}
    if isinstance(value, String):
        return {"family": "string", "length": value.length}
    if isinstance(value, Boolean):
        return {"family": "boolean"}
    if isinstance(value, SmallInteger):
        return {"family": "small_integer"}
    if isinstance(value, BigInteger):
        return {"family": "big_integer"}
    if isinstance(value, Integer):
        return {"family": "integer"}
    if isinstance(value, Float):
        return {"family": "float", "precision": value.precision}
    if isinstance(value, Numeric):
        return {
            "family": "numeric",
            "precision": value.precision,
            "scale": value.scale,
        }
    if isinstance(value, DateTime):
        return {"family": "datetime", "timezone": bool(value.timezone)}
    if isinstance(value, LargeBinary):
        return {"family": "binary", "length": value.length}
    return {"family": value.__class__.__name__.lower(), "rendered": str(value)}


def database_schema_contract(engine: Engine) -> dict[str, Any]:
    if engine.dialect.name != "postgresql":
        raise SchemaContractError(
            f"schema contract requires PostgreSQL; received {engine.dialect.name}"
        )
    inspector = inspect(engine)
    table_names = sorted(
        name for name in inspector.get_table_names() if name.startswith("portal_")
    )
    tables: dict[str, Any] = {}
    for table_name in table_names:
        columns = []
        for column in inspector.get_columns(table_name):
            columns.append(
                {
                    "name": column["name"],
                    "type": _type_contract(column["type"]),
                    "nullable": bool(column["nullable"]),
                    "default": _normalize_sql(column.get("default")),
                    "identity": column.get("identity"),
                    "computed": column.get("computed"),
                }
            )
        primary_key = inspector.get_pk_constraint(table_name)
        unique_constraints = [
            {
                "name": item.get("name"),
                "columns": list(item.get("column_names") or ()),
                "nulls_not_distinct": item.get("dialect_options", {}).get(
                    "postgresql_nulls_not_distinct"
                ),
            }
            for item in inspector.get_unique_constraints(table_name)
        ]
        foreign_keys = [
            {
                "name": item.get("name"),
                "columns": list(item.get("constrained_columns") or ()),
                "referred_schema": item.get("referred_schema"),
                "referred_table": item.get("referred_table"),
                "referred_columns": list(item.get("referred_columns") or ()),
                "ondelete": (item.get("options") or {}).get("ondelete"),
                "onupdate": (item.get("options") or {}).get("onupdate"),
                "deferrable": (item.get("options") or {}).get("deferrable"),
                "initially": (item.get("options") or {}).get("initially"),
            }
            for item in inspector.get_foreign_keys(table_name)
        ]
        checks = [
            {
                "name": item.get("name"),
                "sqltext": _normalize_sql(item.get("sqltext")),
            }
            for item in inspector.get_check_constraints(table_name)
        ]
        indexes = [
            {
                "name": item.get("name"),
                "columns": list(item.get("column_names") or ()),
                "unique": bool(item.get("unique")),
                "duplicates_constraint": item.get("duplicates_constraint"),
                "include_columns": list(
                    (item.get("include_columns") or item.get("dialect_options", {}).get(
                        "postgresql_include", ()
                    ))
                ),
                "where": _normalize_sql(
                    (item.get("dialect_options") or {}).get("postgresql_where")
                ),
            }
            for item in inspector.get_indexes(table_name)
        ]
        tables[table_name] = {
            "columns": columns,
            "primary_key": {
                "name": primary_key.get("name"),
                "columns": list(primary_key.get("constrained_columns") or ()),
            },
            "unique_constraints": sorted(
                unique_constraints,
                key=lambda item: (item["name"] or "", item["columns"]),
            ),
            "foreign_keys": sorted(
                foreign_keys,
                key=lambda item: (item["name"] or "", item["columns"]),
            ),
            "check_constraints": sorted(
                checks,
                key=lambda item: (item["name"] or "", item["sqltext"] or ""),
            ),
            "indexes": sorted(
                indexes,
                key=lambda item: (item["name"] or "", item["columns"]),
            ),
        }
    return {
        "schema_contract_version": _SCHEMA_CONTRACT_VERSION,
        "dialect": "postgresql",
        "tables": tables,
    }


def _orm_columns() -> dict[str, dict[str, dict[str, Any]]]:
    import_model_modules()
    return {
        table.name: {
            column.name: {
                "type": _type_contract(column.type),
                "nullable": bool(column.nullable),
                "primary_key": bool(column.primary_key),
            }
            for column in table.columns
        }
        for table in Base.metadata.tables.values()
    }


def compare_orm_columns(contract: dict[str, Any]) -> list[dict[str, Any]]:
    orm_tables = _orm_columns()
    database_tables = contract["tables"]
    drift: list[dict[str, Any]] = []
    database_model_tables = set(database_tables) - {_REVISION_TABLE}
    if set(orm_tables) != database_model_tables:
        drift.append(
            {
                "kind": "table_set",
                "orm_only": sorted(set(orm_tables) - database_model_tables),
                "database_only": sorted(database_model_tables - set(orm_tables)),
            }
        )
    for table_name in sorted(set(orm_tables) & database_model_tables):
        orm_columns = orm_tables[table_name]
        db_columns = {
            column["name"]: column for column in database_tables[table_name]["columns"]
        }
        if set(orm_columns) != set(db_columns):
            drift.append(
                {
                    "kind": "column_set",
                    "table": table_name,
                    "orm_only": sorted(set(orm_columns) - set(db_columns)),
                    "database_only": sorted(set(db_columns) - set(orm_columns)),
                }
            )
        for column_name in sorted(set(orm_columns) & set(db_columns)):
            orm_column = orm_columns[column_name]
            db_column = db_columns[column_name]
            for attribute in ("type", "nullable"):
                if orm_column[attribute] != db_column[attribute]:
                    drift.append(
                        {
                            "kind": f"column_{attribute}",
                            "table": table_name,
                            "column": column_name,
                            "orm": orm_column[attribute],
                            "database": db_column[attribute],
                        }
                    )
        orm_pk = sorted(
            name for name, payload in orm_columns.items() if payload["primary_key"]
        )
        db_pk = sorted(database_tables[table_name]["primary_key"]["columns"])
        if orm_pk != db_pk:
            drift.append(
                {
                    "kind": "primary_key",
                    "table": table_name,
                    "orm": orm_pk,
                    "database": db_pk,
                }
            )
    return drift


def compare_contract(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    if actual != expected:
        raise SchemaContractError("database schema differs from the checked contract")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("snapshot", "check"))
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    engine = build_engine(args.database_url)
    try:
        contract = database_schema_contract(engine)
        orm_drift = compare_orm_columns(contract)
        payload = {"database": contract, "orm_column_drift": orm_drift}
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        else:
            print(json.dumps(payload, indent=2, sort_keys=True))
        if orm_drift:
            raise SchemaContractError("ORM table/column contract differs from PostgreSQL")
        if args.action == "check":
            if args.contract is None:
                raise SchemaContractError("--contract is required for check")
            expected = json.loads(args.contract.read_text(encoding="utf-8"))
            compare_contract(contract, expected)
        return 0
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
