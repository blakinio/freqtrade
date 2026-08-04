from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from ai_platform.portal.control_plane.database import build_engine
from ai_platform.portal.database.schema import (
    SchemaMigrationError,
    assert_schema_ready,
    migrate_database,
    scan_database_integrity,
    schema_status,
)


def _write_report(report: dict[str, Any], output: Path | None) -> None:
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)


def _database_url(explicit_url: str | None) -> str:
    value = explicit_url or os.environ.get("PORTAL_DATABASE_URL")
    if not value:
        raise RuntimeError("PORTAL_DATABASE_URL is required")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Freqtrade Portal schema authority")
    parser.add_argument("command", choices=("migrate", "check", "status", "scan"))
    parser.add_argument("--database-url")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    engine = build_engine(_database_url(args.database_url))
    try:
        if args.command == "migrate":
            report = migrate_database(engine)
        elif args.command == "check":
            report = assert_schema_ready(engine)
        elif args.command == "scan":
            report = scan_database_integrity(engine)
        else:
            report = schema_status(engine)
        _write_report(report, args.output)
        return 0
    except SchemaMigrationError as exc:
        report = {
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc),
            "details": exc.report,
            "safety": {
                "secret_values_recorded": False,
                "protected_production_mutated": False,
                "live_capital_authorized": False,
            },
        }
        _write_report(report, args.output)
        return 2
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
