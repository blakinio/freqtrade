# AI Trading Portal — end-to-end completeness audit

## Audit identity

```yaml
audited_repository: blakinio/freqtrade
audited_product_branch: develop
audited_develop_head_at_closeout: 79065e29de8d949701e1465fc99cb6b6e8c4857e
audited_portal_implementation_head: 0e7825bf860cd8011e1bd9207fcb0765baf8d52a
audit_branch: audit/portal-e2e-completeness-20260802
audit_pr: 1082
prompting_standard_version: 2.1
audit_date: 2026-08-02
audit_type: static_repository_and_delivery_matrix
```

The only `develop` change after the implementation head was the documentation-only login incident closeout in commit `79065e29de8d949701e1465fc99cb6b6e8c4857e`. It changed two task records and no portal backend, frontend, tests, migrations or deployment implementation. The final audit workflow ran against the current PR merge base containing that closeout.

The audit branch adds only audit tooling, workflow evidence, this report and remediation task records. Portal backend/frontend behavior is unchanged.

## Method and evidence boundary

The audit compared:

- every immediate Python module under `ai_platform/portal`;
- statically detectable FastAPI routes and canonical composition roots;
- every Next.js `page.tsx` route and same-origin BFF `route.ts` handler;
- frontend `/v1/*` producer expectations;
- `UI_DELIVERY_STATUS.md` delivery claims;
- migrations and focused Python/browser test ownership;
- explicit incomplete/default-fail-closed boundaries;
- current portal program, PR, CI and deployment documentation.

Evidence classes:

- `PROVEN` — exact repository files, routes, references, tests, migrations and workflow output;
- `DERIVED` — completeness risk inferred from missing producer, consumer or product composition;
- `UNKNOWN` — real external target behavior not exercised by this static audit.

Static or fixture evidence is not accepted as proof of real Authentik, Vault, private Freqtrade, Loki/Tempo/Prometheus, Synology recovery or Cloudflare acceptance.

## Executive conclusion

**The portal is not fully complete end to end.** Most repository-side product surfaces exist and are covered by substantial tests, but two integration gaps prevent a full completion claim:

1. Strategy Catalog has a frontend, BFF and fixture E2E, but its API-mode backend producer is absent.
2. PI-08 private dry-run submission components exist and are tested in isolation, but no trusted product runtime assembles or injects them; canonical defaults remain fail-closed.

A third gap concerns product localization: the application is fixed to English and has no message-catalog boundary. This requires either implementation or an explicit owner decision that the portal is English-only.

Inventory result:

| Inventory | Count |
|---|---:|
| Backend modules | 30 |
| Statically detected FastAPI routes | 92 |
| Next.js pages | 33 |
| Same-origin BFF handlers | 28 |
| Canonical documented product routes | 29 |
| Focused/backend/browser test files considered | 225 |
| Missing documented pages | 0 |
| Broken detected navigation destinations | 0 |
| Direct browser references to private Freqtrade/Vault/Loki URLs | 0 |
| Actionable findings | 3: 2 high, 1 medium |

## New actionable findings

### F-01 — HIGH — Strategy Catalog API producer is missing

`ai_platform/portal/web/lib/strategy-catalog-api.ts` calls:

- `GET /v1/strategy-catalog`;
- `GET /v1/strategy-catalog/{strategy_version}`;
- `POST /v1/strategy-catalog/{strategy_version}/rollback`.

No matching FastAPI route exists among the detected backend routes. The BFF and browser surface can pass fixture-mode tests, but API mode cannot complete the vertical slice. The current `integrated` delivery claim is therefore too strong.

Remediation task: `FTAI-20260802-portal-strategy-catalog-backend-closure`.

### F-02 — HIGH — PI-08 components are not composed into a product runtime

The repository contains:

- `PrivateDryRunApprovedIntentSubmitter`;
- `PrivateSubmissionExecutionAdapter`;
- durable private submission, transport and reconciliation components;
- focused tests for these components.

