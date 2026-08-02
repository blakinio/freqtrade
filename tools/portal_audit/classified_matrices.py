#!/usr/bin/env python3
# ruff: noqa: E501
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA = Path("artifacts/portal-deep-inventory.json")
OUT = Path("artifacts")
DEVELOP_SHA = "626087ca45d67eb908d6c1f1f419f13cbd49f596"

# fmt: off

def parse_rules(raw: str) -> dict[str, tuple[str, str, str]]:
    return {
        key: (status, issue, reason)
        for key, status, issue, reason in (
            line.split("|", 3) for line in raw.strip().splitlines()
        )
    }


MODULES = parse_rules("""
bot_builder|DISCONNECTED|#1090|in-memory finalization does not create a durable canonical BotInstance
bot_catalog|COMPLETE|—|immutable approved dry-run catalog is constructed and tested
bot_operations|DISCONNECTED|#1091, #1086|command intent persists but runtime activation and PI-08 composition are absent
contracts|COMPLETE|—|versioned strict contracts and drift tests are present
control_plane|PARTIAL|#1089, #1099|routes exist but deployment/runtime workers and several providers are not composed
credentials|DISCONNECTED|#1100|Vault broker is implemented but product construction is test-only
dashboard|PARTIAL|#1092, #1093, #1094, #1098|read model is composed but authoritative upstream sources and API-mode E2E are missing
deploy|FIXTURE_ONLY|#1089|production-labelled package selects fixture data and identity-only backend
events|DISCONNECTED|#1099|durable outbox/inbox exist but no publisher/consumer product worker runs
exchange_connections|DISCONNECTED|#1097|in-memory repository, no credential inspection or verification worker, read-only UI
execution|DISCONNECTED|#1092, #1099|private collector and lifecycle adapter are component-only
execution_submission|DISCONNECTED|#1086|PI-08 submission/reconciliation classes are never composed
feature_registry|COMPLETE|—|read-only immutable registry is registered and tested
grid_control|DISCONNECTED|#1096|in-memory policy store, unavailable capability provider and no operable canonical UI
identity|EXTERNAL_ACCEPTANCE_REQUIRED|owner-managed|repository identity path exists; real users/MFA/recovery/restore require owner target
intelligence|PARTIAL|#1098|durable read models exist; browser-to-real-backend journey is absent
learning|PARTIAL|#1098|durable history exists; browser API-mode closure is absent
model_control|PARTIAL|#1098|durable immutable model controls exist; browser API-mode closure is absent
observability|DISCONNECTED|#1094|canonical app injects unavailable source; Loki source is test-only
operations|DISCONNECTED|#1092|durable mirror exists but no product collector/reconciliation loop refreshes it
product|PARTIAL|#1085, #1096, #1098|generic durable APIs exist but specialized producer/authority and API-mode UI gaps remain
quality_agent|COMPLETE|—|bounded deterministic validation component; no user route required
risk|PARTIAL|#1086|deterministic evaluation is complete; approved submission is not composed
security|COMPLETE|—|tenant/capability helpers and negative tests are present
signal_control|DISCONNECTED|#1095|in-memory state, unavailable verifier and no operable canonical UI
signal_wizard|PARTIAL|#1098|durable advisory evidence exists; browser API-mode closure is absent
simulator|COMPLETE|—|clearly bounded deterministic non-live simulator
strategy_lab|PARTIAL|#1098|durable research evidence exists; browser API-mode closure is absent
telemetry|PARTIAL|#1098|durable telemetry/model-health exists; browser API-mode closure is absent
valuation|DISCONNECTED|#1093|canonical app injects unavailable source; HTTP valuation source is test-only
""")

