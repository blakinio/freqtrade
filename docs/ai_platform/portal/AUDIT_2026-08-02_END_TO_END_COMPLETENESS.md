# AI Trading Portal end-to-end completeness audit — terminal report

## Audit identity

- Repository: `blakinio/freqtrade`
- Audited Portal product base: `626087ca45d67eb908d6c1f1f419f13cbd49f596`
- Canonical audit PR: #1082
- Scope: AI Trading Portal only; audit documentation, deterministic inventory tooling and audit-only CI evidence.
- Product code, deployment, credentials, trading state and live-capital authority changed: **no**.

Later `develop` changes were reviewed. They affect governance, task records and WickHunter implementation/tests, not the audited `ai_platform/portal/**` product behavior.

## Conclusion

**The AI Trading Portal is not complete end to end.**

The repository contains substantial contracts, durable services, security boundaries and focused tests. However, the production-labelled deployment remains fixture-backed and identity-only, multiple adapters/providers are not composed into the canonical runtime, several user workflows terminate in in-memory or unavailable implementations, and browser closure does not exercise the real composed control plane.

No canonical left-navigation item is fully end-to-end `COMPLETE` while the global deployment and API-mode E2E blockers remain open.

## Exact inventory

- Backend modules: **30**
- FastAPI route declarations: **92**
- Next.js pages: **33**
- Same-origin BFF handlers: **28**
- Canonical left-navigation items: **28**
- Focused test files: **225**
- Broken detected navigation destinations: **0**
- Direct browser references to private Freqtrade or Vault authority: **0**

## Backend module completeness

- `COMPLETE`: 6
- `PARTIAL`: 8
- `MISSING`: 0
- `DISCONNECTED`: 14
- `FIXTURE_ONLY`: 1
- `EXTERNAL_ACCEPTANCE_REQUIRED`: 1
- `BLOCKED`: 0
- `NOT_APPLICABLE`: 0

## Left-navigation completeness

- `COMPLETE`: 0
- `PARTIAL`: 9
- `MISSING`: 1
- `DISCONNECTED`: 15
- `FIXTURE_ONLY`: 0
- `EXTERNAL_ACCEPTANCE_REQUIRED`: 3
- `BLOCKED`: 0
- `NOT_APPLICABLE`: 0

The complete 28-row evidence remains in `AUDIT_2026-08-03_LEFT_NAVIGATION_COMPLETENESS.md` and the generated navigation matrices.

## Finding totals

The audit produced **50 open, non-duplicate implementation Issues**:

- `CRITICAL`: **0**
- `HIGH`: **25**
- `MEDIUM`: **25**
- `LOW`: **0**

Open remediation Issues are the expected result of an audit-only task. They prove product incompleteness; PR #1082 does not implement them.

## Confirmed findings

### Product runtime, module and workflow findings

| Issue | Severity | Finding |
|---|---|---|
| #1085 | `HIGH` | Strategy Catalog has no backend producer/API-mode vertical slice. |
| #1086 | `HIGH` | PI-08 private dry-run submission is not composed; dry-run verification has a TOCTOU boundary. |
| #1087 | `MEDIUM` | No explicit testable localization/product-language boundary. |
| #1089 | `HIGH` | Production-labelled package runs fixture web data and identity-only control plane. |
| #1090 | `HIGH` | Create Bot does not materialize a durable canonical bot. |
| #1091 | `HIGH` | BM-07 activation is not composed; alternative routes accept caller-supplied authoritative state and lose partial-effect detail. |
| #1092 | `HIGH` | PI-01 private runtime collection/reconciliation is not scheduled or composed. |
| #1093 | `HIGH` | PI-02 authoritative valuation source is not composed. |
| #1094 | `HIGH` | PI-04 runtime observability source is not composed. |
| #1095 | `HIGH` | Signed Signal control is in-memory/unavailable and lacks an operable canonical UI/trusted state boundary. |
| #1096 | `HIGH` | Canonical Grid policy is in-memory/unavailable and lacks an operable trusted capability workflow. |
| #1097 | `HIGH` | Exchange Connection lifecycle lacks durable storage, trusted verification worker and management UI. |
| #1098 | `MEDIUM` | Browser E2E is fixture-only; local API-mode cookie contracts are inconsistent. |
| #1099 | `HIGH` | Desired-state outbox is not published/consumed into the private dry-run runtime. |
| #1100 | `HIGH` | PI-07 Vault broker is not composed and credential lease TTL is not enforced at every use. |
| #1101 | `MEDIUM` | Active status documents make conflicting completion claims. |
| #1102 | `HIGH` | AI intelligence, learning and model lifecycle producers/actions are simulator/test-only or absent. |
| #1103 | `MEDIUM` | Administration is read-only and lacks true step-up and last-admin protection. |
| #1104 | `MEDIUM` | Notifications lack complete channels, worker, retry/dead-letter and rule policy. |