Exact-head search found construction only in focused tests. No product code instantiates either PI-08 composition component or injects `execution_submitter=`. The canonical defaults in `execution/adapter.py` and `risk/terminal.py` still return `ORDER_SUBMISSION_NOT_IMPLEMENTED` unless an external caller supplies overrides.

This is safe fail-closed behavior, but it means the server-side PI-08 vertical slice is a component library rather than a completed product runtime.

Remediation task: `FTAI-20260802-portal-pi08-runtime-composition-closure`.

### F-03 — MEDIUM — Localization boundary is absent

No locale, translation or message-catalog infrastructure was detected. `web/app/layout.tsx` fixes the document language to English. Under prompting standard 2.1, localization is part of a user-facing vertical slice unless explicitly declared not applicable.

Remediation/decision task: `FTAI-20260802-portal-localization-boundary`.

## Backend module matrix

Status vocabulary:

- `COMPLETE_REPO` — repository-side implementation, wiring and focused evidence are present for its declared bounded scope;
- `NEEDS_REMEDIATION` — a required producer or product composition is missing;
- `PARTIAL_REPO` — intentionally bounded implementation remains incomplete for a wider user workflow;
- `TARGET_BLOCKED` — repository implementation exists but real provider/target acceptance is still external;
- `INTERNAL_ONLY` — supporting module with no independent user-facing completion claim.

| Backend module | Backend status | Frontend/consumer status | Conclusion and required action |
|---|---|---|---|
| `bot_builder` | COMPLETE_REPO | `/bots/new` integrated | Complete for dry-run creation; real execution still depends on PI-08 target/runtime closure. |
| `bot_catalog` | COMPLETE_REPO | Used by bot creation/management | Complete for bot template/catalog contracts; distinct from the incomplete Strategy Catalog surface. |
| `bot_operations` | COMPLETE_REPO | Bot detail lifecycle/command controls integrated | Repository-complete with reconciliation semantics; real private target remains external. |
| `contracts` | INTERNAL_ONLY | Shared across BFF/backend | Broad versioned contract coverage exists. Keep drift tests mandatory. |
| `control_plane` | NEEDS_REMEDIATION | Most BFF surfaces integrated | Missing Strategy Catalog producer and trusted PI-08 runtime composition prevent full closure. |
| `credentials` | COMPLETE_REPO / TARGET_BLOCKED | Exchange metadata hides secrets | Vault broker contracts exist; real initialization, enrollment and restore acceptance remain external. |
| `dashboard` | COMPLETE_REPO | `/` integrated | Server-owned read model complete; source-specific unavailable/partial states are intentional. |
| `deploy` | TARGET_BLOCKED | No direct product page | Repository deployment policies exist; Cloudflare and remaining real-target acceptance remain external. |
| `events` | INTERNAL_ONLY | Feeds audit/operations | Outbox/inbox foundation and tests exist; no independent UI required. |
| `exchange_connections` | COMPLETE_REPO / TARGET_BLOCKED | `/platform/exchanges` integrated metadata/lifecycle | Repository flow complete without browser secrets; real Vault/exchange enrollment remains external. |
| `execution` | NEEDS_REMEDIATION | Terminal/bot operations consume execution contracts | Lifecycle/private reads exist, but approved-intent default is still unimplemented without PI-08 composition. |
| `execution_submission` | NEEDS_REMEDIATION | No direct browser consumer by design | Components and tests exist; add trusted server runtime assembly and API-mode evidence. |
| `feature_registry` | COMPLETE_REPO | Strategy/research consumers | Complete for its research-only bounded role. |
| `grid_control` | PARTIAL_REPO | `/bots/grid` partially integrated | Persisted dry-run control exists; exposure-increasing activation depends on completed PI-08 composition/target evidence. |
| `identity` | COMPLETE_REPO / TARGET_BLOCKED | Login/session/logout BFF present | Repository/deployment login path and owner interactive login are accepted; recovery and restore remain external. |
| `intelligence` | COMPLETE_REPO | Trade analysis/insights integrated | Complete for persisted read-model scope. |
| `learning` | COMPLETE_REPO | Experiments/learning history integrated | Complete for aggregate history; no autonomous promotion authority. |
| `model_control` | COMPLETE_REPO | AI overview/model reads integrated | Complete for immutable registry/control scope; model promotion boundaries remain unchanged. |
| `observability` | COMPLETE_REPO / TARGET_BLOCKED | Execution logs/runtime health consume it | Contracts/redaction/runtime service exist; real Loki/Tempo/Prometheus connectivity remains deployment-owned. |
| `operations` | COMPLETE_REPO / TARGET_BLOCKED | Positions/orders/trades/logs/risk/audit integrated | Repository mirrors and states exist; currentness depends on trusted runtime/telemetry sources. |
| `product` | PARTIAL_REPO | Notifications/profile/admin partly integrated | In-app and overview capabilities exist; external channels and broader recovery administration remain open. |
| `quality_agent` | INTERNAL_ONLY | CI/audit consumer | Supporting validation module; no product page required. |
| `risk` | NEEDS_REMEDIATION | `/terminal` risk-intent UI exists | Deterministic evaluation is complete; approved submission remains blocked in canonical composition until F-02 is fixed. |
| `security` | COMPLETE_REPO | Cross-cutting authorization/session enforcement | Repository policy and negative-path evidence are substantial; remaining recovery/restore acceptance is external. |
| `signal_control` | COMPLETE_REPO | Signal logs/control integrated | Complete for tenant-scoped advisory/operational evidence. |
| `signal_wizard` | COMPLETE_REPO | `/bots/signals` integrated | Complete for advisory control; intentionally no independent execution authority. |
| `simulator` | INTERNAL_ONLY | E2E/quality consumer | Deterministic simulation evidence exists; not a standalone user page. |
| `strategy_lab` | COMPLETE_REPO | AI experiments/research routes | Complete for research experiments; not a substitute for F-01 Strategy Catalog lifecycle API. |
| `telemetry` | COMPLETE_REPO / TARGET_BLOCKED | Model health/runtime views integrated | Repository ingestion/read models complete; real source availability remains target-owned. |
| `valuation` | COMPLETE_REPO / TARGET_BLOCKED | Dashboard/performance consume it | Correct stale/unavailable semantics exist; real attributable currentness depends on private runtime evidence. |

