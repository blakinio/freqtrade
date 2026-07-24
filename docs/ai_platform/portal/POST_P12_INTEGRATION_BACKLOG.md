# AI Trading Portal — Post-P12 Integration Backlog

## 1. Purpose

This document is the canonical dependency-ordered backlog for hard external and private integration work that remains after the bounded P0-P12 software platform and the software-addressable portal surfaces have been completed.

It does not renumber or replace P0-P14 in `DELIVERY_ROADMAP.md`. It introduces `PI-*` integration package identifiers so future implementation can be declared, owned, validated and reviewed without changing the established stage semantics.

This backlog is planning and routing evidence only. A package listed as `planned` is not active until a separate dated task record, branch, owned paths and acceptance evidence are declared.

## 2. Governing boundaries

Every package inherits these invariants:

- browser traffic communicates only with the portal/BFF and never directly with Freqtrade, an exchange, a secret store or the data plane;
- Freqtrade remains private behind the versioned execution-adapter boundary;
- deterministic risk approval is necessary but is not by itself execution authority;
- signal, analysis, experiment and model evidence cannot bypass risk or promotion gates;
- exchange credentials are opaque, tenant-scoped, withdrawal-disabled and never returned to the browser after storage;
- unavailable source data is represented as unavailable, stale or unreconciled rather than fabricated;
- new trading configurations remain `dry_run` unless a separately reviewed live-capital package is explicitly approved;
- frozen thresholds `0.006/-0.009`, protected final holdout `20260801-20260930`, completed Phase 6 policy/evidence and authoritative `selected_model = null` remain unchanged;
- P11 simulated/repository evidence cannot be represented as real Cloudflare production-like staging acceptance;
- P13 remains measured-need-only and P14 remains owner-gated and blocked.

## 3. Status model

| Status | Meaning |
|---|---|
| `planned` | Architecture and acceptance are defined, but no implementation task is active. |
| `active` | A separate dated task, branch and owned paths exist. |
| `blocked` | Work cannot proceed without an explicit external, security, evidence or owner gate. |
| `done` | The package's declared acceptance criteria passed and durable evidence was merged. |
| `deferred` | Work is intentionally postponed until a measurable trigger exists. |

No status in this document authorizes production deployment, real exchange credentials or live capital.

## 4. Canonical package sequence

| Order | Package | Status | Primary outcome | Depends on |
|---:|---|---|---|---|
| 1 | `PI-01` Private Runtime Read and Reconciliation | `done` | authoritative private positions/orders/trades ingestion with source identity and freshness | P3, P4, existing operational mirror |
| 2 | `PI-03` Canonical Inference and Drift Telemetry | `active` | authoritative inference, feature and prediction-distribution telemetry | P4, P5, model/runtime attribution |
| 3 | `PI-04` Centralized Runtime Observability | `planned` | searchable logs/traces/metrics with redaction and correlation | P3, P4, deployment logging source |
| 4 | `PI-06` Product Identity and Session Lifecycle | `planned` | real product authentication, MFA, revocation and tenant membership lifecycle | P1 security contracts, external IdP decision |
| 5 | `PI-02` Authoritative Valuation and Unrealized PNL | `planned` | attributable current valuation with freshness and reconciliation | PI-01 plus authoritative price source |
| 6 | `PI-05` External Notification Delivery | `planned` | auditable email/webhook/push delivery without secret leakage | current in-app notification model; PI-06 where user identity/contact data is required |
| 7 | `PI-07` Runtime Credential Broker and Rotation | `planned` | secret-store/KMS-backed runtime credential injection and revocation | P1 secret references, P3 isolation, security review |
| 8 | `PI-08` Private Dry-Run Approved Execution Submission | `planned` | risk-approved intents submitted privately to isolated Freqtrade dry-run runtimes | PI-01, PI-07, P7 risk, audit and kill switches |
| External gate | P11 Real Cloudflare Production-Like Staging | `blocked` | real protected ingress and five-probe External E2E acceptance | owner-approved Cloudflare and protected GitHub environment |
| Conditional | P13 Scale and Service Extraction | `deferred` | smallest measured response to a proven bottleneck/SLO failure | durable measurement bundle |
| Capital gate | P14 Live-Small Readiness | `blocked` | separately approved minimal-capital readiness | P11, lifecycle evidence, security/operations evidence and explicit owner approval |

