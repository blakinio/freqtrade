#!/usr/bin/env python3
"""Generate a static completeness inventory for the AI Trading Portal."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PORTAL = Path("ai_platform/portal")
WEB = PORTAL / "web"
STATUS = Path("docs/ai_platform/portal/UI_DELIVERY_STATUS.md")
TEST_ROOTS = (
    Path("tests/ai_platform/portal"),
    Path("tests/ai_platform_integration"),
)
COMPOSITION = (
    PORTAL / "control_plane/api.py",
    PORTAL / "control_plane/api_core.py",
    PORTAL / "identity/runtime.py",
    PORTAL / "identity/public_runtime.py",
)
SKIP_MODULES = {"web", "e2e", "__pycache__"}
SEVERITY = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


@dataclass(frozen=True)
class Finding:
    """One reviewable completeness finding."""

    identifier: str
    severity: str
    area: str
    title: str
    evidence: tuple[str, ...]
    remediation: str


def repository_root(start: Path) -> Path:
    """Locate the repository root from an arbitrary working directory."""
    resolved = start.resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "AGENTS.md").exists() and (candidate / "pyproject.toml").exists():
            return candidate
    raise SystemExit("repository root not found")


def read_text(path: Path) -> str:
    """Read UTF-8 text and treat unreadable files as absent evidence."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def matching_files(path: Path, pattern: str) -> list[Path]:
    if not path.exists():
        return []
    return sorted(candidate for candidate in path.rglob(pattern) if candidate.is_file())


def normalize_route(value: str) -> str:
    """Normalize framework path parameters to one comparable representation."""
    value = value.split("?", 1)[0]
    value = re.sub(r"\[[^/]+\]|\{[^/]+\}", "{}", value)
    value = re.sub(r"/+", "/", value)
    return value.rstrip("/") or "/"


def next_route(app: Path, path: Path) -> str:
    parts = [
        part
        for part in path.relative_to(app).parts[:-1]
        if not (part.startswith("(") and part.endswith(")"))
    ]
    return normalize_route("/" + "/".join(parts))


def documented_routes(raw: str) -> dict[str, dict[str, str]]:
    """Parse the canonical product-route table from UI delivery status."""
    result: dict[str, dict[str, str]] = {}
    for line in raw.splitlines():
        if not line.startswith("|") or "`/" not in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0] == "Product surface":
            continue
        match = re.search(r"`([^`]+)`", cells[1])
        if match is None:
            continue
        for item in match.group(1).split(","):
            item = item.strip()
            if item.startswith("/"):
                result[normalize_route(item)] = {
                    "surface": cells[0],
                    "delivery": cells[2],
                    "boundary": cells[3],
                }
    return result


def fastapi_routes(path: Path, root: Path) -> list[dict[str, str]]:
    """Extract literal FastAPI routes from one Python source file."""
    raw = read_text(path)
    prefix_match = re.search(
        r"APIRouter\s*\([^)]*prefix\s*=\s*[\"']([^\"']+)",
        raw,
        re.DOTALL,
    )
    prefix = prefix_match.group(1) if prefix_match else ""
    pattern = re.compile(
        r"@(?P<object>app|router)\."
        r"(?P<method>get|post|put|patch|delete)\(\s*"
        r"[\"'](?P<path>[^\"']+)[\"']",
        re.MULTILINE,
    )
    result: list[dict[str, str]] = []
    for match in pattern.finditer(raw):
        value = match.group("path")
        if match.group("object") == "router":
            value = prefix + value
        result.append(
            {
                "method": match.group("method").upper(),
                "route": normalize_route(value),
                "file": relative(root, path),
            }
        )
    return result


def test_inventory(root: Path) -> list[Path]:
    result: set[Path] = set()
    for test_root in TEST_ROOTS:
        result.update(matching_files(root / test_root, "test_*.py"))
    result.update(matching_files(root / WEB / "e2e", "*.spec.ts"))
    result.update(matching_files(root / WEB / "e2e", "*.test.mjs"))
    return sorted(result)


