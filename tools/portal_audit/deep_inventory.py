#!/usr/bin/env python3
# ruff: noqa: E501
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from audit_ledger import (
    ledger_metadata,
    load_ledger,
    resolve_exact_head,
    validate_inventory,
)


PORTAL = Path("ai_platform/portal")
WEB = PORTAL / "web"
TEST_ROOTS = [Path("tests/ai_platform/portal"), Path("tests/ai_platform_integration")]
SKIP_MODULES = {"web", "e2e", "__pycache__"}


# fmt: off

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def relative(path: Path) -> str:
    return path.as_posix()


def normalize_route(value: str) -> str:
    value = re.sub(r"\[[^/]+\]|\{[^/]+\}", "{}", value.split("?", 1)[0])
    value = re.sub(r"/+", "/", value)
    return value.rstrip("/") or "/"


def next_route(base: Path, path: Path) -> str:
    parts = [
        item
        for item in path.relative_to(base).parts[:-1]
        if not (item.startswith("(") and item.endswith(")"))
    ]
    return normalize_route("/" + "/".join(parts))


def router_prefix(raw: str) -> str:
    match = re.search(
        r"APIRouter\s*\([^)]*prefix\s*=\s*[\"']([^\"']+)",
        raw,
        re.DOTALL,
    )
    return match.group(1) if match else ""


def backend_routes() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    pattern = re.compile(
        r"@(?P<object>app|router)\.(?P<method>get|post|put|patch|delete)\(\s*"
        r"[\"'](?P<path>[^\"']+)",
        re.MULTILINE,
    )
    for path in sorted(PORTAL.rglob("*.py")):
        raw = read(path)
        prefix = router_prefix(raw)
        for match in pattern.finditer(raw):
            route = (prefix if match.group("object") == "router" else "") + match.group("path")
            result.append(
                {
                    "method": match.group("method").upper(),
                    "route": normalize_route(route),
                    "file": relative(path),
                    "line": raw[: match.start()].count("\n") + 1,
                }
            )
    unique = {
        (item["method"], item["route"], item["file"], item["line"]): item
        for item in result
    }
    return sorted(
        unique.values(),
        key=lambda item: (item["route"], item["method"], item["file"], item["line"]),
    )


def exported_methods(raw: str) -> list[str]:
    return [
        method
        for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]
        if re.search(rf"export\s+async\s+function\s+{method}\b", raw)
    ]