The numeric order is the recommended software sequencing. PI-03, PI-04 and PI-06 may run in parallel when ownership is disjoint and shared contract changes are serialized. PI-02 may now begin once its authoritative price-source, currency-conversion and staleness entry gates are satisfied.

## 5. Dependency graph

```text
P3 private runtime lifecycle ----+----------------------+
                                 |                      |
P4 events/observability ---------+--> PI-01 reads ------+--> PI-02 valuation
                                 |                      |
P5 model identity ---------------+--> PI-03 drift       |
                                 |                      |
Deployment telemetry source -----+--> PI-04 logs        |
                                                        |
P1 identity/security contracts ------> PI-06 identity --+--> PI-05 delivery
                                                        |
P1 secret references + P3 isolation --> PI-07 secrets --+--> PI-08 dry-run submission
PI-01 reads + P7 risk + audit --------------------------+

PI-03/PI-04/PI-06/PI-08 software intended for staging
                                 |
                                 v
                         P11 real external staging
                                 |
              +------------------+------------------+
              |                                     |
        measured SLO trigger                    explicit owner gate
              |                                     |
              v                                     v
         P13 if justified                    P14 live-small readiness
```

P11 may be resumed earlier when the owner intentionally starts the external infrastructure phase. It remains mandatory before production-like staging is accepted and before P14 can be considered.

## 6. Package specifications

### PI-01 — Private Runtime Read and Reconciliation

Status: `done`

Completion evidence: task `FTAI-20260724-portal-pi01-runtime-read-reconciliation`, PR #234, squash merge `00c50b4340945cb71e149f269de33f75f9d84a3c` after all required CI passed.

Goal: replace portal-only operational evidence gaps with authenticated private reads from the runtime boundary while preserving source-runtime identity, tenant scope, staleness and reconciliation state.

Recommended ownership:

- `ai_platform/portal/execution/` adapter read methods;
- `ai_platform/portal/operations/` ingestion and reconciliation;
- targeted execution/operations tests and documentation.

Entry gates:

- current `ExecutionAdapter` read contracts are reviewed and versioned;
- runtime identity maps deterministically to one tenant and BotInstance;
- private authentication and network route are defined without browser exposure;
- source timestamps and pagination semantics are understood.

Deliverables:

- working private implementations for `get_open_positions`, `get_orders` and `get_trades`, or a versioned collector interface with equivalent authoritative evidence;
- normalized ingestion preserving `source_runtime_id`, source record identity and observed timestamp;
- idempotent reconciliation with `SYNCED`, `PENDING`, `SOURCE_UNAVAILABLE` and `MISMATCH` states;
- bounded retry, timeout, pagination and partial-source behavior;
- tenant-isolation, stale-source, duplicate and mismatch tests;
- no execution command path.

Acceptance:

1. The portal can distinguish current, stale, unavailable and mismatched runtime evidence.
2. Cross-tenant and cross-runtime reads fail closed.
3. Repeated ingestion is idempotent and does not duplicate orders/trades.
4. A runtime outage does not silently present old data as current.
5. Browser clients still have no direct runtime address or credential.

Non-goals:

- order submission;
- exchange credential creation;
- live capital;
- unrealized valuation without PI-02.

Completed task ID:

`FTAI-20260724-portal-pi01-runtime-read-reconciliation`

### PI-02 — Authoritative Valuation and Unrealized PNL

Status: `planned`

Goal: calculate current position valuation and unrealized PNL only from attributable position evidence and an authoritative, timestamped price source.

Recommended ownership:

- a bounded portal valuation/read-model module;
- operations/performance API and UI integration;
- valuation freshness and reconciliation tests.

Entry gates:

- PI-01 provides attributable open-position evidence;
- one authoritative price/mark source is selected per supported execution mode;
- currency conversion and fee treatment are explicitly defined;
- timestamp, timezone and market-staleness policy are versioned.