### Shared transport, data, security, reliability and usability findings

| Issue | Severity | Finding |
|---|---|---|
| #1107 | `HIGH` | Growing reads use unbounded materialization; pagination, indexed filters, retention and bounded local-file parsing are incomplete. |
| #1108 | `MEDIUM` | Trusted request/correlation/causation identity is not propagated across BFF, backend, events and runtime. |
| #1109 | `MEDIUM` | Contracts are manually duplicated, upstream JSON is unchecked and error envelopes are inconsistent. |
| #1110 | `MEDIUM` | BFF/control-plane calls lack shared timeout, cancellation, redirect, content-type and response-size limits. |
| #1111 | `HIGH` | Audit Events is not a complete append-only privileged-action/outcome record and lacks integrity-chain evidence. |
| #1112 | `HIGH` | Transactional outbox/domain-event coverage and publisher/inbox/poison handling are incomplete. |
| #1113 | `HIGH` | Mutations lack uniform durable idempotency and optimistic concurrency/CAS. |
| #1114 | `MEDIUM` | No repository-verifiable browser security-header and authenticated cache policy. |
| #1115 | `MEDIUM` | Inbound body, depth, cardinality, query/form and content-type limits are missing before parsing. |
| #1116 | `MEDIUM` | Exact Portal images lack SBOM, vulnerability/license policy and provenance. |
| #1117 | `MEDIUM` | Navigation/actions are not capability-aware; local Market Evidence uses a separate role-name policy. |
| #1118 | `MEDIUM` | Multi-membership principals cannot select or switch tenants through the product. |
| #1119 | `HIGH` | Operational views have no bounded freshness-aware update/stale transition mechanism. |
| #1120 | `HIGH` | Hierarchical emergency kill switch is not exposed, composed or visibly enforced. |
| #1121 | `MEDIUM` | Profile & Security lacks active-session inventory/targeted revoke; identity variants differ in cookie clearing. |
| #1122 | `HIGH` | ORM/create-all and migrations diverge, SQLite FKs are not enabled, three tables lack migrations and production dialect parity is unproven. |
| #1123 | `MEDIUM` | Multi-source pages discard available evidence when one optional source fails. |
| #1124 | `HIGH` | Liquid20 trusts cookie presence instead of current backend session/tenant/permission authorization. |
| #1126 | `HIGH` | AI Intelligence/Learning reads and producers enforce tenant scope but no explicit permission. |
| #1127 | `HIGH` | Secret detection/redaction is inconsistent and accepts common raw credential/session aliases. |
| #1128 | `MEDIUM` | Public OIDC login starts create unbounded durable flow rows without quota/cleanup. |
| #1129 | `MEDIUM` | Public fields/collections lack semantic maximums aligned with storage/providers. |
| #1130 | `MEDIUM` | OIDC provider responses are unbounded; algorithm policy and same-`kid` rotation recovery are incomplete. |
| #1132 | `MEDIUM` | OIDC back-channel logout does not require/replay-protect `jti`. |
| #1134 | `MEDIUM` | Protected APIs lack per-tenant/actor rate, concurrency and workload budgets. |
| #1135 | `MEDIUM` | Identity HMAC/encryption keys lack versioned staged rotation. |
| #1136 | `MEDIUM` | Runtime/valuation/telemetry timestamps lack one skew/monotonicity policy. |
| #1137 | `MEDIUM` | OIDC login-state consumption is not atomic under concurrent callbacks. |
| #1139 | `HIGH` | Portal application state lacks encrypted backup, isolated restore and measured RPO/RTO. |
| #1140 | `MEDIUM` | Accessibility/responsive acceptance is incomplete: keyboard, focus, field errors, reduced motion and standards-based scanning. |
| #1142 | `MEDIUM` | Every authenticated read commits a session activity/idle-expiry write, amplifying SQLite contention. |

