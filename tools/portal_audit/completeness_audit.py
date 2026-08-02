#!/usr/bin/env python3
"""Generate a static end-to-end completeness inventory for the AI Trading Portal."""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

PORTAL = Path("ai_platform/portal")
WEB = PORTAL / "web"
STATUS = Path("docs/ai_platform/portal/UI_DELIVERY_STATUS.md")
TEST_ROOTS = (Path("tests/ai_platform/portal"), Path("tests/ai_platform_integration"))
COMPOSITION = (
    PORTAL / "control_plane/api.py",
    PORTAL / "control_plane/api_core.py",
    PORTAL / "identity/runtime.py",
    PORTAL / "identity/public_runtime.py",
)
SKIP_MODULES = {"web", "e2e", "__pycache__"}
MARKERS = re.compile(r"\b(TODO|FIXME|XXX|NotImplementedError)\b", re.I)
SEVERITY = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


@dataclass(frozen=True)
class Finding:
    id: str
    severity: str
    area: str
    title: str
    evidence: tuple[str, ...]
    remediation: str


def root_from(start: Path) -> Path:
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "AGENTS.md").exists() and (candidate / "pyproject.toml").exists():
            return candidate
    raise SystemExit("repository root not found")


def text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def files(path: Path, pattern: str) -> list[Path]:
    return sorted(p for p in path.rglob(pattern) if p.is_file()) if path.exists() else []


def route(value: str) -> str:
    value = value.split("?", 1)[0]
    value = re.sub(r"\[[^/]+\]|\{[^/]+\}", "{}", value)
    value = re.sub(r"/+", "/", value)
    return value.rstrip("/") or "/"


def next_route(app: Path, path: Path) -> str:
    parts = [p for p in path.relative_to(app).parts[:-1] if not (p.startswith("(") and p.endswith(")"))]
    return route("/" + "/".join(parts))


def documented_routes(raw: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for line in raw.splitlines():
        if not line.startswith("|") or "`/" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0] == "Product surface":
            continue
        match = re.search(r"`([^`]+)`", cells[1])
        if not match:
            continue
        for item in match.group(1).split(","):
            item = item.strip()
            if item.startswith("/"):
                result[route(item)] = {"surface": cells[0], "delivery": cells[2], "boundary": cells[3]}
    return result


def fastapi_routes(path: Path, root: Path) -> list[dict[str, str]]:
    raw = text(path)
    prefix_match = re.search(r"APIRouter\s*\([^)]*prefix\s*=\s*[\"']([^\"']+)", raw, re.S)
    prefix = prefix_match.group(1) if prefix_match else ""
    pattern = re.compile(
        r"@(?P<obj>app|router)\.(?P<method>get|post|put|patch|delete)\(\s*[\"'](?P<path>[^\"']+)[\"']",
        re.M,
    )
    found = []
    for match in pattern.finditer(raw):
        value = match.group("path")
        if match.group("obj") == "router":
            value = prefix + value
        found.append({"method": match.group("method").upper(), "route": route(value), "file": rel(root, path)})
    return found


def marker_lines(root: Path, candidates: list[Path]) -> list[str]:
    result = []
    for path in candidates:
        for number, line in enumerate(text(path).splitlines(), 1):
            if MARKERS.search(line):
                result.append(f"{rel(root, path)}:{number}: {line.strip()[:180]}")
    return result


def test_inventory(root: Path) -> list[Path]:
    result: set[Path] = set()
    for test_root in TEST_ROOTS:
        result.update(files(root / test_root, "test_*.py"))
    result.update(files(root / WEB / "e2e", "*.spec.ts"))
    result.update(files(root / WEB / "e2e", "*.test.mjs"))
    return sorted(result)


def backend_inventory(root: Path, tests: list[Path]) -> list[dict[str, object]]:
    portal = root / PORTAL
    wiring = "\n".join(text(root / p) for p in COMPOSITION)
    modules = []
    for directory in sorted(p for p in portal.iterdir() if p.is_dir() and p.name not in SKIP_MODULES):
        py = files(directory, "*.py")
        if not py:
            continue
        name = directory.name
        mapped_tests = []
        for test_path in tests:
            body = text(test_path)
            test_rel = rel(root, test_path)
            if name in test_rel or f"ai_platform.portal.{name}" in body:
                mapped_tests.append(test_rel)
        py_rel = [rel(root, p) for p in py]
        modules.append(
            {
                "name": name,
                "python_files": py_rel,
                "routers": [p for p in py_rel if p.endswith("router.py") or p.endswith("api.py")],
                "services": [p for p in py_rel if p.endswith("service.py") or p.endswith("services.py")],
                "persistence": [p for p in py_rel if p.endswith(("repository.py", "store.py", "database.py"))],
                "schemas": [p for p in py_rel if p.endswith("schema.py") or "/contracts/" in p],
                "migrations": [rel(root, p) for p in files(directory, "*.sql")],
                "tests": mapped_tests,
                "wired": f"ai_platform.portal.{name}." in wiring,
                "markers": marker_lines(root, py),
            }
        )
    return modules