Deliverables:

- `ValuationSnapshot` or equivalent immutable evidence contract;
- source price ID, source timestamp, quote currency and conversion provenance;
- per-position and aggregate unrealized PNL;
- explicit `CURRENT`, `STALE`, `SOURCE_UNAVAILABLE` and `UNPRICED` states;
- deterministic handling of partial fills, fees and unsupported pairs;
- no fabricated price fallback in API mode.

Acceptance:

1. Every unrealized value links to a position snapshot and price evidence.
2. Stale or missing prices produce an unavailable/unpriced state, not a numeric guess.
3. Aggregates cannot mix incompatible currencies without recorded conversion evidence.
4. Reconciliation changes invalidate or supersede affected valuations deterministically.
5. Realized PNL remains sourced from closed trade evidence and is not recomputed inconsistently.

Non-goals:

- forecasting future PNL;
- treating fixture prices as production evidence;
- live execution.

Recommended task ID:

`FTAI-YYYYMMDD-portal-pi02-authoritative-valuation`

### PI-03 — Canonical Inference and Drift Telemetry

Status: `active`

Implementation evidence: task `FTAI-20260724-portal-pi03-inference-drift-telemetry`, draft PR #239. Merge evidence remains pending until required CI is green.

Goal: provide canonical inference, feature and prediction-distribution evidence so Model Health can report measured drift rather than only metadata age or `UNAVAILABLE`.

Recommended ownership:

- inference telemetry contracts and ingestion;
- model-control health aggregation;
- observability storage/query boundary;
- drift tests and UI read-model integration.

Entry gates:

- exact ModelVersion, feature-schema, bot-config and runtime attribution exists for each inference sample or aggregate;
- privacy, retention and sampling policy is declared;
- baseline/reference distribution ownership is defined;
- drift method and alert thresholds are versioned and are not promotion rules by themselves.

Deliverables:

- versioned inference telemetry envelope;
- accepted/rejected prediction counts and reason attribution;
- feature availability/quality and prediction-distribution aggregates;
- reference-window and observation-window identities;
- deterministic drift calculation with minimum-sample and missing-data states;
- `HEALTHY`, `ATTENTION`, `DEGRADED`, `INSUFFICIENT_EVIDENCE` and `UNAVAILABLE` semantics;
- alert evidence linked to model/runtime/config identity.

Acceptance:

1. Drift status can be reproduced from versioned windows and method parameters.
2. Missing or insufficient samples never produce a healthy claim.
3. Telemetry cannot mutate model lifecycle state or promote a model automatically.
4. Protected final-holdout data is not used as iterative drift-training evidence.
5. Cross-tenant telemetry is isolated.

Non-goals:

- automatic retraining or promotion;
- changing frozen thresholds;
- claiming causality from drift alone.

Recommended task ID:

`FTAI-YYYYMMDD-portal-pi03-inference-drift-telemetry`

### PI-04 — Centralized Runtime Observability

Status: `planned`

Goal: make runtime logs, traces and metrics searchable and attributable without confusing operational telemetry with immutable audit evidence.

Recommended ownership:

- deployment log/trace/metric collector configuration;
- `ai_platform/portal/observability/` source adapters and query contracts;
- operations UI read model and runbooks.

Entry gates:

- a centralized log/trace backend is selected for the target environment;
- retention, tenant visibility and access-control policies are declared;
- redaction rules are tested before ingestion;
- runtime correlation fields are emitted consistently.

Deliverables:

- structured runtime log ingestion with service/component/environment/runtime/bot/correlation identity;
- distributed traces across portal, orchestrator and runtime boundaries where supported;
- Prometheus-compatible runtime/exchange/error metrics;
- bounded search API with tenant and permission enforcement;
- source freshness/availability status;
- dashboards and alert/runbook links for agreed critical signals;
- explicit separation from append-only audit records.

Acceptance:

1. A portal-to-runtime incident can be traced by correlation ID.
2. Secret-like fields are redacted before storage and covered by tests.
3. A user cannot query another tenant's telemetry.
4. Backend unavailability is visible and does not erase audit evidence.
5. Raw log access is permission-gated and retention-aware.

