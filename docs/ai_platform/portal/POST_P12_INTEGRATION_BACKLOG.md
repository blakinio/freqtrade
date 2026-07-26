# AI Trading Portal — Post-P12 Integration Backlog

## 1. Purpose

This document is the canonical dependency-ordered backlog for hard external and private integration work remaining after the bounded P0-P12 software platform and software-addressable portal surfaces.

It does not renumber or replace P0-P14 in `DELIVERY_ROADMAP.md`. PI identifiers allow future work to be declared, owned, validated and reviewed without changing established stage semantics.

A package listed as `active` may contain completed bounded subpackages while still requiring target-environment or external acceptance. No status here authorizes production deployment, exchange credentials or live capital.

## 2. Governing boundaries

Every package inherits these invariants:

- browser traffic communicates only with the portal/BFF and never directly with Freqtrade, an exchange, a secret store or the data plane;
- Freqtrade remains private behind the versioned execution-adapter boundary;
- deterministic risk approval is necessary but is not execution authority by itself;
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
| `active` | At least one implementation subpackage exists, but full package acceptance is incomplete. |
| `blocked` | Work cannot proceed without an explicit external, security, evidence or owner gate. |
| `done` | Declared package acceptance passed and durable evidence was merged. |
| `deferred` | Work is postponed until a measurable trigger exists. |

## 4. Canonical package sequence

| Order | Package | Status | Primary outcome | Depends on |
|---:|---|---|---|---|
| 1 | `PI-01` Private Runtime Read and Reconciliation | `done` | authoritative private positions/orders/trades with source identity and freshness | P3, P4, runtime mirror |
| 2 | `PI-03` Canonical Inference and Drift Telemetry | `done` | attributable aggregate inference and drift evidence | P4, P5, model/runtime attribution |
| 3 | `PI-04` Centralized Runtime Observability | `done` | searchable redacted logs/traces/metrics | P3, P4, deployment logging source |
| 4 | `PI-06` Product Identity and Session Lifecycle | `active` | real product authentication, MFA, revocation and membership lifecycle | P1 and accepted PI-06 decision |
| 5 | `PI-02` Authoritative Valuation and Unrealized PNL | `done` | attributable valuation with freshness and reconciliation | PI-01 and authoritative mark source |
| 6 | `PI-05` External Notification Delivery | `planned` | auditable external delivery without secret leakage | in-app notifications; PI-06 where identity/contact data is required |
| 7 | `PI-07` Runtime Credential Broker and Rotation | `planned` | secret-store-backed credential injection and revocation | P1 secret references, P3 isolation, security review |
| 8 | `PI-08` Private Dry-Run Approved Execution Submission | `planned` | risk-approved intents submitted privately to dry-run runtimes | PI-01, PI-07, P7 and audit |
| External gate | P11 Real Cloudflare Production-Like Staging | `blocked` | real protected ingress and five-probe acceptance | owner-approved Cloudflare and protected GitHub environment |
| Conditional | P13 Scale and Service Extraction | `deferred` | smallest measured response to a proven bottleneck | durable measurement bundle |
| Capital gate | P14 Live-Small Readiness | `blocked` | separately approved minimal-capital readiness | P11 and explicit owner approval |

PI-01 through PI-04 and PI-02 are complete. PI-06 remains active: the architecture decision, repository backend and same-origin BFF/browser-session integration are complete; real Authentik/Synology deployment, MFA enrollment, recovery, backup/restore and target-environment acceptance remain.

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

P11 may resume earlier only when the owner intentionally starts the external infrastructure phase. It remains mandatory before production-like staging is accepted and before P14 can be considered.

## 6. Package specifications

### PI-01 — Private Runtime Read and Reconciliation

Status: `done`.

Completion: task `FTAI-20260724-portal-pi01-runtime-read-reconciliation`, PR #234, merge `00c50b4340945cb71e149f269de33f75f9d84a3c`.

Acceptance delivered:

1. Current, stale, unavailable and mismatched runtime evidence are distinct.
2. Cross-tenant and cross-runtime reads fail closed.
3. Repeated ingestion is idempotent.
4. Outage does not present old data as current.
5. Browser clients receive no runtime address or credential.

Non-goals: order submission, credential creation, live capital.

### PI-02 — Authoritative Valuation and Unrealized PNL

Status: `done`.

Completion: task `FTAI-20260724-portal-pi02-authoritative-valuation`, PR #267, merge `0c8fdfe6fb50ff635403ae963484bf4e6883e1e1`.

Acceptance delivered:

1. Every unrealized value links to position and price evidence.
2. Stale/missing marks produce unavailable or unpriced state.
3. Aggregates do not silently mix currencies.
4. Reconciliation supersedes affected valuations deterministically.
5. Realized PNL remains sourced from closed trades.

Non-goals: forecasting, fixture prices as production evidence, live execution.

### PI-03 — Canonical Inference and Drift Telemetry

Status: `done`.

