# AI Trading Portal — Post-P12 Integration Backlog

## 1. Purpose

This document is the canonical dependency-ordered backlog for hard external and private integration work that remains after the bounded P0-P12 software platform and the software-addressable portal surfaces have been completed.

It does not renumber or replace P0-P14 in `DELIVERY_ROADMAP.md`. It introduces `PI-*` integration package identifiers so future implementation can be declared, owned, validated and reviewed without changing the established stage semantics.

This backlog is planning and routing evidence. A package listed as `planned` is not active until a separate dated task record, branch, owned paths and acceptance evidence are declared. A package listed as `active` may contain completed bounded subpackages while still requiring additional integration or target-environment evidence.

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
- P13 remains measured-need-only and P14 remains owner-gated and blocked;
- Cloudflare Access may supplement privileged ingress but cannot replace product sessions, portal-owned membership, server-side capabilities or tenant isolation;
- browser-readable storage receives no IdP access, ID or refresh token.

## 3. Status model

| Status | Meaning |
|---|---|
| `planned` | Architecture and acceptance are defined, but no implementation task is active. |
| `active` | At least one separate dated implementation task exists, but full package acceptance is incomplete. |
| `blocked` | Work cannot proceed without an explicit external, security, evidence or owner gate. |
| `done` | The package's declared acceptance criteria passed and durable evidence was merged. |
| `deferred` | Work is intentionally postponed until a measurable trigger exists. |

No status in this document authorizes production deployment, real exchange credentials or live capital.

## 4. Canonical package sequence

| Order | Package | Status | Primary outcome | Depends on |
|---:|---|---|---|---|
| 1 | `PI-01` Private Runtime Read and Reconciliation | `done` | authoritative private positions/orders/trades ingestion with source identity and freshness | P3, P4, existing operational mirror |
| 2 | `PI-03` Canonical Inference and Drift Telemetry | `done` | authoritative inference, feature and prediction-distribution telemetry | P4, P5, model/runtime attribution |
| 3 | `PI-04` Centralized Runtime Observability | `done` | searchable logs/traces/metrics with redaction and correlation | P3, P4, deployment logging source |
| 4 | `PI-06` Product Identity and Session Lifecycle | `active` | real product authentication, MFA, revocation and tenant membership lifecycle | P1 security contracts and accepted PI-06 identity decision |
| 5 | `PI-02` Authoritative Valuation and Unrealized PNL | `done` | attributable current valuation with freshness and reconciliation | PI-01 plus authoritative price source |
| 6 | `PI-05` External Notification Delivery | `planned` | auditable email/webhook/push delivery without secret leakage | current in-app notification model; PI-06 where user identity/contact data is required |
| 7 | `PI-07` Runtime Credential Broker and Rotation | `planned` | secret-store/KMS-backed runtime credential injection and revocation | P1 secret references, P3 isolation, security review |
| 8 | `PI-08` Private Dry-Run Approved Execution Submission | `planned` | risk-approved intents submitted privately to isolated Freqtrade dry-run runtimes | PI-01, PI-07, P7 risk, audit and kill switches |
| External gate | P11 Real Cloudflare Production-Like Staging | `blocked` | real protected ingress and five-probe External E2E acceptance | owner-approved Cloudflare and protected GitHub environment |
| Conditional | P13 Scale and Service Extraction | `deferred` | smallest measured response to a proven bottleneck/SLO failure | durable measurement bundle |
| Capital gate | P14 Live-Small Readiness | `blocked` | separately approved minimal-capital readiness | P11, lifecycle evidence, security/operations evidence and explicit owner approval |

PI-01 through PI-04 are complete. PI-02 completed in PR #267, squash merge `0c8fdfe6fb50ff635403ae963484bf4e6883e1e1`. PI-06 is active: the identity architecture decision and repository backend are complete, while Next.js BFF/browser integration, browser security E2E, recovery verification and real authentik target provisioning remain.

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

Completion evidence: task `FTAI-20260724-portal-pi01-runtime-read-reconciliation`, PR #234, squash merge `00c50b4340945cb71e149f269de33f75f9d84a3c`.

Goal: replace portal-only operational evidence gaps with authenticated private reads from the runtime boundary while preserving source-runtime identity, tenant scope, staleness and reconciliation state.

