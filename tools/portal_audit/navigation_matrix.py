#!/usr/bin/env python3
# ruff: noqa: E501
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


APP_SHELL = Path("ai_platform/portal/web/components/app-shell.tsx")
INVENTORY = Path("artifacts/portal-deep-inventory.json")
OUTPUT_JSON = Path("artifacts/portal-navigation-completeness-matrix.json")
OUTPUT_MD = Path("artifacts/portal-navigation-completeness-matrix.md")
DEVELOP_SHA = "626087ca45d67eb908d6c1f1f419f13cbd49f596"

# fmt: off

@dataclass(frozen=True)
class Surface:
    group: str
    label: str
    route: str
    frontend: str
    api_boundary: str
    backend: str
    persistence_provider: str
    tests: str
    overall: str
    issues: str
    reason: str


SURFACES = (
    Surface("Overview", "Dashboard", "/", "COMPLETE", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "PARTIAL", "#1089, #1092, #1093, #1094, #1098", "Dashboard read model exists, but authoritative runtime, valuation and observability sources are not composed and production-labelled deployment is fixture-backed."),
    Surface("Overview", "PNL & Performance", "/performance", "COMPLETE", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1092, #1093, #1098", "Rendered portfolio/bot performance cannot be authoritative without runtime collection and valuation composition."),
    Surface("Overview", "Open Positions", "/positions", "PARTIAL", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1091, #1092, #1098", "Position read model exists, but no authoritative collector is composed and documented manual exit actions are not complete."),
    Surface("Market Data", "Likwidacje", "/market/liquidations", "COMPLETE", "COMPLETE", "COMPLETE", "EXTERNAL_ACCEPTANCE_REQUIRED", "COMPLETE", "EXTERNAL_ACCEPTANCE_REQUIRED", "owner-managed source acceptance", "Repository reader, health and browser states are implemented; current real-source freshness and protected deployment acceptance remain external."),
    Surface("Market Data", "WickHunter Evidence", "/market/evidence", "COMPLETE", "COMPLETE", "COMPLETE", "EXTERNAL_ACCEPTANCE_REQUIRED", "COMPLETE", "EXTERNAL_ACCEPTANCE_REQUIRED", "owner-managed source acceptance", "Bounded same-origin evidence reader is implemented; real package/source publication and protected-target acceptance remain external."),
    Surface("Trading", "Trading Terminal", "/terminal", "PARTIAL", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1086, #1089, #1091, #1095, #1098", "Manual risk intent UI exists, but trusted approved submission is not composed and other documented terminal modes remain incomplete."),
    Surface("Trading", "Orders", "/orders", "PARTIAL", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1091, #1092, #1098", "Order read API exists, but no authoritative collection loop is composed and full order actions are not available."),
    Surface("Trading", "Trade History", "/trades", "COMPLETE", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1092, #1098", "Trade history reader exists, but production evidence is not refreshed by an authoritative private-runtime collector."),
    Surface("Bots", "View Bots", "/bots", "PARTIAL", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "PARTIAL", "#1089, #1092, #1093, #1099, #1098", "Durable bot CRUD/read paths exist, but observed runtime, valuation and desired-state execution/reconciliation are incomplete."),
    Surface("Bots", "Create Bot", "/bots/new", "COMPLETE", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1090, #1098", "Wizard and catalog validation exist, but finalization remains in memory and does not create the durable canonical bot."),
    Surface("Bots", "Signal Wizard", "/bots/signals", "PARTIAL", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1095, #1100, #1098", "Readiness view exists, but signed endpoint persistence, verifier/provider and operable UI are not composed."),
    Surface("Bots", "Strategy Catalog", "/bots/strategies", "COMPLETE", "COMPLETE", "MISSING", "MISSING", "FIXTURE_ONLY", "MISSING", "#1085, #1089, #1098", "Rich frontend and BFF expect /v1/strategy-catalog producers that do not exist."),
    Surface("Bots", "Grid Bots", "/bots/grid", "PARTIAL", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1096, #1098", "Readiness view exists, but capability provider, durable policy and canonical configuration actions are unavailable."),
    Surface("AI Intelligence", "AI Overview", "/ai", "COMPLETE", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1098, #1102", "Read APIs exist, but trusted intelligence/learning producers and model lifecycle workflows are not composed."),
    Surface("AI Intelligence", "Trade Analysis", "/ai/trade-analysis", "PARTIAL", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1098, #1102", "List view exists, while production analyses are created only through simulator/test call paths."),
    Surface("AI Intelligence", "Insights", "/ai/insights", "PARTIAL", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1098, #1102", "Insight list exists, but canonical producer plus acknowledge/dismiss/create-experiment actions are incomplete."),
    Surface("AI Intelligence", "Model Health", "/ai/model-health", "COMPLETE", "COMPLETE", "PARTIAL", "PARTIAL", "FIXTURE_ONLY", "PARTIAL", "#1089, #1098, #1102", "Telemetry ingestion and health reads exist, but a complete registered model lifecycle and trusted producer path are missing."),
    Surface("AI Intelligence", "Experiments", "/ai/experiments", "COMPLETE", "COMPLETE", "COMPLETE", "COMPLETE", "FIXTURE_ONLY", "PARTIAL", "#1089, #1098, #1102", "Strategy Lab create/read/compare persistence is implemented, but real API-mode browser proof and authorized promotion handoff are incomplete."),
    Surface("AI Intelligence", "Learning History", "/ai/learning", "PARTIAL", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1098, #1102", "History reader exists, while learning evidence is produced only by simulator/test workflows."),
    Surface("Operations", "Execution Logs", "/operations/execution-logs", "COMPLETE", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1094, #1098", "UI and query API exist, but the canonical app injects an unavailable runtime observability source."),
    Surface("Operations", "Signal Logs", "/operations/signal-logs", "COMPLETE", "COMPLETE", "COMPLETE", "PARTIAL", "FIXTURE_ONLY", "PARTIAL", "#1089, #1095, #1098", "Durable advisory signal evidence is readable, but the signed signal-control producer remains disconnected."),
    Surface("Operations", "Risk Events", "/operations/risk-events", "COMPLETE", "COMPLETE", "COMPLETE", "PARTIAL", "FIXTURE_ONLY", "PARTIAL", "#1086, #1089, #1098", "Deterministic risk decisions persist, but the full intent-to-private-execution product path and real API-mode proof are incomplete."),
    Surface("Operations", "Runtime Health", "/operations/runtime-health", "COMPLETE", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1092, #1099, #1098", "Desired/observed view exists, but no product collector and desired-state worker reconcile authoritative runtime state."),
    Surface("Operations", "Audit Events", "/operations/audit", "COMPLETE", "COMPLETE", "COMPLETE", "COMPLETE", "FIXTURE_ONLY", "PARTIAL", "#1089, #1098", "Tenant-scoped audit reads are durable and permission-gated, but real API-mode browser and deployment evidence are absent."),
    Surface("Platform", "Exchange Connections", "/platform/exchanges", "PARTIAL", "COMPLETE", "PARTIAL", "DISCONNECTED", "FIXTURE_ONLY", "DISCONNECTED", "#1089, #1097, #1100, #1098", "Public metadata is read-only; durable create/verify/rotate/revoke and Vault-backed credential composition are absent."),
    Surface("Platform", "Notifications", "/platform/notifications", "PARTIAL", "COMPLETE", "PARTIAL", "PARTIAL", "FIXTURE_ONLY", "PARTIAL", "#1089, #1098, #1104", "In-app preferences and entries work, but channel delivery, full rule families, retries and receipts are incomplete."),
    Surface("Platform", "Profile & Security", "/platform/profile", "PARTIAL", "COMPLETE", "PARTIAL", "EXTERNAL_ACCEPTANCE_REQUIRED", "FIXTURE_ONLY", "EXTERNAL_ACCEPTANCE_REQUIRED", "owner-managed identity acceptance", "Trusted identity summary exists; MFA enrollment, recovery, credential changes and real session acceptance remain external IdP responsibilities."),
    Surface("Platform", "Administration", "/platform/admin", "PARTIAL", "COMPLETE", "PARTIAL", "PARTIAL", "FIXTURE_ONLY", "PARTIAL", "#1089, #1098, #1102, #1103", "Permission-gated RBAC overview is safe but read-only; documented administration workflows are not connected."),
)


def parse_navigation() -> tuple[tuple[str, str], ...]:
    raw = APP_SHELL.read_text(encoding="utf-8")
    return tuple(re.findall(r'\{ href: "([^"]+)", label: "([^"]+)" \}', raw))


def load_inventory() -> dict[str, object]:
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def validate() -> None:
    expected = tuple((surface.route, surface.label) for surface in SURFACES)
    actual = parse_navigation()
    if actual != expected:
        raise SystemExit(f"navigation drift: expected {expected!r}, got {actual!r}")
    inventory = load_inventory()
    summary = inventory.get("summary")
    if not isinstance(summary, dict) or summary.get("backend_routes") != 92:
        raise SystemExit("backend route inventory must contain the audited 92 declarations")
    pages = inventory.get("frontend_pages")
    if not isinstance(pages, list):
        raise SystemExit("frontend page inventory missing")
    page_routes = {item.get("route") for item in pages if isinstance(item, dict)}
    missing = sorted(surface.route for surface in SURFACES if surface.route not in page_routes)
    if missing:
        raise SystemExit(f"navigation pages missing: {missing}")
    route_rows = inventory.get("backend_routes")
    if not isinstance(route_rows, list):
        raise SystemExit("backend route inventory missing")
    backend_routes = {item.get("route") for item in route_rows if isinstance(item, dict)}
    required = {
        "/v1/admin/overview",
        "/v1/audit-events",
        "/v1/bots",
        "/v1/bot-management/grid/overview",
        "/v1/bot-management/signals/overview",
        "/v1/execution-activity",
        "/v1/insights",
        "/v1/learning/history",
        "/v1/model-health",
        "/v1/notifications",
        "/v1/orders",
        "/v1/performance",
        "/v1/positions",
        "/v1/profile",
        "/v1/risk-events",
        "/v1/runtime-evidence",
        "/v1/runtime-observability/availability",
        "/v1/signals",
        "/v1/strategy-lab/experiments",
        "/v1/terminal/intents",
        "/v1/trade-analysis",
        "/v1/trades",
        "/v1/valuations",
    }
    absent = sorted(required - backend_routes)
    if absent:
        raise SystemExit(f"expected backend routes missing: {absent}")
    if any(str(route).startswith("/v1/strategy-catalog") for route in backend_routes):
        raise SystemExit("Strategy Catalog missing-producer finding no longer holds")


def markdown() -> str:
    totals: dict[str, int] = {}
    for surface in SURFACES:
        totals[surface.overall] = totals.get(surface.overall, 0) + 1
    lines = [
        "# AI Trading Portal left-navigation completeness matrix",
        "",
        f"- Audited product base: `{DEVELOP_SHA}`",
        f"- Canonical navigation items: **{len(SURFACES)}**",
        "- Global deployment gate: `FIXTURE_ONLY` (#1089).",
        "- Global real browser-to-backend gate: incomplete API-mode E2E (#1098).",
        "",
        "## Overall totals",
        "",
    ]
    for status in ("COMPLETE", "PARTIAL", "MISSING", "DISCONNECTED", "FIXTURE_ONLY", "EXTERNAL_ACCEPTANCE_REQUIRED", "BLOCKED", "NOT_APPLICABLE"):
        lines.append(f"- `{status}`: {totals.get(status, 0)}")
    lines.extend(
        [
            "",
            "## Every left-navigation item",
            "",
            "| Group | Item | Route | Frontend | API/BFF | Backend | Persistence/provider | Tests | Overall | Issue/boundary | Reason |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for surface in SURFACES:
        lines.append(
            f"| {surface.group} | {surface.label} | `{surface.route}` | {surface.frontend} | {surface.api_boundary} | {surface.backend} | {surface.persistence_provider} | {surface.tests} | **{surface.overall}** | {surface.issues} | {surface.reason} |"
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
            "No navigation item is fully end-to-end `COMPLETE` on the audited production-labelled deployment because #1089 and #1098 remain open.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    validate()
    OUTPUT_JSON.parent.mkdir(exist_ok=True)
    payload = {
        "schema_version": "portal-navigation-completeness-v1",
        "develop_sha": DEVELOP_SHA,
        "count": len(SURFACES),
        "surfaces": [asdict(surface) for surface in SURFACES],
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(markdown(), encoding="utf-8")
    print(json.dumps({"navigation_items": len(SURFACES)}, sort_keys=True))
    return 0


# fmt: on

if __name__ == "__main__":
    raise SystemExit(main())