def web_inventory(root: Path) -> dict[str, object]:
    app = root / WEB / "app"
    pages = {next_route(app, p): rel(root, p) for p in files(app, "page.tsx")}
    handlers = {next_route(app, p): rel(root, p) for p in files(app / "api", "route.ts")}
    source = files(root / WEB, "*.ts") + files(root / WEB, "*.tsx") + files(root / WEB, "*.mjs")
    v1_refs: dict[str, set[str]] = defaultdict(set)
    hrefs: dict[str, set[str]] = defaultdict(set)
    private_refs = []
    for path in sorted(set(source)):
        body = text(path)
        where = rel(root, path)
        for match in re.finditer(r"[\"'`](/v1/[^\"'`\s$]*)[\"'`]", body):
            v1_refs[route(match.group(1))].add(where)
        for match in re.finditer(r"(?:href\s*=\s*|href\s*:\s*)[\"'](/[^\"']*)[\"']", body):
            hrefs[route(match.group(1))].add(where)
        for line_no, line in enumerate(body.splitlines(), 1):
            lowered = line.lower()
            if ("freqtrade" in lowered or "loki" in lowered or "vault" in lowered) and (
                "http://" in lowered or "https://" in lowered
            ):
                private_refs.append(f"{where}:{line_no}: {line.strip()[:180]}")
    support = {
        "loading": [rel(root, p) for p in files(app, "loading.tsx")],
        "error": [rel(root, p) for p in files(app, "error.tsx")],
        "not_found": [rel(root, p) for p in files(app, "not-found.tsx")],
        "locale": [
            rel(root, p)
            for p in source
            if re.search(r"(i18n|locale|messages|translations)", rel(root, p), re.I)
        ],
    }
    return {
        "page_routes": dict(sorted(pages.items())),
        "bff_routes": dict(sorted(handlers.items())),
        "v1_refs": {k: sorted(v) for k, v in sorted(v1_refs.items())},
        "navigation": {k: sorted(v) for k, v in sorted(hrefs.items())},
        "private_refs": private_refs,
        "support": support,
    }


def equivalent_backend(reference: str, routes: set[str]) -> bool:
    normalized = route(reference)
    for candidate in routes:
        if normalized == candidate:
            return True
        pattern = "^" + re.escape(candidate).replace(re.escape("{}"), "[^/]+") + "$"
        if re.match(pattern, normalized):
            return True
    return False