Delivered acceptance:

1. The portal distinguishes current, stale, unavailable and mismatched runtime evidence.
2. Cross-tenant and cross-runtime reads fail closed.
3. Repeated ingestion is idempotent and does not duplicate orders/trades.
4. A runtime outage does not silently present old data as current.
5. Browser clients receive no direct runtime address or credential.

Non-goals:

- order submission;
- exchange credential creation;
- live capital;
- unrealized valuation without PI-02.

Completed task ID:

`FTAI-20260724-portal-pi01-runtime-read-reconciliation`

### PI-02 — Authoritative Valuation and Unrealized PNL

Status: `done`

Completion evidence: task `FTAI-20260724-portal-pi02-authoritative-valuation`, PR #267, squash merge `0c8fdfe6fb50ff635403ae963484bf4e6883e1e1`.

Goal: calculate current position valuation and unrealized PNL only from attributable position evidence and an authoritative, timestamped price source.

Delivered acceptance:

1. Every unrealized value links to a position snapshot and price evidence.
2. Stale or missing prices produce unavailable or unpriced state, not a numeric guess.
3. Aggregates do not mix incompatible currencies without recorded conversion evidence.
4. Reconciliation changes invalidate or supersede affected valuations deterministically.
5. Realized PNL remains sourced from closed-trade evidence.

Non-goals:

- forecasting future PNL;
- treating fixture prices as production evidence;
- live execution.

Completed task ID:

`FTAI-20260724-portal-pi02-authoritative-valuation`

### PI-03 — Canonical Inference and Drift Telemetry

Status: `done`

Completion evidence: task `FTAI-20260724-portal-pi03-inference-drift-telemetry`, PR #239, squash merge `d85ed2c7700a10833aa32d84e7d10cc0a623179c`; closure PR #260 merged as `ee6c8c36272e5b565515692ddb1c834c4ff6a88c`.

Goal: provide canonical inference, feature and prediction-distribution evidence so Model Health can report measured drift rather than only metadata age or `UNAVAILABLE`.

Delivered acceptance:

1. Drift status is reproducible from versioned windows and method parameters.
2. Missing or insufficient samples never produce a healthy claim.
3. Telemetry cannot mutate model lifecycle state or promote a model automatically.
4. Protected final-holdout data is not used as iterative drift-training evidence.
5. Cross-tenant telemetry is isolated.

Non-goals:

- automatic retraining or promotion;
- changing frozen thresholds;
- claiming causality from drift alone.

Completed task ID:

`FTAI-20260724-portal-pi03-inference-drift-telemetry`

### PI-04 — Centralized Runtime Observability

Status: `done`

Completion evidence: task `FTAI-20260724-portal-pi04-central-runtime-observability`, PR #261, squash merge `57a48de41daf98fd0360eaecd841b257947e2559`.

Selected repository target: private OpenTelemetry Collector fan-out to Loki-compatible logs, Tempo-compatible traces and Prometheus-compatible metrics. Repository and CI use injected deterministic sources; target-environment endpoints and credentials remain server-side and unavailable by default until configured.

Delivered acceptance:

1. A portal-to-runtime incident can be traced by correlation ID.
2. Secret-like fields are redacted before storage and covered by tests.
3. A user cannot query another tenant's telemetry.
4. Backend unavailability is visible and does not erase audit evidence.
5. Raw log access is permission-gated and retention-aware.

Non-goals:

- using debug logs as sole business/security proof;
- committing private endpoints or credentials;
- premature service extraction.

Completed task ID:

`FTAI-20260724-portal-pi04-central-runtime-observability`

### PI-05 — External Notification Delivery

Status: `planned`

Goal: deliver selected canonical portal notifications through external channels with idempotency, user preferences, delivery evidence and secret-safe provider integration.

Entry gates:

- canonical in-app notification categories and actor preferences are stable;
- at least one provider/channel is selected;
- destination ownership/verification and privacy rules are declared;
- provider credentials use opaque secret references.

Deliverables:

- one email, signed-webhook or push adapter at a time;
- idempotency key and delivery-attempt model;
- retry, backoff and dead-letter behavior;
- opt-in/out and severity/category routing;
- delivery status without provider secrets or unrestricted payloads;
- abuse and rate-limit controls.

Acceptance:

1. Duplicate event delivery does not create duplicate notifications beyond declared retry semantics.
2. Disabled channels/categories are not delivered.
3. Provider outage is retryable and observable.
4. Destinations and provider secrets are tenant/actor scoped and not exposed to browser or logs.
5. External delivery failure cannot affect trading execution.

Non-goals:

- notification as execution approval;
- sending secrets, raw feature data or unrestricted logs;
- claiming external delivery before provider evidence exists.

Recommended task ID:

`FTAI-YYYYMMDD-portal-pi05-external-notification-delivery`

### PI-06 — Product Identity, MFA, Session and Membership Lifecycle

Status: `active`

Goal: replace the trusted development/application identity boundary with a real product identity integration supporting secure sessions, MFA, revocation, recovery and tenant membership lifecycle.

#### Accepted decision

Decision task `FTAI-20260726-portal-pi06-identity-decision`, PR #331, selected:

- authentik as the product IdP;
- Authorization Code Flow with PKCE;
- portal-owned principals, tenants, memberships, roles, capabilities and local revocation;
- immutable external identity mapping by OIDC `iss` plus `sub`;
- opaque local sessions and no browser-readable IdP token material;
- MFA for mutation-capable roles and five-minute step-up for declared high-impact administration;
- synchronous membership/session invalidation;
- Cloudflare Access as supplemental privileged ingress only.

#### Completed repository backend

Task `FTAI-20260726-portal-pi06-product-identity-lifecycle`, PR #341, squash merge `41834d18f3a05b0dfa44dc5af9b97942e685d2a1` delivered:

- OIDC discovery, PKCE, JWKS signature, issuer, audience, expiry and nonce validation;
- one-time expiring login state and encrypted PKCE verifier material;
- portal identity, membership, session, revocation and audit persistence;
- opaque 256-bit browser session and CSRF tokens with keyed hashes in storage;
- secure host-only session cookie and server-verified CSRF;
- membership-derived tenant and capability context;
- MFA and five-minute step-up enforcement;
- logout, logout-all, role/membership-change revocation and OIDC back-channel logout;
- deterministic runtime configuration, migrations and security tests.

Exact final backend head `c258567cabd1c9ddf3d90c63f36319be99463978` passed AI Platform CI #1415, Freqtrade CI #1713 and GitHub Actions Security Analysis #1580.

#### Remaining work

1. Connect same-origin Next.js login, callback, session and logout routes to the merged backend.
2. Replace fixture/trusted browser identity on protected product paths without exposing private backend or IdP credentials.
3. Add deterministic Playwright coverage for anonymous denial, successful session, CSRF failure, MFA/step-up denial, idle and absolute expiry, membership revocation, logout-all and cross-tenant denial.
4. Verify recovery states do not reveal account existence or bypass MFA policy.
5. In a later deployment package, add pinned Authentik/Synology Compose configuration, runtime-injected secret placeholders, restricted bootstrap and recovery/restore runbooks.
6. Provision and validate real owner-managed authentik and Cloudflare resources before target-environment acceptance.

Full-package acceptance:

1. Revoked or expired sessions fail closed on every protected API and browser path.
2. MFA is enforced for declared privileged roles without relying solely on page visibility.
3. Tenant context is derived from authenticated portal membership, not browser-supplied tenant IDs.
4. Role/membership changes are audited and take effect according to the versioned revocation policy.
5. Recovery flows do not expose account existence or bypass MFA/security policy.
6. Real target deployment proves login, logout, revocation and recovery against owner-managed authentik without committing credentials.

Non-goals:

- storing primary passwords in the portal;
- using Cloudflare Access as the only product identity layer;
- treating repository tests as real IdP or P11 acceptance;
- live-capital authorization.

Completed backend task ID:

`FTAI-20260726-portal-pi06-product-identity-lifecycle`

Recommended next task ID:

`FTAI-YYYYMMDD-portal-pi06-bff-browser-session-integration`

### PI-07 — Runtime Credential Broker and Rotation

Status: `planned`