Non-goals:

- using debug logs as sole business/security proof;
- committing private endpoints or credentials;
- premature service extraction.

Recommended task ID:

`FTAI-YYYYMMDD-portal-pi04-central-runtime-observability`

### PI-05 — External Notification Delivery

Status: `planned`

Goal: deliver selected canonical portal notifications through external channels with idempotency, user preferences, delivery evidence and secret-safe provider integration.

Recommended ownership:

- notification delivery provider abstraction and worker/outbox consumer;
- provider secret references;
- preference/channel UI and delivery audit evidence;
- provider failure/retry tests.

Entry gates:

- canonical in-app notification categories and actor preferences are stable;
- at least one provider/channel is selected;
- destination ownership/verification and privacy rules are declared;
- provider credentials use opaque secret references.

Deliverables:

- email, signed webhook or push provider adapter, introduced one channel at a time;
- idempotency key and delivery-attempt model;
- retry/backoff/dead-letter behavior;
- opt-in/opt-out and severity/category routing;
- delivery status without exposing provider secrets or full private payloads;
- abuse/rate-limit controls.

Acceptance:

1. Duplicate event delivery does not send duplicate notifications beyond the declared retry semantics.
2. Disabled channels/categories are not delivered.
3. Provider outage is retryable and observable.
4. Destinations and provider secrets are tenant/actor scoped and not exposed to the browser or logs.
5. External delivery failure cannot affect trading execution.

Non-goals:

- using notifications as an execution approval channel;
- sending secrets, raw feature data or unrestricted logs;
- claiming external delivery before provider evidence exists.

Recommended task ID:

`FTAI-YYYYMMDD-portal-pi05-external-notification-delivery`

### PI-06 — Product Identity, MFA, Session and Membership Lifecycle

Status: `planned`

Goal: replace the trusted development/application identity boundary with a real product identity integration supporting secure sessions, MFA, revocation, recovery and tenant membership lifecycle.

Recommended ownership:

- portal identity/session module and BFF middleware;
- external IdP adapter/configuration boundary;
- membership/role administration integration;
- security E2E and recovery/session runbooks.

Entry gates:

- product IdP and OIDC/OAuth2 flow are selected;
- tenant and membership source-of-truth ownership is decided;
- session duration, refresh, revocation and recovery policies are approved;
- privileged-role MFA and re-authentication policy is defined;
- P11 Cloudflare Access remains supplemental rather than a substitute for application authorization.

Deliverables:

- OIDC/OAuth2-compatible login and callback flow;
- secure HttpOnly/SameSite cookies and CSRF protection;
- session refresh/revocation and logout-all behavior;
- MFA enrollment/challenge for privileged roles through the chosen IdP or compatible product flow;
- tenant membership and role mapping with server-side authorization;
- login/recovery abuse controls and security event emission;
- denied, expired, revoked and recovery E2E states.

Acceptance:

1. Revoked or expired sessions fail closed on every protected API.
2. MFA is enforced for declared privileged roles without relying solely on page visibility.
3. Tenant context is derived from authenticated membership, not browser-supplied tenant IDs.
4. Role/membership changes are audited and take effect according to a documented revocation/cache policy.
5. Recovery flows do not expose account existence or bypass MFA/security policy.

Non-goals:

- storing primary passwords unless the selected architecture explicitly owns them;
- using Cloudflare Access as the only product identity layer;
- live-capital authorization.

Recommended task ID:

`FTAI-YYYYMMDD-portal-pi06-product-identity-lifecycle`

### PI-07 — Runtime Credential Broker and Rotation

Status: `planned`

Goal: implement the secret-store/KMS-backed path that resolves an opaque exchange connection reference and injects minimum-scope credentials only into the intended isolated runtime.

Recommended ownership:

- exchange connection metadata and secret-reference resolver;
- runtime credential broker/injection boundary;
- rotation/revocation audit and incident runbooks;
- security tests.

Entry gates:

- secret store/KMS and deployment environment are selected;
- withdrawal-disabled credential policy is enforceable and reviewed;
- runtime identity and tenant ownership are deterministic;
- secret rotation, revocation and incident procedures are approved;
- research/training network and identity denial is testable.

Deliverables:

- one-time secret submission and opaque reference storage;
- envelope encryption or provider-native secret storage;
- per-runtime credential resolution/injection without returning plaintext to portal consumers;
- rotation/versioning/revocation workflow;
- least-privilege and withdrawal-disabled validation where exchange/provider capability allows;
- audit events containing references/hashes only, never secret values;
- compromise kill-switch linkage.

Acceptance:

1. Plaintext credentials never appear in Git, public API responses, logs, events or audit payloads.
2. One runtime cannot resolve another tenant/runtime's credential reference.
3. Revocation prevents future use and produces attributable evidence.
4. Research/training workloads cannot access runtime exchange credentials.
5. Rotation can complete without silently changing unrelated bot/config identity.

Non-goals:

- live-capital enablement;
- withdrawal permission;
- exposing secret-management APIs directly to the browser beyond one-time submission.

Recommended task ID:

`FTAI-YYYYMMDD-portal-pi07-runtime-credential-broker`

### PI-08 — Private Dry-Run Approved Execution Submission

Status: `planned`

Goal: implement the concrete private `FreqtradeExecutionAdapter.submit_approved_intent` path for isolated `dry_run` runtimes after deterministic risk approval, without creating live-capital authority.

Recommended ownership:

- `ai_platform/portal/execution/` approved-intent submitter;
- Freqtrade private API/command adapter;
- idempotency, reconciliation and failure mapping;
- terminal/execution E2E in dry-run only.

Entry gates:

- PI-01 private runtime identity and reconciliation are complete;
- PI-07 credential/runtime-secret boundary is complete where the runtime requires exchange credentials;
- P7 risk and hierarchical kill switches remain authoritative;
- command authentication, rate limiting and idempotency semantics are approved;
- dry-run environment is enforced independently of browser input.

Deliverables:

- private authenticated submission of `ApprovedExecutionIntent` to the exact pinned runtime;
- deterministic idempotency and duplicate-command handling;
- bounded timeout/retry with no ambiguous silent success;
- order acknowledgement and later reconciliation through PI-01;
- explicit rejected/blocked/unavailable/unknown-result states;
- kill-switch and runtime-health recheck immediately before submission;
- full audit/correlation evidence;
- security and dry-run E2E proving browser/runtime separation.

Acceptance:

1. Only a valid, unexpired risk-approved intent for the exact tenant/bot/config/runtime can be submitted.
2. Duplicate delivery cannot create duplicate exposure beyond proven adapter semantics.
3. Kill switch, degraded health or mismatched runtime identity blocks submission.
4. Ambiguous runtime responses remain unresolved/blocked until reconciliation; they are not reported as fills.
5. The implementation cannot select live capital or production credentials.
6. Browser clients still cannot address or authenticate to Freqtrade directly.

Non-goals:

- P14 live-small;
- bypassing risk because an intent originated from AI or an admin;
- treating order acknowledgement as a trade fill.

Recommended task ID:

`FTAI-YYYYMMDD-portal-pi08-private-dry-run-submission`

## 7. Existing governed stages

### P11 — Real Cloudflare Production-Like Staging

Status: `blocked`

P11 already has a dedicated task, repository-side policy/verifier/workflows and runbooks. It is not duplicated by a PI package.

Resume gate:

- explicit owner start of the external infrastructure phase;
- owner-approved Cloudflare Tunnel, proxied DNS, WAF, rate limiting, Access/Zero Trust and direct-origin denial;
- protected GitHub staging variables/secrets;
- successful real `Portal Staging External E2E` covering public portal reachability, anonymous privileged denial, service-identity access, direct-origin denial and direct-Freqtrade denial.

P11 uses simulated execution by default and does not authorize P14.

Canonical task:

`docs/agents/tasks/FTAI-20260723-portal-p11-cloudflare-staging.md`

### P13 — Scale and Service Extraction