## Frontend product-surface matrix

| Product route | Frontend | Backend/BFF | Status | Required action |
|---|---|---|---|---|
| `/` | Present | Dashboard read API present | COMPLETE_REPO | None beyond real source acceptance. |
| `/performance` | Present | Performance/valuation APIs present | COMPLETE_REPO / TARGET_BLOCKED | Validate real valuation source. |
| `/positions` | Present | Operational API present | COMPLETE_REPO / TARGET_BLOCKED | Validate real private runtime mirror. |
| `/orders` | Present | Operational API present | COMPLETE_REPO / TARGET_BLOCKED | Validate reconciliation against real target. |
| `/trades` | Present | Operational API present | COMPLETE_REPO / TARGET_BLOCKED | Validate real target evidence. |
| `/market/liquidations` | Present | Bounded read-only evidence | COMPLETE_REPO | Preserve `trading_authorized=false`. |
| `/terminal` | Present | Risk endpoint present; real submitter not composed | NEEDS_REMEDIATION | Complete F-02. |
| `/bots` | Present | Fleet/read composition present | COMPLETE_REPO | None beyond source acceptance. |
| `/bots/detail/[botId]` | Present | Lifecycle/commands present | COMPLETE_REPO / TARGET_BLOCKED | Real command target acceptance remains external. |
| `/bots/new` | Present | Protected dry-run creation present | COMPLETE_REPO | None. |
| `/bots/signals` | Present | Advisory backend present | COMPLETE_REPO | None. |
| `/bots/strategies` | Present | BFF present; backend producer absent | NEEDS_REMEDIATION | Complete F-01. |
| `/bots/grid` | Present | Persisted bounded backend present | PARTIAL_REPO | Finish exposure-increasing activation after F-02. |
| `/platform/exchanges` | Present | Metadata/lifecycle API present | COMPLETE_REPO / TARGET_BLOCKED | Real Vault/exchange enrollment acceptance. |
| `/ai` | Present | Model/intelligence/learning reads present | COMPLETE_REPO | None. |
| `/ai/trade-analysis` | Present | TradeAnalysis API present | COMPLETE_REPO | None. |
| `/ai/insights` | Present | TradeInsight API present | COMPLETE_REPO | None. |
| `/ai/model-health` | Present | Telemetry/model-health API present | COMPLETE_REPO / TARGET_BLOCKED | Validate real telemetry source. |
| `/ai/experiments` | Present | Learning/strategy-lab evidence present | COMPLETE_REPO | None for bounded scope. |
| `/ai/learning` | Present | Learning history API present | COMPLETE_REPO | None. |
| `/operations/execution-logs` | Present | Repository observability present | PARTIAL_REPO / TARGET_BLOCKED | Connect and accept real observability target. |
| `/operations/signal-logs` | Present | Signal evidence API present | COMPLETE_REPO | None. |
| `/operations/risk-events` | Present | Risk evidence API present | COMPLETE_REPO | None. |
| `/operations/runtime-health` | Present | Runtime state/evidence APIs present | COMPLETE_REPO / TARGET_BLOCKED | Validate real target freshness. |
| `/operations/audit` | Present | Permission-gated audit API present | COMPLETE_REPO | None. |
| `/platform/notifications` | Present | In-app preferences/entries present | PARTIAL_REPO | External email/webhook/push remains PI-05. |
| `/login` and `/api/identity/*` | Present | Repository/BFF identity and owner login accepted | COMPLETE_REPO / PARTIAL_TARGET | Recovery/restore and protected-ingress closure remain. |
| `/platform/profile` | Present | Session/security read and logout controls present | PARTIAL_REPO / TARGET_BLOCKED | Real enrollment/recovery acceptance. |
| `/platform/admin` | Present | RBAC overview present | PARTIAL_REPO / TARGET_BLOCKED | Broader membership/recovery administration. |