PAGE_RULES = parse_rules("""
/bots/strategies|DISCONNECTED|#1085|BFF exists but Strategy Catalog backend producer is absent
/terminal|DISCONNECTED|#1086|risk intent exists but PI-08 submitter is not composed
/bots/new|DISCONNECTED|#1090|builder finalizes only in memory and does not materialize canonical bot
/bots/detail/{}|DISCONNECTED|#1091, #1092, #1093, #1094|detail renders but lifecycle/runtime sources are not composed
/bots/grid|DISCONNECTED|#1096|readiness-only page; canonical preview/policy actions unavailable
/bots/signals|DISCONNECTED|#1095|readiness-only page; signed endpoint controls unavailable
/platform/exchanges|DISCONNECTED|#1097|read-only metadata; durable create/verify lifecycle absent
/operations/execution-logs|DISCONNECTED|#1094|runtime observability source is not composed
/positions|DISCONNECTED|#1092|mirror reader exists but no authoritative collection loop
/orders|DISCONNECTED|#1092|mirror reader exists but no authoritative collection loop
/trades|DISCONNECTED|#1092|mirror reader exists but no authoritative collection loop
/performance|DISCONNECTED|#1093|authoritative valuation source is not composed
/|PARTIAL|#1092, #1093, #1094, #1098|dashboard shell/read model exists; upstream providers and API-mode E2E are incomplete
/bots|PARTIAL|#1092, #1093, #1098|fleet renders but authoritative runtime/valuation and API-mode E2E are incomplete
/operations/runtime-health|PARTIAL|#1092, #1094, #1098|read model exists; live source loops and API-mode E2E are incomplete
/login|EXTERNAL_ACCEPTANCE_REQUIRED|owner-managed|repository identity path exists; real target recovery/restore remains external
""")

BFF_RULES = parse_rules("""
/api/strategy-catalog|DISCONNECTED|#1085|no matching backend producer
/api/strategy-catalog/{}|DISCONNECTED|#1085|no matching backend producer
/api/strategy-catalog/{}/rollback|DISCONNECTED|#1085|no matching backend producer
/api/terminal|DISCONNECTED|#1086|backend risk route exists but approved submitter is not composed
/api/bot-management/builder|DISCONNECTED|#1090|builder state is in-memory and never creates canonical bot
/api/bot-management/commands/lifecycle-intents|DISCONNECTED|#1091|runtime-state provider and activation path are unavailable
/api/bots/{}/desired-state|DISCONNECTED|#1099|desired state persists but no outbox consumer executes/reconciles runtime
/api/grid-bots|PARTIAL|#1096|generic grid authority conflicts with disconnected canonical BM-05 workflow
/api/signals|PARTIAL|#1095|generic advisory evidence is distinct from disconnected signed BM-04 control
""")

ROUTE_RULES = tuple(
    (prefix, (status, issue, reason))
    for prefix, status, issue, reason in (
        line.split("|", 3)
        for line in """
/v1/strategy-catalog|MISSING|#1085|frontend/BFF expects this producer but route is absent
/v1/bot-management/builder|DISCONNECTED|#1090|in-memory builder never materializes canonical bot
/v1/bot-management/commands|DISCONNECTED|#1091, #1086|command persistence exists; activation/submission runtime is absent
/v1/bot-management/exchanges|DISCONNECTED|#1097|in-memory state and no verification worker/provider
/v1/bot-management/grid|DISCONNECTED|#1096|capability provider unavailable and policy store in-memory
/v1/bot-management/signals|DISCONNECTED|#1095|signature provider unavailable and state in-memory
/v1/runtime-observability|DISCONNECTED|#1094|real source is not composed
/v1/valuations|DISCONNECTED|#1093|real source is not composed
/v1/positions|DISCONNECTED|#1092|reader exists but no authoritative collection/reconciliation loop
/v1/orders|DISCONNECTED|#1092|reader exists but no authoritative collection/reconciliation loop
/v1/trades|DISCONNECTED|#1092|reader exists but no authoritative collection/reconciliation loop
/v1/performance|DISCONNECTED|#1092|reader exists but no authoritative collection/reconciliation loop
/v1/runtime-states|DISCONNECTED|#1092|reader exists but no authoritative collection/reconciliation loop
/v1/execution-activity|DISCONNECTED|#1092|reader exists but no authoritative collection/reconciliation loop
/v1/terminal|DISCONNECTED|#1086|approved submission is not composed
/v1/bot-management/dashboard|PARTIAL|#1092, #1093, #1094|upstream authoritative sources are disconnected
/v1/bot-management/catalog|COMPLETE|—|immutable approved catalog is constructed
""".strip().splitlines()
    )
)

STATUS_ORDER = ["COMPLETE", "PARTIAL", "MISSING", "DISCONNECTED", "FIXTURE_ONLY", "EXTERNAL_ACCEPTANCE_REQUIRED", "BLOCKED", "NOT_APPLICABLE"]