Completion: task `FTAI-20260724-portal-pi03-inference-drift-telemetry`, PR #239, merge `d85ed2c7700a10833aa32d84e7d10cc0a623179c`, closure PR #260.

Acceptance delivered:

1. Drift status is reproducible from versioned windows and methods.
2. Missing/insufficient samples never produce a healthy claim.
3. Telemetry cannot promote or mutate a model.
4. Protected holdout is excluded from iterative evidence.
5. Cross-tenant telemetry is isolated.

### PI-04 — Centralized Runtime Observability

Status: `done` for repository contracts.

Completion: task `FTAI-20260724-portal-pi04-central-runtime-observability`, PR #261, merge `57a48de41daf98fd0360eaecd841b257947e2559`.

Acceptance delivered:

1. Correlation ID traces portal-to-runtime incidents.
2. Secret-like fields are redacted before storage.
3. Cross-tenant queries fail closed.
4. Backend unavailability is explicit and does not erase audit evidence.
5. Raw log access is permission and retention aware.

Real Loki/Tempo/Prometheus connectivity remains deployment-owned.

### PI-05 — External Notification Delivery

Status: `planned`.

Entry gates:

- select one provider/channel;
- declare destination ownership, verification and privacy rules;
- keep provider credentials behind opaque secret references.

Deliverables:

- one email, signed-webhook or push adapter at a time;
- idempotency and delivery-attempt evidence;
- retry/backoff/dead-letter handling;
- preferences and severity/category routing;
- secret-safe delivery status and abuse controls.

Acceptance:

1. Duplicate events do not create undeclared duplicate delivery.
2. Disabled channels/categories are not delivered.
3. Provider outage is retryable and observable.
4. Destinations and secrets remain tenant/actor scoped and hidden.
5. Delivery failure cannot affect trading execution.

Recommended task: `FTAI-YYYYMMDD-portal-pi05-external-notification-delivery`.

### PI-06 — Product Identity, MFA, Session and Membership Lifecycle

Status: `active`.

Goal: replace the trusted development identity boundary with real product identity supporting secure sessions, MFA, revocation, recovery and tenant membership lifecycle.

#### Accepted decision

Task `FTAI-20260726-portal-pi06-identity-decision`, PR #331, selected:

- Authentik as product IdP;
- Authorization Code plus PKCE;
- portal-owned principals, tenants, memberships, roles, capabilities and local revocation;
- immutable OIDC `iss` plus `sub` mapping;
- opaque sessions with no browser-readable IdP token material;
- MFA for mutation-capable roles and five-minute step-up for high-impact administration;
- synchronous membership/session invalidation;
- Cloudflare Access as supplemental ingress only.

#### Completed repository backend

Task `FTAI-20260726-portal-pi06-product-identity-lifecycle`, PR #341, merge `41834d18f3a05b0dfa44dc5af9b97942e685d2a1` delivered OIDC validation, identity/membership/session persistence, CSRF, MFA/step-up, logout, synchronous revocation, back-channel logout, migrations and security tests.

Exact backend head `c258567cabd1c9ddf3d90c63f36319be99463978` passed AI Platform CI #1415, Freqtrade CI #1713 and security #1580.

#### Completed BFF and browser-session integration

Task `FTAI-20260726-portal-pi06-bff-browser-session-integration`, PR #361, merge `4f76eecadcb8dda964a8d247327db9dc6ef1c931` delivered:

- same-origin login, callback, session, logout and logout-all;
- HTTPS-only authorization redirects and relative application returns;
- forwarding of opaque session/CSRF cookies without IdP token exposure;
- optimistic Proxy checks and Route Handler defense in depth;
- double-submit CSRF for existing mutations;
- tenant/MFA session display;
- fixture-only denied, expired, revoked, MFA, step-up and cross-tenant states;
- 37-test Chromium identity and product regression suite.

Exact final head `ec1970a9272bec241a1bab3c447ebd36f53afa58` passed Portal Web CI #287, Portal Universal E2E #292, AI Platform CI #1521, Freqtrade CI #1837 and security #1702.

#### Remaining work

1. Add a separate secret-free Authentik/Synology deployment package with pinned images, private networking, runtime-injected configuration, restricted bootstrap, health checks, migrations, backups, restore and rollback runbooks.
2. On owner-managed target resources, prove OIDC login, MFA enrollment/challenge, session cookies, logout, logout-all, membership revocation, recovery and restore.
3. Keep Cloudflare P11 provisioning and five-probe external acceptance separate.

Full PI-06 acceptance requires:

1. Revoked or expired sessions fail closed on every protected API/browser path.
2. MFA is enforced server-side for privileged roles.
3. Tenant context derives from authenticated portal membership.
4. Role/membership changes are audited and synchronously effective.
5. Recovery does not reveal account existence or bypass MFA.
6. Real target deployment proves login, logout, revocation, recovery and restore without committed credentials.

Completed tasks:

- `FTAI-20260726-portal-pi06-product-identity-lifecycle`;
- `FTAI-20260726-portal-pi06-bff-browser-session-integration`.

Recommended next task: `FTAI-YYYYMMDD-portal-pi06-authentik-synology-deployment`.

### PI-07 — Runtime Credential Broker and Rotation

Status: `planned`.

Entry gates:

- select secret store/KMS and deployment environment;
- review withdrawal-disabled policy;
- make runtime and tenant identity deterministic;
- approve rotation, revocation and incident procedures;
- prove research/training denial.

Acceptance:

1. Plaintext credentials never appear in Git, public APIs, logs, events or audit.
2. One runtime cannot resolve another tenant/runtime reference.
3. Revocation prevents future use and produces evidence.
4. Research/training cannot access runtime credentials.
5. Rotation does not silently change bot/config identity.

Recommended task: `FTAI-YYYYMMDD-portal-pi07-runtime-credential-broker`.

### PI-08 — Private Dry-Run Approved Execution Submission

Status: `planned`.

Entry gates: PI-01 complete, PI-07 complete where credentials are required, P7 risk/kill switches authoritative, command authentication/idempotency approved, and dry-run independently enforced.

Acceptance:

1. Only valid unexpired approved intents for the exact tenant/bot/config/runtime are submitted.
2. Duplicate delivery cannot create unproven duplicate exposure.
3. Kill switch, degraded health or runtime mismatch blocks submission.
4. Ambiguous responses remain unresolved until reconciliation.
5. The implementation cannot select live capital or production credentials.
6. Browsers cannot address Freqtrade directly.

Recommended task: `FTAI-YYYYMMDD-portal-pi08-private-dry-run-submission`.

## 7. Existing governed stages

### P11 — Real Cloudflare Production-Like Staging

Status: `blocked`.

Resume only with explicit owner start, owner-approved Cloudflare Tunnel/DNS/WAF/rate limits/Access/direct-origin denial, protected GitHub variables/secrets, and successful real five-probe `Portal Staging External E2E`. P11 uses simulated execution and does not authorize P14.

Canonical task: `docs/agents/tasks/FTAI-20260723-portal-p11-cloudflare-staging.md`.

### P13 — Scale and Service Extraction

Status: `deferred` until durable measurements identify a specific bottleneck or unmet SLO and justify the smallest change.

### P14 — Live-Small Readiness

Status: `blocked` and outside this backlog's autonomous authority. It requires explicit owner approval, successful P11, independently reviewed model/strategy eligibility, withdrawal-disabled production credentials, strict limits, security/operations evidence and sustained dry-run evidence.

## 8. Recommended execution waves

### Wave PI-A — Truthful operational evidence and identity

PI-01, PI-02, PI-03 and PI-04 are complete. PI-06 decision, repository backend and BFF/browser integration are complete subpackages.

Next:

- add the bounded Authentik/Synology deployment package;
- then collect real owner-managed identity acceptance.

Exit condition: protected browser paths derive identity, tenant and capabilities from the real product session; missing target resources remain explicit; no execution submission is added.

### Wave PI-B — Product completeness from authoritative sources

Declare PI-05 only after provider, channel, privacy and destination ownership decisions.

### Wave PI-C — High-risk private execution enablement

Declare PI-07 before PI-08. No live-capital path exists.

### Wave PI-D — Real external staging

Resume P11 only when explicitly authorized and the staging software/infrastructure set is stable.

### Wave PI-E — Conditional scale or capital

P13 starts only from measured need. P14 starts only from explicit owner approval and all prerequisites.

## 9. Package declaration rules

Before implementing any PI package or subpackage:

1. inspect current `develop`, open PRs, active ownership and CI;
2. create one dated task and branch;
3. declare exact paths and shared-contract coordination;
4. copy entry gates, acceptance and non-goals into the task;
5. identify authoritative sources and unavailability behavior;
6. add tenant, permission, secret-redaction, idempotency and fail-closed tests;
7. run narrow validation and required repository CI;
8. update this backlog only when status or dependency evidence changes;
9. leave P11/P13/P14 semantics unchanged without governed evidence.

Do not broaden a package merely because adjacent code is convenient.

## 10. Priority decision

The next dependency-ordered identity action is **PI-06 Authentik/Synology deployment packaging**. Repository backend and BFF/browser integration are complete; real identity acceptance remains unproven.

PI-05 requires a channel/provider decision. PI-07 requires a secret-store/KMS decision before PI-08. P11 remains owner-started external infrastructure work.

## 11. Completion definition

The post-P12 backlog is complete only when:

- PI-01 through PI-08 are done or explicitly retired;
- P11 real external acceptance is done;
- every portal surface reports authoritative current/stale/unavailable state without fabrication;
- product identity, membership, session, MFA, recovery and revocation are proven through the real protected browser path;
- private dry-run execution is risk-gated, secret-safe, attributable and reconciled;
- P13 remains evidence-triggered;
- P14 remains separately owner-approved and is never inferred from software completion.