Status: `deferred`

Trigger:

- durable measurements identify a specific bottleneck or unmet SLO;
- quantified user/operational impact exists;
- alternatives and smallest justified change are documented;
- validation and rollback criteria are declared.

No PI package may introduce Kubernetes, a workflow engine, service extraction, partitioned infrastructure or multi-region complexity merely for architectural preference.

### P14 — Live-Small Readiness

Status: `blocked`

P14 remains outside this backlog's implementation authority.

Required before declaration:

- explicit owner approval and a separate reviewed work package;
- successful required AI Platform lifecycle evidence and independently reviewed model/strategy eligibility;
- successful P11 production-like staging acceptance;
- withdrawal-disabled production exchange credentials;
- strict capital/exposure/loss limits;
- security review, monitoring, alerting, emergency procedures and rollback;
- sustained dry-run evidence including the intended private execution path;
- no unresolved severe reconciliation, drift, observability or identity/security gaps.

## 8. Recommended execution waves

### Wave PI-A — Truthful operational evidence

PI-01 is complete.

PI-03 and PI-04 may run in parallel after checking shared event/observability contract ownership. PI-06 may also begin independently when the product IdP decision is available.

Exit condition:

- runtime evidence, model telemetry and operational telemetry are attributable and truthfully expose freshness/unavailability;
- no execution submission is added.

### Wave PI-B — Product completeness from authoritative sources

PI-02 may now be declared once its authoritative price, conversion and staleness policies are selected. Declare PI-05 after channel/provider and identity/destination ownership are clear.

Exit condition:

- unrealized PNL and external notification states are backed by authoritative evidence;
- missing sources remain explicit.

### Wave PI-C — High-risk private execution enablement

Declare PI-07 before PI-08.

Exit condition:

- secrets are brokered safely;
- risk-approved execution can reach only isolated dry-run runtimes;
- reconciliation proves resulting order/trade state;
- no live-capital path exists.

### Wave PI-D — Real external staging

Resume P11 when explicitly authorized and when the intended staging software/infrastructure set is stable.

Exit condition:

- all real external ingress, Access and direct-denial probes pass;
- production-like staging is accepted with simulated execution by default.

### Wave PI-E — Conditional scale or capital work

P13 starts only from measured need. P14 starts only from explicit owner approval and all prerequisite evidence.

## 9. Package declaration rules

Before implementing any PI package, the agent must:

1. inspect current `develop`, open PRs, active task ownership and relevant CI;
2. create one dated task record and dedicated branch;
3. declare exact owned paths and shared-contract coordination;
4. copy package-specific entry gates, deliverables, acceptance criteria and non-goals into the task;
5. identify the authoritative external/data source and how unavailability is represented;
6. add tenant, permission, secret-redaction, idempotency and fail-closed tests as applicable;
7. run narrow validation followed by required repository CI;
8. update this backlog only when package status or dependency evidence materially changes;
9. leave P11/P13/P14 semantics unchanged unless the corresponding governed evidence exists.

A package must not be broadened mid-implementation to include the next package merely because adjacent code is convenient to edit.

## 10. Priority decision

The active software package is **PI-03 Canonical Inference and Drift Telemetry**. Its bounded task and PR implement aggregate-only, attributable inference windows and reproducible PSI-v1 evidence without execution authority, automatic retraining or model promotion. The next package is selected only after PI-03 durable completion evidence is merged.

PI-02 is now dependency-ready from the runtime-position side, but still requires explicit authoritative price, conversion and staleness decisions before declaration.

The recommended next external action remains **P11**, but only when the owner intentionally starts the Cloudflare/protected GitHub infrastructure phase.

## 11. Completion definition for this backlog

The post-P12 integration backlog is complete only when:

- PI-01 through PI-08 are either `done` or explicitly retired by an architecture decision;
- P11 real external acceptance is `done`;
- every portal surface reports authoritative current/stale/unavailable state without fabrication;
- private dry-run execution is risk-gated, secret-safe, attributable and reconciled;
- P13 remains evidence-triggered;
- P14 remains separately owner-approved and is never inferred from software completion.