def route_status(route: str) -> tuple[str, str, str]:
    if route.startswith("/v1/bots") and "desired-state" in route:
        return ("DISCONNECTED", "#1099", "desired-state event is not consumed by a runtime worker")
    if route == "/healthz" or route.startswith("/v1/identity"):
        return ("EXTERNAL_ACCEPTANCE_REQUIRED", "owner-managed", "repository identity route exists; protected target acceptance remains external")
    for prefix, result in ROUTE_RULES:
        if route.startswith(prefix):
            return result
    return ("PARTIAL", "#1098", "backend route exists; API-mode browser closure is missing")


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *("| " + " | ".join(row) + " |" for row in rows),
    ])


def module_matrix(data: dict[str, Any]) -> str:
    rows = []
    for item in data["backend_modules"]:
        status, issue, reason = MODULES[item["module"]]
        rows.append([f"`{item['module']}`", status, reason, str(len(item["routers"])), str(len(item["repositories"])), str(len(item["migrations"])), str(len(item["tests"])), issue])
    counts = {key: 0 for key in STATUS_ORDER}
    for status, _issue, _reason in MODULES.values():
        counts[status] += 1
    route_rows = []
    for item in data["backend_routes"]:
        status, issue, reason = route_status(item["route"])
        route_rows.append([item["method"], f"`{item['route']}`", f"`{item['file']}:{item['line']}`", status, reason, issue])
    return "\n".join([
        "# AI Trading Portal backend completeness matrix", "", f"- Audited product base: `{DEVELOP_SHA}`",
        "- Evidence: exact-head static inventory plus repository tests; protected target acceptance is separate.", "",
        "## Module matrix", "", md_table(["Module", "Status", "Reason", "Routers", "Repositories", "Migrations", "Tests", "Issue/boundary"], rows), "",
        "## Module status totals", "", *(f"- `{key}`: {counts[key]}" for key in STATUS_ORDER), "",
        "## All FastAPI route declarations", "", md_table(["Method", "Route", "Source", "Status", "Reason", "Issue/boundary"], route_rows), "",
        "Expected but absent Strategy Catalog producers are recorded in #1085 and are not counted among the 92 declarations.", "",
    ])


def page_status(route: str) -> tuple[str, str, str]:
    if route in PAGE_RULES:
        return PAGE_RULES[route]
    if route in {"/denied", "/market/evidence", "/market/liquidations", "/market/wickhunter"}:
        return ("COMPLETE", "external source acceptance where applicable", "bounded page/source boundary is explicit")
    return ("PARTIAL", "#1098", "page exists; API-mode browser-to-real-backend closure is missing")


def bff_status(route: str) -> tuple[str, str, str]:
    if route in BFF_RULES:
        return BFF_RULES[route]
    if route.startswith("/api/identity/"):
        return ("EXTERNAL_ACCEPTANCE_REQUIRED", "owner-managed", "repository session boundary exists; real identity target acceptance remains external")
    if route.startswith("/api/market/"):
        return ("COMPLETE", "external feed acceptance where applicable", "same-origin bounded local/package reader")
    return ("PARTIAL", "#1098", "handler exists; complete API-mode browser integration is not proven")


def frontend_matrix(data: dict[str, Any]) -> str:
    pages = []
    for item in data["frontend_pages"]:
        status, issue, reason = page_status(item["route"])
        pages.append([f"`{item['route']}`", f"`{item['file']}`", status, reason, "yes" if item["has_form"] else "no", "yes" if item["explicit_unavailable"] or item["explicit_empty"] else "no", issue])
    bff = []
    for item in data["bff_handlers"]:
        status, issue, reason = bff_status(item["route"])
        targets = ", ".join(f"`{value}`" for value in item["backend_targets"]) or "local/indirect"
        bff.append([f"`{item['route']}`", ", ".join(item["methods"]) or "none", targets, status, reason, "yes" if item["fixture_branch"] else "no", "yes" if item["csrf"] else "no", issue])
    return "\n".join([
        "# AI Trading Portal frontend and BFF completeness matrix", "", f"- Audited product base: `{DEVELOP_SHA}`", "",
        "## All Next.js pages", "", md_table(["Page", "Source", "Status", "Reason", "Form", "Explicit state", "Issue/boundary"], pages), "",
        "## All same-origin BFF handlers", "", md_table(["BFF route", "Methods", "Backend targets", "Status", "Reason", "Fixture branch", "CSRF", "Issue/boundary"], bff), "",
        "Canonical navigation inventory is validated separately by the basic completeness tool; no broken destination was detected.", "",
    ])