def backend_inventory(root: Path, tests: list[Path]) -> list[dict[str, Any]]:
    """Inventory immediate backend modules and their supporting evidence."""
    portal = root / PORTAL
    wiring = "\n".join(read_text(root / path) for path in COMPOSITION)
    result: list[dict[str, Any]] = []
    directories = sorted(
        path for path in portal.iterdir() if path.is_dir() and path.name not in SKIP_MODULES
    )
    for directory in directories:
        python_files = matching_files(directory, "*.py")
        if not python_files:
            continue
        name = directory.name
        mapped_tests = []
        for test_path in tests:
            body = read_text(test_path)
            test_name = relative(root, test_path)
            if name in test_name or f"ai_platform.portal.{name}" in body:
                mapped_tests.append(test_name)
        paths = [relative(root, path) for path in python_files]
        result.append(
            {
                "name": name,
                "python_files": paths,
                "routers": [
                    path for path in paths if path.endswith("router.py") or path.endswith("api.py")
                ],
                "persistence": [
                    path
                    for path in paths
                    if path.endswith(("repository.py", "store.py", "database.py"))
                ],
                "migrations": [relative(root, path) for path in matching_files(directory, "*.sql")],
                "tests": mapped_tests,
                "wired": f"ai_platform.portal.{name}." in wiring,
            }
        )
    return result


def web_inventory(root: Path) -> dict[str, Any]:
    """Inventory pages, BFF handlers, API references and navigation targets."""
    app = root / WEB / "app"
    pages = {
        next_route(app, path): relative(root, path) for path in matching_files(app, "page.tsx")
    }
    handlers = {
        next_route(app, path): relative(root, path)
        for path in matching_files(app / "api", "route.ts")
    }
    source = matching_files(root / WEB, "*.ts")
    source += matching_files(root / WEB, "*.tsx")
    source += matching_files(root / WEB, "*.mjs")
    api_references: dict[str, set[str]] = defaultdict(set)
    navigation: dict[str, set[str]] = defaultdict(set)
    private_references: list[str] = []
    for path in sorted(set(source)):
        body = read_text(path)
        location = relative(root, path)
        for match in re.finditer(r"[\"'`](/v1/[^\"'`\s$]*)[\"'`]", body):
            api_references[normalize_route(match.group(1))].add(location)
        for match in re.finditer(
            r"(?:href\s*=\s*|href\s*:\s*)[\"'](/[^\"']*)[\"']",
            body,
        ):
            navigation[normalize_route(match.group(1))].add(location)
        for line_number, line in enumerate(body.splitlines(), 1):
            lowered = line.lower()
            names_private_service = any(
                token in lowered for token in ("freqtrade", "loki", "vault")
            )
            contains_url = "http://" in lowered or "https://" in lowered
            if names_private_service and contains_url:
                private_references.append(f"{location}:{line_number}: {line.strip()[:180]}")
    locale_files = [
        relative(root, path)
        for path in source
        if re.search(
            r"(i18n|locale|messages|translations)",
            relative(root, path),
            re.IGNORECASE,
        )
    ]
    return {
        "page_routes": dict(sorted(pages.items())),
        "bff_routes": dict(sorted(handlers.items())),
        "v1_refs": {key: sorted(value) for key, value in sorted(api_references.items())},
        "navigation": {key: sorted(value) for key, value in sorted(navigation.items())},
        "private_refs": private_references,
        "locale_files": locale_files,
    }


def route_exists(reference: str, routes: set[str]) -> bool:
    normalized = normalize_route(reference)
    for candidate in routes:
        if normalized == candidate:
            return True
        pattern = "^" + re.escape(candidate).replace(re.escape("{}"), "[^/]+") + "$"
        if re.match(pattern, normalized):
            return True
    return False


