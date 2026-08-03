#!/usr/bin/env python3
# ruff: noqa: E501
from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from audit_ledger import (
    load_ledger,
    resolve_exact_head,
    validate_inventory,
    validate_report_metadata,
)

DATA = Path("artifacts/portal-deep-inventory.json")
OUT = Path("artifacts")
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


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "|" + "|".join("---" for _ in headers) + "|",
            *("| " + " | ".join(row) + " |" for row in rows),
        ]
    )


def classification(ledger: Mapping[str, Any], section: str, key: str) -> Mapping[str, str]:
    try:
        return ledger["classifications"][section][key]
    except KeyError as exc:
        raise SystemExit(f"missing explicit classification for {section}:{key}") from exc


def report_header(title: str, data: Mapping[str, Any]) -> list[str]:
    return [
        title,
        "",
        f"- Audited head: `{data['audited_head']}`",
        f"- Ledger version: `{data['ledger_version']}`",
        f"- Ledger SHA-256: `{data['ledger_sha256']}`",
        "",
    ]


def module_matrix(data: Mapping[str, Any], ledger: Mapping[str, Any]) -> str:
    rows: list[list[str]] = []
    counts = {key: 0 for key in STATUS_ORDER}
    for item in data["backend_modules"]:
        rule = classification(ledger, "backend_modules", str(item["module"]))
        status = str(rule["status"])
        counts[status] += 1
        rows.append(
            [
                f"`{item['module']}`",
                status,
                str(rule["reason"]),
                str(len(item["routers"])),
                str(len(item["repositories"])),
                str(len(item["migrations"])),
                str(len(item["tests"])),
                str(rule["issue"]),
            ]
        )

    route_rows: list[list[str]] = []
    for item in data["backend_routes"]:
        key = f"{item['method']} {item['route']}"
        rule = classification(ledger, "backend_routes", key)
        route_rows.append(
            [
                str(item["method"]),
                f"`{item['route']}`",
                f"`{item['file']}:{item['line']}`",
                str(rule["status"]),
                str(rule["reason"]),
                str(rule["issue"]),
            ]
        )

    notes = ledger["classifications"]["runtime_notes"]
    lines = report_header("# AI Trading Portal backend completeness matrix", data)
    lines.extend(
        [
            f"- Evidence: {notes['backend_evidence']}",
            "",
            "## Module matrix",
            "",
            md_table(
                [
                    "Module",
                    "Status",
                    "Reason",
                    "Routers",
                    "Repositories",
                    "Migrations",
                    "Tests",
                    "Issue/boundary",
                ],
                rows,
            ),
            "",
            "## Module status totals",
            "",
            *(f"- `{key}`: {counts[key]}" for key in STATUS_ORDER),
            "",
            "## All FastAPI route declarations",
            "",
            md_table(
                ["Method", "Route", "Source", "Status", "Reason", "Issue/boundary"],
                route_rows,
            ),
            "",
        ]
    )
    for route, rule in ledger["classifications"]["expected_absent_backend_routes"].items():
        lines.append(
            f"Expected but absent `{route}` producers are classified `{rule['status']}` in {rule['issue']}."
        )
    lines.append("")
    return "\n".join(lines)


def frontend_matrix(data: Mapping[str, Any], ledger: Mapping[str, Any]) -> str:
    pages: list[list[str]] = []
    for item in data["frontend_pages"]:
        rule = classification(ledger, "frontend_pages", str(item["route"]))
        pages.append(
            [
                f"`{item['route']}`",
                f"`{item['file']}`",
                str(rule["status"]),
                str(rule["reason"]),
                "yes" if item["has_form"] else "no",
                "yes" if item["explicit_unavailable"] or item["explicit_empty"] else "no",
                str(rule["issue"]),
            ]
        )

    bff: list[list[str]] = []
    for item in data["bff_handlers"]:
        rule = classification(ledger, "bff_handlers", str(item["route"]))
        targets = ", ".join(f"`{value}`" for value in item["backend_targets"]) or "local/indirect"
        bff.append(
            [
                f"`{item['route']}`",
                ", ".join(item["methods"]) or "none",
                targets,
                str(rule["status"]),
                str(rule["reason"]),
                "yes" if item["fixture_branch"] else "no",
                "yes" if item["csrf"] else "no",
                str(rule["issue"]),
            ]
        )

    lines = report_header("# AI Trading Portal frontend and BFF completeness matrix", data)
    lines.extend(
        [
            "## All Next.js pages",
            "",
            md_table(
                ["Page", "Source", "Status", "Reason", "Form", "Explicit state", "Issue/boundary"],
                pages,
            ),
            "",
            "## All same-origin BFF handlers",
            "",
            md_table(
                [
                    "BFF route",
                    "Methods",
                    "Backend targets",
                    "Status",
                    "Reason",
                    "Fixture branch",
                    "CSRF",
                    "Issue/boundary",
                ],
                bff,
            ),
            "",
            "Canonical navigation inventory is validated separately; any added, removed or renamed page/BFF route now requires an explicit ledger update.",
            "",
        ]
    )
    return "\n".join(lines)