Goal: implement the secret-store/KMS-backed path that resolves an opaque exchange connection reference and injects minimum-scope credentials only into the intended isolated runtime.

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
- rotation, versioning and revocation workflow;
- least-privilege and withdrawal-disabled validation where provider capability allows;
- audit references/hashes only, never secret values;
- compromise kill-switch linkage.

Acceptance:

1. Plaintext credentials never appear in Git, public APIs, logs, events or audit payloads.
2. One runtime cannot resolve another tenant/runtime's credential reference.
3. Revocation prevents future use and produces attributable evidence.
4. Research/training workloads cannot access runtime exchange credentials.
5. Rotation does not silently change unrelated bot/config identity.

Non-goals:

- live-capital enablement;
- withdrawal permission;
- exposing secret-management APIs directly to the browser beyond one-time submission.

Recommended task ID:

`FTAI-YYYYMMDD-portal-pi07-runtime-credential-broker`

### PI-08 — Private Dry-Run Approved Execution Submission

Status: `planned`

Goal: implement the concrete private `FreqtradeExecutionAdapter.submit_approved_intent` path for isolated `dry_run` runtimes after deterministic risk approval, without creating live-capital authority.

Entry gates:

- PI-01 private runtime identity and reconciliation are complete;
- PI-07 credential/runtime-secret boundary is complete where required;
- P7 risk and hierarchical kill switches remain authoritative;
- command authentication, rate limiting and idempotency semantics are approved;
- dry-run environment is enforced independently of browser input.

Deliverables:

- private authenticated submission of `ApprovedExecutionIntent` to the exact pinned runtime;
- deterministic idempotency and duplicate-command handling;
- bounded timeout/retry with no ambiguous silent success;
- order acknowledgement and later reconciliation through PI-01;
- explicit rejected, blocked, unavailable and unknown-result states;
- kill-switch and runtime-health recheck immediately before submission;
- full audit/correlation evidence;
- security and dry-run E2E proving browser/runtime separation.

Acceptance:

1. Only a valid, unexpired risk-approved intent for the exact tenant/bot/config/runtime can be submitted.
2. Duplicate delivery cannot create duplicate exposure beyond proven adapter semantics.
3. Kill switch, degraded health or mismatched runtime identity blocks submission.
4. Ambiguous runtime responses remain unresolved until reconciliation and are not reported as fills.
5. The implementation cannot select live capital or production credentials.
6. Browser clients cannot address or authenticate to Freqtrade directly.

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

### Wave PI-A — Truthful operational evidence and identity

PI-01, PI-02, PI-03 and PI-04 are complete. PI-06 decision and repository backend are complete subpackages.

Next action:

- complete PI-06 same-origin BFF/browser-session integration and deterministic browser security E2E;
- then complete separately controlled Authentik/Synology deployment and real identity acceptance.

Exit condition:

- runtime, valuation, model and operational evidence are attributable and truthfully expose freshness/unavailability;
- protected browser paths derive identity, tenant and capabilities from the real product session;
- no execution submission is added.

### Wave PI-B — Product completeness from authoritative sources

PI-02 is complete. Declare PI-05 only after channel/provider and identity/destination ownership are clear.

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

Before implementing any PI package or remaining subpackage, the agent must:

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

The next dependency-ordered core software action is **PI-06 same-origin BFF and browser-session integration** using the merged repository backend.

Real Authentik/Synology and Cloudflare provisioning follows only in a separately controlled deployment package. PI-05 requires a channel/provider decision, and PI-07 requires a secret-store/KMS decision before PI-08 can be considered.

The recommended external action remains P11 only when the owner intentionally starts the Cloudflare/protected GitHub infrastructure phase.

## 11. Completion definition for this backlog

The post-P12 integration backlog is complete only when:

- PI-01 through PI-08 are either `done` or explicitly retired by an architecture decision;
- P11 real external acceptance is `done`;
- every portal surface reports authoritative current/stale/unavailable state without fabrication;
- product identity, membership, session, MFA, recovery and revocation are proven through the real protected browser path;
- private dry-run execution is risk-gated, secret-safe, attributable and reconciled;
- P13 remains evidence-triggered;
- P14 remains separately owner-approved and is never inferred from software completion.