def pi08_evidence(root: Path) -> tuple[list[str], list[str]]:
    """Return runtime construction and fail-closed PI-08 boundary evidence."""
    wiring: list[str] = []
    boundaries: list[str] = []
    for source in matching_files(root / PORTAL, "*.py"):
        for line_number, line in enumerate(read_text(source).splitlines(), 1):
            stripped = line.strip()
            construction = (
                "execution_submitter=" in stripped
                or (
                    "PrivateSubmissionExecutionAdapter(" in stripped
                    and not stripped.startswith("class ")
                )
                or (
                    "PrivateDryRunApprovedIntentSubmitter(" in stripped
                    and not stripped.startswith("class ")
                )
            )
            if construction:
                wiring.append(f"{relative(root, source)}:{line_number}: {stripped[:180]}")
            if "ORDER_SUBMISSION_NOT_IMPLEMENTED" in stripped:
                boundaries.append(f"{relative(root, source)}:{line_number}: {stripped[:180]}")
    return wiring, boundaries


def contract_findings(
    backend_routes: set[str],
    web: dict[str, Any],
) -> list[Finding]:
    result: list[Finding] = []
    for reference, sources in sorted(web["v1_refs"].items()):
        if route_exists(reference, backend_routes):
            continue
        identifier = re.sub(r"[^a-z0-9]+", "-", reference.lower()).strip("-")
        result.append(
            Finding(
                f"CONTRACT-NO-BACKEND-{identifier}",
                "high",
                "integration",
                f"Frontend references {reference} without a matching FastAPI route",
                tuple(sources),
                "Add the producer route or correct the BFF contract and drift tests.",
            )
        )
    return result


def route_findings(
    docs: dict[str, dict[str, str]],
    web: dict[str, Any],
) -> list[Finding]:
    result: list[Finding] = []
    pages = web["page_routes"]
    for documented, status in sorted(docs.items()):
        if documented.startswith("/api/") or documented in pages:
            continue
        identifier = re.sub(r"[^a-z0-9]+", "-", documented.lower()).strip("-")
        result.append(
            Finding(
                f"UI-DOC-MISSING-{identifier}",
                "high",
                "frontend",
                f"Documented product route {documented} has no Next.js page",
                (f"{STATUS}: {status['surface']} ({status['delivery']})",),
                "Implement the page or correct the canonical delivery claim.",
            )
        )
    for target, sources in sorted(web["navigation"].items()):
        if target.startswith("/api/") or target in pages:
            continue
        identifier = re.sub(r"[^a-z0-9]+", "-", target.lower()).strip("-")
        result.append(
            Finding(
                f"UI-BROKEN-NAV-{identifier}",
                "high",
                "frontend",
                f"Navigation points to missing page {target}",
                tuple(sources),
                "Add the destination page or replace the navigation entry.",
            )
        )
    return result


def boundary_findings(root: Path, web: dict[str, Any]) -> list[Finding]:
    result: list[Finding] = []
    wiring, boundaries = pi08_evidence(root)
    if not wiring:
        evidence = boundaries + [
            "execution_submission adapter and submitter are definition-only in product code"
        ]
        result.append(
            Finding(
                "INTEGRATION-PI08-NO-RUNTIME-COMPOSITION",
                "high",
                "integration",
                "PI-08 components are not assembled in a trusted portal runtime",
                tuple(evidence),
                "Add a fail-closed server runtime factory and API-mode evidence.",
            )
        )
    if not web["locale_files"]:
        result.append(
            Finding(
                "UX-NO-LOCALIZATION",
                "medium",
                "frontend",
                "No localization or message-catalog infrastructure was detected",
                ("ai_platform/portal/web/app/layout.tsx: fixed html language",),
                "Implement locales or record an owner-approved English-only decision.",
            )
        )
    if web["private_refs"]:
        result.append(
            Finding(
                "SECURITY-BROWSER-PRIVATE-ENDPOINT",
                "critical",
                "security",
                "Browser code contains direct private-service URL references",
                tuple(web["private_refs"][:20]),
                "Keep all private services behind the same-origin BFF.",
            )
        )
    return result


def build_findings(
    root: Path,
    backend_routes: list[dict[str, str]],
    web: dict[str, Any],
    docs: dict[str, dict[str, str]],
) -> list[Finding]:
    routes = {item["route"] for item in backend_routes}
    result = contract_findings(routes, web)
    result.extend(route_findings(docs, web))
    result.extend(boundary_findings(root, web))
    return sorted(result, key=lambda item: (SEVERITY[item.severity], item.identifier))