def runtime_matrix(data: Mapping[str, Any], ledger: Mapping[str, Any]) -> str:
    comp_rows: list[list[str]] = []
    for needle, refs in data["composition_evidence"].items():
        product = [
            value for value in refs if "/tests/" not in value and not value.startswith("tests/")
        ]
        test_refs = [value for value in refs if value not in product]
        status = (
            "COMPOSED"
            if product and not str(needle).startswith(("InMemory", "Unavailable"))
            else "TEST_ONLY/DEFAULT_BOUNDARY"
        )
        comp_rows.append(
            [
                f"`{needle}`",
                status,
                str(len(product)),
                str(len(test_refs)),
                "<br>".join((product + test_refs)[:3]) or "none",
            ]
        )

    test_counts: dict[str, int] = {}
    for item in data["tests"]:
        kind = str(item["kind"])
        test_counts[kind] = test_counts.get(kind, 0) + 1
    workflows = [
        [
            f"`{item['name']}`",
            f"`{item['file']}`",
            "security" if item["security"] else "validation",
        ]
        for item in data["workflows"]
    ]
    fixtures = ledger["classifications"]["runtime_fixture_boundaries"]
    fixture_rows = [
        [
            str(item["path"]),
            str(item["classification"]),
            str(item["proves"]),
            str(item["does_not_prove"]),
        ]
        for item in fixtures
    ]
    deployment_rows = [
        [str(item["area"]), str(item["status"]), str(item["reason"])]
        for item in ledger["classifications"]["deployment_boundaries"]
    ]
    notes = ledger["classifications"]["runtime_notes"]
    browser_count = test_counts.get("browser_e2e", 0)

    lines = report_header("# AI Trading Portal runtime, fixture, test and deployment matrix", data)
    lines.extend(
        [
            "## Runtime composition roots and boundaries",
            "",
            md_table(
                [
                    "Symbol/construction",
                    "Classification",
                    "Product refs",
                    "Test refs",
                    "Evidence sample",
                ],
                comp_rows,
            ),
            "",
            "## Fixture/mock/provider boundary",
            "",
            md_table(["Path/evidence", "Classification", "Proves", "Does not prove"], fixture_rows),
            "",
            "## Test inventory",
            "",
            md_table(
                ["Kind", "Files", "Audit interpretation"],
                [
                    [f"`{kind}`", str(count), "exact file list in deep inventory JSON"]
                    for kind, count in sorted(test_counts.items())
                ],
            ),
            "",
            f"Browser conclusion: {browser_count} browser E2E files were inventoried. {notes['browser_conclusion']} See {notes['browser_issue']}.",
            "",
            "## Relevant workflow inventory",
            "",
            md_table(["Workflow", "File", "Role"], workflows),
            "",
            "## Deployment and external acceptance",
            "",
            md_table(["Area", "Status", "Reason"], deployment_rows),
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
    data: dict[str, Any] = json.loads(DATA.read_text(encoding="utf-8"))
    validate_report_metadata(data, ledger, audited_head)
    validate_inventory(data, ledger)
    OUT.mkdir(exist_ok=True)
    outputs = {
        "portal-backend-matrix.md": module_matrix(data, ledger),
        "portal-frontend-bff-matrix.md": frontend_matrix(data, ledger),
        "portal-runtime-test-deployment-matrix.md": runtime_matrix(data, ledger),
    }
    for name, content in outputs.items():
        (OUT / name).write_text(content, encoding="utf-8")
    print(
        json.dumps(
            {name: len(content.splitlines()) for name, content in outputs.items()},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