def findings(
    root: Path,
    modules: list[dict[str, object]],
    backend_routes: list[dict[str, str]],
    web: dict[str, object],
    docs: dict[str, dict[str, str]],
) -> list[Finding]:
    result: list[Finding] = []
    pages: dict[str, str] = web["page_routes"]  # type: ignore[assignment]
    bff: dict[str, str] = web["bff_routes"]  # type: ignore[assignment]
    refs: dict[str, list[str]] = web["v1_refs"]  # type: ignore[assignment]
    nav: dict[str, list[str]] = web["navigation"]  # type: ignore[assignment]
    support: dict[str, list[str]] = web["support"]  # type: ignore[assignment]
    private_refs: list[str] = web["private_refs"]  # type: ignore[assignment]
    backend_set = {item["route"] for item in backend_routes}

    pi08_wiring: list[str] = []
    pi08_boundary: list[str] = []
    for source in files(root / PORTAL, "*.py"):
        for line_no, line in enumerate(text(source).splitlines(), 1):
            stripped = line.strip()
            if (
                "execution_submitter=" in stripped
                or ("PrivateSubmissionExecutionAdapter(" in stripped and not stripped.startswith("class "))
                or ("PrivateDryRunApprovedIntentSubmitter(" in stripped and not stripped.startswith("class "))
            ):
                pi08_wiring.append(f"{rel(root, source)}:{line_no}: {stripped[:180]}")
            if "ORDER_SUBMISSION_NOT_IMPLEMENTED" in stripped:
                pi08_boundary.append(f"{rel(root, source)}:{line_no}: {stripped[:180]}")
    if not pi08_wiring:
        result.append(Finding(
            "INTEGRATION-PI08-NO-RUNTIME-COMPOSITION", "high", "integration",
            "PI-08 submission components are not assembled in a trusted portal runtime",
            tuple(pi08_boundary + [
                "ai_platform/portal/execution_submission/adapter.py: PrivateSubmissionExecutionAdapter is definition-only",
                "ai_platform/portal/execution_submission/integration.py: PrivateDryRunApprovedIntentSubmitter is definition-only",
            ]),
            "Add one fail-closed server-side runtime factory that injects the real snapshot provider and PI-08 submitter into TerminalService/ExecutionAdapter, then prove API-mode submission and reconciliation without browser access to private Freqtrade.",
        ))

    ignored_doc_routes = {"/api/identity/*"}
    for documented, status in sorted(docs.items()):
        if documented in ignored_doc_routes or documented.startswith("/api/"):
            continue
        if documented not in pages:
            result.append(Finding(
                f"UI-DOC-MISSING-{re.sub(r'[^a-z0-9]+', '-', documented.lower()).strip('-')}",
                "high", "frontend", f"Documented product route {documented} has no Next.js page",
                (f"{STATUS}: {status['surface']} ({status['delivery']})",),
                "Implement the page or correct the canonical delivery-status claim and register a dependent task.",
            ))
    for target, sources in sorted(nav.items()):
        if target.startswith("/api/") or target in pages:
            continue
        result.append(Finding(
            f"UI-BROKEN-NAV-{re.sub(r'[^a-z0-9]+', '-', target.lower()).strip('-')}",
            "high", "frontend", f"Navigation points to missing page {target}", tuple(sources),
            "Add the destination page or remove/replace the navigation entry.",
        ))
    for reference, sources in sorted(refs.items()):
        if not equivalent_backend(reference, backend_set):
            result.append(Finding(
                f"CONTRACT-NO-BACKEND-{re.sub(r'[^a-z0-9]+', '-', reference.lower()).strip('-')}",
                "high", "integration", f"Frontend references {reference} but no matching FastAPI route was detected",
                tuple(sources), "Wire the producer route or correct the BFF contract and add drift coverage.",
            ))
    for module in modules:
        routers = module["routers"]
        tests = module["tests"]
        if routers and not module["wired"]:
            result.append(Finding(
                f"BACKEND-UNWIRED-{module['name']}", "high", "backend",
                f"Router-bearing module {module['name']} is not detected in canonical composition roots",
                tuple(routers), "Wire it into the product application or mark it internal/partial with an exact consumer task.",
            ))
        if routers and not tests:
            result.append(Finding(
                f"BACKEND-NO-FOCUSED-TEST-{module['name']}", "medium", "testing",
                f"Router-bearing module {module['name']} has no focused mapped test",
                tuple(routers), "Add focused contract/API tests or document the exact shared suite that proves it.",
            ))
        markers = module["markers"]
        if markers:
            sev = "high" if any("ORDER_SUBMISSION_NOT_IMPLEMENTED" in item for item in markers) else "medium"
            result.append(Finding(
                f"BACKEND-MARKERS-{module['name']}", sev, "backend",
                f"Module {module['name']} contains explicit incompleteness markers", tuple(markers[:12]),
                "Resolve each marker or retain an explicit partial status, dependent task and non-completion claim.",
            ))
    if not support["locale"]:
        result.append(Finding(
            "UX-NO-LOCALIZATION", "medium", "frontend", "No localization/message-catalog infrastructure was detected",
            (rel(root, root / WEB / "app/layout.tsx"), "Root layout uses a fixed html language."),
            "Add locale-aware messages/formatting or record a product decision that localization is not applicable.",
        ))
    if not support["loading"]:
        result.append(Finding(
            "UX-NO-LOADING-BOUNDARY", "medium", "frontend", "No Next.js loading.tsx boundary was detected",
            (rel(root, root / WEB / "app"),),
            "Add loading boundaries or prove an equivalent explicit loading-state strategy for every data-backed surface.",
        ))
    if not support["error"]:
        result.append(Finding(
            "UX-NO-ERROR-BOUNDARY", "medium", "frontend", "No Next.js error.tsx boundary was detected",
            (rel(root, root / WEB / "app"),),
            "Add recoverable error boundaries and browser E2E for network/server failure and retry.",
        ))
    if private_refs:
        result.append(Finding(
            "SECURITY-BROWSER-PRIVATE-ENDPOINT", "critical", "security",
            "Browser code contains direct private-service URL references", tuple(private_refs[:20]),
            "Remove direct browser access and keep private services behind the same-origin BFF.",
        ))
    if not bff:
        result.append(Finding(
            "INTEGRATION-NO-BFF", "critical", "integration", "No same-origin BFF handlers were detected",
            (rel(root, root / WEB / "app"),), "Implement the BFF required by the portal trust boundary.",
        ))
    return sorted(result, key=lambda item: (SEVERITY[item.severity], item.id))