def markdown(data: dict[str, Any]) -> str:
    """Render the machine inventory as a bounded human-readable report."""
    summary = data["summary"]
    lines = [
        "# AI Trading Portal end-to-end completeness audit",
        "",
        f"Audited head: `{data['audited_head']}`",
        "",
        "## Evidence boundary",
        "",
        "Static repository evidence only; external target acceptance is separate.",
        "",
        "## Summary",
        "",
        f"- Backend modules: **{summary['backend_modules']}**",
        f"- FastAPI routes: **{summary['backend_routes']}**",
        f"- Next.js pages: **{summary['frontend_pages']}**",
        f"- BFF handlers: **{summary['bff_routes']}**",
        f"- Canonical product routes: **{summary['documented_routes']}**",
        f"- Test files considered: **{summary['test_files']}**",
        f"- Findings: **{summary['finding_count']}**",
        "",
        "## Findings",
        "",
    ]
    findings = data["findings"]
    if not findings:
        lines.append("No static completeness findings.")
    for item in findings:
        lines.extend(
            [
                f"### {item['severity'].upper()} — {item['identifier']}",
                "",
                item["title"],
                "",
                "Evidence:",
            ]
        )
        lines.extend(f"- `{evidence}`" for evidence in item["evidence"])
        lines.extend(["", f"Required follow-up: {item['remediation']}", ""])
    lines.extend(
        [
            "## Backend module inventory",
            "",
            "| Module | Files | Routers | Persistence | Migrations | Tests | Wired |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in data["backend_modules"]:
        wired = "yes" if item["wired"] else "no"
        lines.append(
            "| "
            f"{item['name']} | {len(item['python_files'])} | "
            f"{len(item['routers'])} | {len(item['persistence'])} | "
            f"{len(item['migrations'])} | {len(item['tests'])} | {wired} |"
        )
    lines.extend(
        [
            "",
            "## Product route inventory",
            "",
            "| Route | Surface | Delivery claim | Page |",
            "|---|---|---|---|",
        ]
    )
    pages = data["web"]["page_routes"]
    for product_route, status in sorted(data["documented_routes"].items()):
        page = pages.get(product_route, "MISSING")
        lines.append(
            f"| `{product_route}` | {status['surface']} | {status['delivery']} | `{page}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--head", default="UNKNOWN")
    parser.add_argument(
        "--output-json",
        default="artifacts/portal-completeness-audit.json",
    )
    parser.add_argument(
        "--output-md",
        default="artifacts/portal-completeness-audit.md",
    )
    args = parser.parse_args()
    root = repository_root(Path(args.root))
    tests = test_inventory(root)
    modules = backend_inventory(root, tests)
    routes: list[dict[str, str]] = []
    for path in matching_files(root / PORTAL, "*.py"):
        routes.extend(fastapi_routes(path, root))
    unique = {json.dumps(item, sort_keys=True): item for item in routes}
    routes = sorted(
        unique.values(),
        key=lambda item: (item["route"], item["method"], item["file"]),
    )
    web = web_inventory(root)
    docs = documented_routes(read_text(root / STATUS))
    findings = build_findings(root, routes, web, docs)
    data: dict[str, Any] = {
        "schema_version": "portal-completeness-audit-v1",
        "audited_head": args.head,
        "summary": {
            "backend_modules": len(modules),
            "backend_routes": len(routes),
            "frontend_pages": len(web["page_routes"]),
            "bff_routes": len(web["bff_routes"]),
            "documented_routes": len(docs),
            "test_files": len(tests),
            "finding_count": len(findings),
            "by_severity": {
                severity: sum(1 for finding in findings if finding.severity == severity)
                for severity in SEVERITY
            },
        },
        "findings": [asdict(finding) for finding in findings],
        "backend_modules": modules,
        "backend_routes": routes,
        "web": web,
        "documented_routes": docs,
        "test_files": [relative(root, path) for path in tests],
    }
    output_json = root / args.output_json
    output_markdown = root / args.output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output_markdown.write_text(markdown(data), encoding="utf-8")
    print(json.dumps(data["summary"], sort_keys=True))
    for finding in findings:
        print(f"::{finding.severity}::{finding.identifier}::{finding.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