def backend_targets(raw: str) -> list[str]:
    values: set[str] = set()
    patterns = [
        r"[\"'`](/v1/[^\"'`\s$]*)[\"'`]",
        r"forwardControlPlaneMutation<[^>]+>\([^,]+,\s*[\"']([^\"']+)",
        r"apiFetch<[^>]+>\([\"']([^\"']+)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, raw):
            values.add(normalize_route(match.group(1)))
    return sorted(values)


def bff_inventory() -> list[dict[str, Any]]:
    base = WEB / "app" / "api"
    result: list[dict[str, Any]] = []
    for path in sorted(base.rglob("route.ts")):
        raw = read(path)
        methods = exported_methods(raw)
        mutating = any(method in methods for method in ["POST", "PUT", "PATCH", "DELETE"])
        result.append(
            {
                "route": next_route(WEB / "app", path),
                "file": relative(path),
                "methods": methods,
                "backend_targets": backend_targets(raw),
                "fixture_branch": 'dataMode() === "fixture"' in raw or "fixture" in raw.lower(),
                "csrf": "requireBrowserMutation" in raw or not mutating,
                "session": "requireBrowserSession" in raw
                or "requireBrowserMutation" in raw
                or "/identity/" in relative(path),
                "local_reader": any(
                    name in raw for name in ["MarketEvidence", "Liquidation", "WickHunter"]
                ),
            }
        )
    return result


def frontend_pages() -> list[dict[str, Any]]:
    base = WEB / "app"
    result: list[dict[str, Any]] = []
    for path in sorted(base.rglob("page.tsx")):
        raw = read(path)
        result.append(
            {
                "route": next_route(base, path),
                "file": relative(path),
                "client": '"use client"' in raw[:40],
                "has_form": "<form" in raw,
                "has_button": "<button" in raw,
                "api_refs": sorted(
                    {
                        normalize_route(value)
                        for value in re.findall(
                            r"[\"'`](/(?:api|v1)/[^\"'`\s$]*)[\"'`]",
                            raw,
                        )
                    }
                ),
                "explicit_unavailable": any(
                    value in raw for value in ["unavailable", "Unavailable", 'role="alert"']
                ),
                "explicit_empty": "empty-state" in raw,
            }
        )
    return result


def test_inventory() -> list[dict[str, Any]]:
    files: list[Path] = []
    for root in TEST_ROOTS:
        if root.exists():
            files.extend(root.rglob("test_*.py"))
    files.extend((WEB / "e2e").rglob("*.spec.ts"))
    files.extend((WEB / "e2e").rglob("*.test.mjs"))

    result: list[dict[str, Any]] = []
    for path in sorted(set(files)):
        raw = read(path)
        name = relative(path)
        if name.endswith((".spec.ts", ".test.mjs")):
            kind = "browser_e2e"
        elif "integration" in name or "TestClient(" in raw:
            kind = "integration"
        elif "contract" in name:
            kind = "contract"
        elif "migration" in name or "restart" in raw.lower():
            kind = "persistence_recovery"
        else:
            kind = "unit_component"
        result.append(
            {
                "file": name,
                "kind": kind,
                "fixture": "fixture" in raw.lower(),
                "mock": "mock" in raw.lower() or "Fake" in raw,
                "api_mode": "PORTAL_WEB_DATA_MODE" in raw and "api" in raw.lower(),
            }
        )
    return result


def backend_modules(tests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    roots = [
        path
        for path in PORTAL.iterdir()
        if path.is_dir() and path.name not in SKIP_MODULES
    ]
    for directory in sorted(roots):
        python_files = sorted(directory.rglob("*.py"))
        raw = "\n".join(read(path) for path in python_files)
        mapped_tests = [
            str(item["file"])
            for item in tests
            if f"/{directory.name}/" in str(item["file"])
            or f"ai_platform.portal.{directory.name}" in read(Path(str(item["file"])))
        ]
        result.append(
            {
                "module": directory.name,
                "python_files": [relative(path) for path in python_files],
                "services": [
                    relative(path)
                    for path in python_files
                    if path.name in {"service.py", "services.py"} or "service" in path.name
                ],
                "repositories": [
                    relative(path)
                    for path in python_files
                    if "repository" in path.name or path.name in {"store.py", "database.py"}
                ],
                "adapters_providers": [
                    relative(path)
                    for path in python_files
                    if any(
                        token in path.name
                        for token in [
                            "adapter",
                            "provider",
                            "runtime",
                            "transport",
                            "broker",
                            "driver",
                        ]
                    )
                ],
                "routers": [
                    relative(path)
                    for path in python_files
                    if path.name
                    in {"router.py", "api.py", "api_core.py", "http.py", "public_runtime.py"}
                ],
                "migrations": [relative(path) for path in sorted(directory.rglob("*.sql"))],
                "tests": mapped_tests,
                "in_memory": "InMemory" in raw,
                "unavailable_boundary": "Unavailable" in raw,
            }
        )
    return result


def workflow_inventory() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for path in sorted(Path(".github/workflows").glob("*")):
        if path.suffix not in {".yml", ".yaml"}:
            continue
        raw = read(path)
        lower = (path.name + " " + raw).lower()
        if any(
            token in lower
            for token in ["portal", "ai platform", "freqtrade ci", "zizmor", "pre-commit"]
        ):
            name = next(
                (
                    line.split(":", 1)[1].strip()
                    for line in raw.splitlines()
                    if line.startswith("name:")
                ),
                path.name,
            )
            result.append(
                {
                    "file": relative(path),
                    "name": name,
                    "portal_related": "portal" in lower,
                    "security": "zizmor" in lower or "security" in lower,
                }
            )
    return result


def composition_evidence() -> dict[str, list[str]]:
    needles = [
        "FreqtradeExecutionAdapter(",
        "PrivateRuntimeCollector(",
        "HttpPrivateRuntimeTransport(",
        "HttpPrivateRuntimeValuationSource(",
        "LokiRuntimeObservabilitySource(",
        "VaultCredentialBroker(",
        "PrivateDryRunApprovedIntentSubmitter(",
        "PrivateSubmissionExecutionAdapter(",
        "BotCommandActivationService(",
        "OutboxPublisher(",
        "InMemoryBotConfigurationRepository(",
        "InMemorySignalControlRepository(",
        "InMemoryGridControlRepository(",
        "InMemoryExchangeConnectionRepository(",
        "UnavailableRuntimeValuationSource(",
        "UnavailableRuntimeObservabilitySource(",
        "UnavailableBotRuntimeStateProvider(",
    ]
    result: dict[str, list[str]] = {needle: [] for needle in needles}
    files = list(PORTAL.rglob("*.py")) + list(Path("deploy").rglob("*.py"))
    for root in TEST_ROOTS:
        files.extend(root.rglob("*.py"))
    for path in sorted(set(files)):
        for line_number, line in enumerate(read(path).splitlines(), 1):
            for needle in needles:
                if needle in line and not line.lstrip().startswith("class "):
                    result[needle].append(
                        f"{relative(path)}:{line_number}: {line.strip()[:180]}"
                    )
    return result


def markdown(data: dict[str, Any]) -> str:
    summary = data["summary"]
    routes = data["backend_routes"]
    pages = data["frontend_pages"]
    bff = data["bff_handlers"]
    modules = data["backend_modules"]
    lines = [
        "# Portal deep inventory",
        "",
        f"- Audited head: `{data['audited_head']}`",
        f"- Ledger version: `{data['ledger_version']}`",
        f"- Ledger SHA-256: `{data['ledger_sha256']}`",
        f"- Backend modules: **{summary['backend_modules']}**",
        f"- Backend routes: **{summary['backend_routes']}**",
        f"- Frontend pages: **{summary['frontend_pages']}**",
        f"- BFF handlers: **{summary['bff_handlers']}**",
        f"- Test files: **{summary['tests']}**",
        "",
        "## Backend routes",
        "",
        "| Method | Route | Source |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| {item['method']} | `{item['route']}` | `{item['file']}:{item['line']}` |"
        for item in routes
    )
    lines.extend(
        [
            "",
            "## Frontend pages",
            "",
            "| Route | Source | Form | Error/empty state |",
            "|---|---|---:|---:|",
        ]
    )
    lines.extend(
        f"| `{item['route']}` | `{item['file']}` | "
        f"{'yes' if item['has_form'] else 'no'} | "
        f"{'yes' if item['explicit_unavailable'] or item['explicit_empty'] else 'no'} |"
        for item in pages
    )
    lines.extend(
        [
            "",
            "## BFF handlers",
            "",
            "| Route | Methods | Backend targets | Fixture branch | CSRF for mutations | Source |",
            "|---|---|---|---:|---:|---|",
        ]
    )
    lines.extend(
        f"| `{item['route']}` | {', '.join(item['methods']) or 'none'} | "
        f"{', '.join('`' + target + '`' for target in item['backend_targets']) or 'local/indirect'} | "
        f"{'yes' if item['fixture_branch'] else 'no'} | "
        f"{'yes' if item['csrf'] else 'no'} | `{item['file']}` |"
        for item in bff
    )
    lines.extend(
        [
            "",
            "## Backend modules",
            "",
            "| Module | Python | Routers | Repositories | Migrations | Tests | In-memory implementation | Unavailable boundary |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    lines.extend(
        f"| {item['module']} | {len(item['python_files'])} | {len(item['routers'])} | "
        f"{len(item['repositories'])} | {len(item['migrations'])} | {len(item['tests'])} | "
        f"{'yes' if item['in_memory'] else 'no'} | "
        f"{'yes' if item['unavailable_boundary'] else 'no'} |"
        for item in modules
    )
    lines.extend(["", "## Test inventory", "", "| Kind | Count |", "|---|---:|"])
    lines.extend(
        f"| {kind} | {count} |"
        for kind, count in summary["tests_by_kind"].items()
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    audited_head = resolve_exact_head(args.head)
    ledger = load_ledger()
    tests = test_inventory()
    data: dict[str, Any] = {
        "schema_version": "portal-deep-inventory-v1",
        "backend_modules": backend_modules(tests),
        "backend_routes": backend_routes(),
        "frontend_pages": frontend_pages(),
        "bff_handlers": bff_inventory(),
        "tests": tests,
        "workflows": workflow_inventory(),
        "composition_evidence": composition_evidence(),
    }
    summary = {
        "backend_modules": len(data["backend_modules"]),
        "backend_routes": len(data["backend_routes"]),
        "frontend_pages": len(data["frontend_pages"]),
        "bff_handlers": len(data["bff_handlers"]),
        "tests": len(tests),
        "tests_by_kind": {
            kind: sum(item["kind"] == kind for item in tests)
            for kind in sorted({str(item["kind"]) for item in tests})
        },
        "workflows": len(data["workflows"]),
    }
    data["summary"] = summary
    data.update(ledger_metadata(ledger, audited_head))
    validate_inventory(data, ledger)
    output = Path("artifacts")
    output.mkdir(exist_ok=True)
    (output / "portal-deep-inventory.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "portal-deep-inventory.md").write_text(markdown(data), encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0

# fmt: on


if __name__ == "__main__":
    raise SystemExit(main())