def markdown(data: dict[str, object]) -> str:
    summary = data["summary"]
    found = data["findings"]
    modules = data["backend_modules"]
    docs = data["documented_routes"]
    pages = data["web"]["page_routes"]  # type: ignore[index]
    lines = [
        "# AI Trading Portal end-to-end completeness audit", "",
        f"Audited head: `{data['audited_head']}`", "",
        "## Evidence boundary", "",
        "This is a static repository audit. It proves file, route, wiring, migration, test and explicit-marker evidence on the audited head. It does not prove real Authentik, Synology, Vault, private Freqtrade, Loki/Tempo/Prometheus or Cloudflare target acceptance.", "",
        "## Summary", "",
        f"- Backend modules: **{summary['backend_modules']}**",  # type: ignore[index]
        f"- FastAPI routes: **{summary['backend_routes']}**",  # type: ignore[index]
        f"- Next.js pages: **{summary['frontend_pages']}**",  # type: ignore[index]
        f"- BFF handlers: **{summary['bff_routes']}**",  # type: ignore[index]
        f"- Canonical product routes: **{summary['documented_routes']}**",  # type: ignore[index]
        f"- Test files considered: **{summary['test_files']}**",  # type: ignore[index]
        f"- Findings: **{summary['finding_count']}**", "",  # type: ignore[index]
        "## Findings", "",
    ]
    if not found:
        lines.append("No static completeness findings. Real-target and runtime gates still apply.")
    for item in found:  # type: ignore[assignment]
        lines.extend([f"### {item['severity'].upper()} — {item['id']}: {item['title']}", "", f"Area: `{item['area']}`", "", "Evidence:"])
        lines.extend(f"- `{e}`" for e in item["evidence"])
        lines.extend(["", f"Required follow-up: {item['remediation']}", ""])
    lines.extend(["## Backend module inventory", "", "| Module | Files | Routers | Persistence | Migrations | Tests | Wired | Markers |", "|---|---:|---:|---:|---:|---:|---:|---:|"])
    for item in modules:  # type: ignore[assignment]
        lines.append(f"| {item['name']} | {len(item['python_files'])} | {len(item['routers'])} | {len(item['persistence'])} | {len(item['migrations'])} | {len(item['tests'])} | {'yes' if item['wired'] else 'no'} | {len(item['markers'])} |")
    lines.extend(["", "## Product route inventory", "", "| Route | Surface | Delivery claim | Page |", "|---|---|---|---|"])
    for item_route, status in sorted(docs.items()):  # type: ignore[union-attr]
        lines.append(f"| `{item_route}` | {status['surface']} | {status['delivery']} | `{pages.get(item_route, 'MISSING')}` |")
    lines.extend(["", "## Classification", "", "- `PROVEN`: static repository evidence on the exact audited head.", "- `DERIVED`: completeness risk inferred from absent wiring, route, test or UX boundary.", "- `UNKNOWN`: real external target availability and owner-operated identity/recovery journeys.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--head", default="UNKNOWN")
    parser.add_argument("--output-json", default="artifacts/portal-completeness-audit.json")
    parser.add_argument("--output-md", default="artifacts/portal-completeness-audit.md")
    args = parser.parse_args()
    root = root_from(Path(args.root))
    tests = test_inventory(root)
    modules = backend_inventory(root, tests)
    routes = []
    for path in files(root / PORTAL, "*.py"):
        routes.extend(fastapi_routes(path, root))
    routes = sorted({json.dumps(x, sort_keys=True): x for x in routes}.values(), key=lambda x: (x["route"], x["method"], x["file"]))
    web = web_inventory(root)
    docs = documented_routes(text(root / STATUS))
    found = findings(root, modules, routes, web, docs)
    data: dict[str, object] = {
        "schema_version": "portal-completeness-audit-v1",
        "audited_head": args.head,
        "summary": {
            "backend_modules": len(modules), "backend_routes": len(routes),
            "frontend_pages": len(web["page_routes"]), "bff_routes": len(web["bff_routes"]),
            "documented_routes": len(docs), "test_files": len(tests), "finding_count": len(found),
            "by_severity": {name: sum(1 for f in found if f.severity == name) for name in SEVERITY},
        },
        "findings": [asdict(x) for x in found], "backend_modules": modules,
        "backend_routes": routes, "web": web, "documented_routes": docs,
        "test_files": [rel(root, p) for p in tests],
    }
    out_json, out_md = root / args.output_json, root / args.output_md
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out_md.write_text(markdown(data) + "\n", encoding="utf-8")
    print(json.dumps(data["summary"], sort_keys=True))
    for item in found:
        print(f"::{item.severity}::{item.id}::{item.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