## Quantitative cross-cutting evidence

- **35** collection-like GET routes have no cursor/page/limit argument.
- At least **31** repository queries use unbounded `.all()` materialization.
- At least **5** independent generic web API clients and **34** unchecked upstream JSON assertions/casts exist.
- **17** control-plane-oriented `fetch()` call sites lacked explicit timeout/abort and response-size limits.
- Shared `NonEmptyStr` appears approximately **829** times without a maximum length; no Portal production `Field(max_length=...)` declaration was found.
- ORM metadata defines **41** Portal tables while migrations define **38**.
- Only one production repository query uses `with_for_update()`; no SQLAlchemy optimistic-version mapper was found.
- Accessibility acceptance covers **5 of 33** pages and responsive acceptance covers two journeys.
- The Portal renders approximately **44** tables without a complete semantic/keyboard/overflow acceptance inventory.
- Every protected FastAPI request currently writes session activity by default.

## Positive controls and reviewed non-findings

- Same-origin browser architecture; no direct browser authority over Vault, Freqtrade or exchanges detected.
- Random opaque sessions stored as HMAC digests and constant-time CSRF validation.
- OIDC state, nonce, PKCE, issuer, audience, expiry and signature validation.
- Credential lease non-serialization, hidden representation and zeroization.
- Vault/private-runtime path/origin confinement, TLS/private trust, redirect/proxy disablement and response bounds.
- Runtime acknowledgement remains distinct from execution proof.
- Market Evidence file confinement, symlink and integrity checks.
- Non-root containers plus read-only filesystem, tmpfs, dropped capabilities, no-new-privileges and resource limits.
- Public request models generally reject unknown fields.
- Dry-run/live-capital authority remained blocked and was never exercised.

## Evidence classification and external gates

Static/component/integration/fixture/simulator evidence remains distinct from canonical runtime composition, deployment-package validation and real protected-target acceptance. Real Authentik, Vault, Cloudflare, Synology and private Freqtrade acceptance was not performed or claimed. Live-small/live-capital operations remain blocked and unauthorized.

## Durable outputs

- this terminal report;
- `AUDIT_2026-08-03_LEFT_NAVIGATION_COMPLETENESS.md`;
- terminal task checkpoint;
- four deterministic audit generators;
- audit-only GitHub Actions workflow and exact-head evidence artifact;
- 50 implementation Issues with evidence, impact, required work, acceptance criteria and safety boundaries.

The exact final head, workflow run IDs and artifact ID/name/digest are recorded in live PR #1082 metadata after exact-head validation because a commit cannot contain its own resulting SHA.

## Final disposition

```yaml
audit_result: FAIL_PRODUCT_COMPLETENESS
audit_work_complete: true
portal_end_to_end_complete: false
findings_open: 50
critical: 0
high: 25
medium: 25
low: 0
implementation_delegated_to_linked_issues: true
protected_target_acceptance_performed: false
secret_values_recorded: false
live_capital_authorized: false
product_code_changed: false
```
