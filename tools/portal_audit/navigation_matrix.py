#!/usr/bin/env python3
# ruff: noqa: E501
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from audit_ledger import (
    load_ledger,
    resolve_exact_head,
    validate_inventory,
    validate_report_metadata,
)


APP_SHELL = Path("ai_platform/portal/web/components/app-shell.tsx")
WEB_AVAILABILITY = Path("ai_platform/portal/web/lib/product-surface-availability.json")
WEB_UNAVAILABLE_OVERALL_STATUSES = ("DISCONNECTED", "MISSING")
INVENTORY = Path("artifacts/portal-deep-inventory.json")
OUTPUT_JSON = Path("artifacts/portal-navigation-completeness-matrix.json")
OUTPUT_MD = Path("artifacts/portal-navigation-completeness-matrix.md")
STATUS_ORDER = [
    "COMPLETE",
    "PARTIAL",
    "MISSING",
    "DISCONNECTED",
    "FIXTURE_ONLY",
    "EXTERNAL_ACCEPTANCE_REQUIRED",
    "BLOCKED",
    "NOT_APPLICABLE",
]


def parse_navigation() -> tuple[tuple[str, str], ...]:
    raw = APP_SHELL.read_text(encoding="utf-8")
    return tuple(re.findall(r'\{ href: "([^"]+)", label: "([^"]+)" \}', raw))


def load_inventory() -> dict[str, Any]:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def surfaces(ledger: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return list(ledger["classifications"]["navigation"])


def expected_web_availability(ledger: Mapping[str, Any]) -> dict[str, Any]:
    unavailable = [
        {
            "route": str(item["route"]),
            "label": str(item["label"]),
            "status": str(item["overall"]),
            "issues": str(item["issues"]),
            "reason": str(item["reason"]),
        }
        for item in surfaces(ledger)
        if item["overall"] in WEB_UNAVAILABLE_OVERALL_STATUSES
    ]
    return {
        "schema_version": "portal-product-surface-availability-v1",
        "source": "tools/portal_audit/ledger/navigation.json",
        "ledger_version": str(ledger["ledger_version"]),
        "unavailable_overall_statuses": list(WEB_UNAVAILABLE_OVERALL_STATUSES),
        "surfaces": unavailable,
    }


def validate_web_availability(ledger: Mapping[str, Any]) -> None:
    try:
        actual = json.loads(WEB_AVAILABILITY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot load web surface availability projection: {exc}") from exc
    expected = expected_web_availability(ledger)
    if actual != expected:
        raise SystemExit(
            "web surface availability projection drift requires an explicit ledger-synchronized update: "
            f"expected {expected!r}, got {actual!r}"
        )


def validate_navigation(data: Mapping[str, Any], ledger: Mapping[str, Any]) -> None:
    expected = tuple((str(item["route"]), str(item["label"])) for item in surfaces(ledger))
    actual = parse_navigation()
    if actual != expected:
        raise SystemExit(
            f"navigation drift requires an explicit ledger update: expected {expected!r}, got {actual!r}"
        )
    page_routes = {str(item["route"]) for item in data["frontend_pages"]}
    missing = sorted(
        str(item["route"]) for item in surfaces(ledger) if item["route"] not in page_routes
    )
    if missing:
        raise SystemExit(f"navigation pages missing: {missing}")
    validate_web_availability(ledger)


def markdown(data: Mapping[str, Any], ledger: Mapping[str, Any]) -> str:
    rows = surfaces(ledger)
    totals = {status: 0 for status in STATUS_ORDER}
    for surface in rows:
        totals[str(surface["overall"])] += 1
    notes = ledger["classifications"]["runtime_notes"]
    lines = [
        "# AI Trading Portal left-navigation completeness matrix",
        "",
        f"- Audited head: `{data['audited_head']}`",
        f"- Ledger version: `{data['ledger_version']}`",
        f"- Ledger SHA-256: `{data['ledger_sha256']}`",
        f"- Canonical navigation items: **{len(rows)}**",
        f"- Global deployment gate: {notes['navigation_global_deployment']}",
        f"- Global real browser-to-backend gate: {notes['navigation_global_e2e']}",
        "",
        "## Overall totals",
        "",
    ]
    lines.extend(f"- `{status}`: {totals[status]}" for status in STATUS_ORDER)
    lines.extend(
        [
            "",
            "## Every left-navigation item",
            "",
            "| Group | Item | Route | Frontend | API/BFF | Backend | Persistence/provider | Tests | Overall | Issue/boundary | Reason |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for surface in rows:
        lines.append(
            f"| {surface['group']} | {surface['label']} | `{surface['route']}` | {surface['frontend']} | {surface['api_boundary']} | {surface['backend']} | {surface['persistence_provider']} | {surface['tests']} | **{surface['overall']}** | {surface['issues']} | {surface['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `COMPLETE` requires a usable frontend, reviewed API boundary, composed backend, durable or explicitly bounded provider path, and non-fixture acceptance evidence.",
            "- `PARTIAL` means a useful subset exists but documented actions, data sources or acceptance evidence remain incomplete.",
            "- `MISSING` means the expected producer or capability is absent.",
            "- `DISCONNECTED` means classes/routes may exist but the canonical product does not compose the required durable/provider/runtime path.",
            "- `EXTERNAL_ACCEPTANCE_REQUIRED` means repository-side behavior is bounded, but owner-managed identity, source or protected-target acceptance is still required.",
            "",
            "Any navigation, inventory or runtime-composition change now fails until this ledger receives an explicit current disposition.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    audited_head = resolve_exact_head(args.head)
    ledger = load_ledger()
    data = load_inventory()
    validate_report_metadata(data, ledger, audited_head)
    validate_inventory(data, ledger)
    validate_navigation(data, ledger)
    OUTPUT_JSON.parent.mkdir(exist_ok=True)
    payload = {
        "schema_version": "portal-navigation-completeness-v2",
        "audited_head": data["audited_head"],
        "ledger_version": data["ledger_version"],
        "ledger_sha256": data["ledger_sha256"],
        "count": len(surfaces(ledger)),
        "surfaces": surfaces(ledger),
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(markdown(data, ledger), encoding="utf-8")
    print(json.dumps({"navigation_items": len(surfaces(ledger))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