## Existing hard boundaries, not newly discovered code defects

| Boundary | Current classification |
|---|---|
| Authentik/Synology login and owner TOTP/logout | ACCEPTED; recorded by the merged incident closeout |
| Identity recovery and backup/restore | TARGET_BLOCKED / owner-operated |
| Real Loki/Tempo/Prometheus connectivity and dashboards | TARGET_BLOCKED |
| External email/webhook/push delivery | DEFERRED PI-05 provider/privacy decision |
| Real Vault initialization, credential enrollment and restore | TARGET_BLOCKED |
| Real private Freqtrade target, TLS and reconciliation acceptance | TARGET_BLOCKED after F-02 repository repair |
| Protected Cloudflare staging acceptance | P11 TARGET_BLOCKED |
| Live-small readiness | P14 BLOCKED and separately owner-approved |

## Remediation order

1. **F-02 PI-08 runtime composition** — prerequisite for truthful terminal/private submission and grid activation claims.
2. **F-01 Strategy Catalog backend closure** — required because the current integrated UI is fixture-capable but API-incomplete.
3. **F-03 localization decision/implementation** — required by the current completion standard unless formally declared not applicable.
4. Execute real target acceptance packages separately; do not mix them with repository fixes or claim completion from fixture evidence.

## Final audit workflow evidence

```yaml
run_id: 30766675903
job_id: 91546521839
result: success
audited_pr_head: 09a6be82fc702c75d3bb9c808e26c931a9ed6c8b
merge_base_develop_head: 79065e29de8d949701e1465fc99cb6b6e8c4857e
artifact_id: 8839161469
artifact_digest: sha256:8b84593589b7f345952c8e885bc765ffdebfe0eb82c8ddb05c8140eb41b90398
finding_summary:
  critical: 0
  high: 2
  medium: 1
```

A subsequent documentation-only closeout commit may change the audit PR head. The dedicated audit workflow and normal repository/security CI must remain green on that final head before merge or handover.

```text
secret_values_recorded=false
live_capital_authorized=false
product_code_changed=false
```