def runtime_matrix(data: dict[str, Any]) -> str:
    comp_rows = []
    for needle, refs in data["composition_evidence"].items():
        product = [value for value in refs if "/tests/" not in value and not value.startswith("tests/")]
        test_refs = [value for value in refs if value not in product]
        status = "COMPOSED" if product and not needle.startswith(("InMemory", "Unavailable")) else "TEST_ONLY/DEFAULT_BOUNDARY"
        comp_rows.append([f"`{needle}`", status, str(len(product)), str(len(test_refs)), "<br>".join((product + test_refs)[:3]) or "none"])
    test_counts: dict[str, int] = {}
    for item in data["tests"]:
        kind = str(item["kind"])
        test_counts[kind] = test_counts.get(kind, 0) + 1
    workflows = [[f"`{item['name']}`", f"`{item['file']}`", "security" if item["security"] else "validation"] for item in data["workflows"]]
    fixture_rows = [
        ["Next.js `PORTAL_WEB_DATA_MODE=fixture`", "FIXTURE", "UI navigation/states and same-origin shape", "real backend, persistence or provider"],
        ["Playwright fixture identity/data", "FIXTURE/MOCK", "browser interaction and accessibility regressions", "real identity or API-mode E2E"],
        ["FastAPI tests with injected fakes", "UNIT/INTEGRATION", "route/service contracts", "canonical product composition"],
        ["deterministic simulator", "SIMULATOR", "bounded non-live execution semantics", "real private Freqtrade acceptance"],
        ["Synology/Docker package validation", "DEPLOYMENT_PACKAGE", "secret-free packaging and topology checks", "real Synology/Cloudflare/Auth/Vault acceptance"],
        ["owner protected targets", "REAL_ACCEPTANCE_REQUIRED", "only after owner-run evidence", "not exercised by this audit"],
    ]
    deployment_rows = [
        ["Full Portal Synology candidate", "FIXTURE_ONLY", "production-labelled web uses fixture data and identity-only backend; #1089"],
        ["Authentik users/MFA/recovery/restore", "EXTERNAL_ACCEPTANCE_REQUIRED", "owner-managed protected target"],
        ["Vault initialization/unseal/rotation/restore", "EXTERNAL_ACCEPTANCE_REQUIRED", "owner-managed after repository composition #1100"],
        ["Cloudflare protected ingress/DNS", "EXTERNAL_ACCEPTANCE_REQUIRED", "owner-managed infrastructure"],
        ["Real private dry-run Freqtrade target", "EXTERNAL_ACCEPTANCE_REQUIRED", "after repository composition findings close"],
        ["P14 live-small/live capital", "BLOCKED", "no authorization; outside audit"],
    ]
    return "\n".join([
        "# AI Trading Portal runtime, fixture, test and deployment matrix", "", f"- Audited product base: `{DEVELOP_SHA}`", "",
        "## Runtime composition roots and boundaries", "", md_table(["Symbol/construction", "Classification", "Product refs", "Test refs", "Evidence sample"], comp_rows), "",
        "## Fixture/mock/provider boundary", "", md_table(["Path/evidence", "Classification", "Proves", "Does not prove"], fixture_rows), "",
        "## Test inventory", "", md_table(["Kind", "Files", "Audit interpretation"], [[f"`{kind}`", str(count), "exact file list in deep inventory JSON"] for kind, count in sorted(test_counts.items())]), "",
        "Browser conclusion: 30 browser E2E files were inventoried; default fixture identity/data and request interception do not prove the real composed API path. See #1098.", "",
        "## Relevant workflow inventory", "", md_table(["Workflow", "File", "Role"], workflows), "",
        "## Deployment and external acceptance", "", md_table(["Area", "Status", "Reason"], deployment_rows), "",
    ])


def main() -> int:
    data: dict[str, Any] = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    outputs = {
        "portal-backend-matrix.md": module_matrix(data),
        "portal-frontend-bff-matrix.md": frontend_matrix(data),
        "portal-runtime-test-deployment-matrix.md": runtime_matrix(data),
    }
    for name, content in outputs.items():
        (OUT / name).write_text(content, encoding="utf-8")
    print(json.dumps({name: len(content.splitlines()) for name, content in outputs.items()}, sort_keys=True))
    return 0

# fmt: on

if __name__ == "__main__":
    raise SystemExit(main())
