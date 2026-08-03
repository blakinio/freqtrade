# AI Trading Portal Remediation Programme

```yaml
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
default_integration_branch: develop
programme_lane: freqtrade-portal
status: active
prompting_standard_version: 2.1
execution_policy_version: 2
task_kind: durable_remediation_program
context_pressure: high
decomposition_decision: split
coordinator_execution_mode: chat
implementation_worker_mode: codex_or_github_actions
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
live_capital_authorized: false
withdrawals_enabled: false
fixture_reported_as_production: false
```

## Mission

Resolve exactly the 50 implementation Issues authorized by the terminal AI Trading Portal completeness audit. Every Issue remains an independent acceptance unit and is terminal only after complete applicable implementation, independent audit, real API-mode or system E2E, exact-head CI, PR hygiene, archival and ownership release. Protected production deployment, real credentials, withdrawals and live-capital activation are outside this programme's repository merge authority.

## Baseline

- Audit PR: `#1082` — merged into `develop` by squash commit `ba4173e975b6ae40c8b0266e3c15cb1b19a0755d`.
- Exact initial programme base: `ba4173e975b6ae40c8b0266e3c15cb1b19a0755d`.
- Audit product verdict: incomplete; `25 HIGH`, `25 MEDIUM`, `0 CRITICAL`, `0 LOW`.
- Audit evidence: `docs/ai_platform/portal/AUDIT_2026-08-02_END_TO_END_COMPLETENESS.md` and linked generated matrices.
- Existing remediation programme/task/branch/PR at initialization: none found in live GitHub state.
- Open implementation PRs related to this authorized set at initialization: none found.
- Issue labels, milestones and GitHub Project placement: `UNKNOWN` where the connector did not expose authoritative metadata; Issue number and body remain acceptance inputs only.

## Authorized Issue inventory and task/PR map

Only these Issues are in scope. `QUEUED` means no child branch or PR has been claimed yet. The coordinator creates the durable task before any product mutation.

| Issue | Severity | Primary module | State | Durable task | PR |
|---|---|---|---|---|---|
| #1085 | HIGH | Strategy Catalog producer/API slice | QUEUED | pending | pending |
| #1086 | HIGH | PI-08 private dry-run composition | QUEUED | pending | pending |
| #1087 | MEDIUM | Localization boundary | QUEUED | pending | pending |
| #1089 | HIGH | API-mode authenticated deployment | QUEUED | pending | pending |
| #1090 | HIGH | Durable Create Bot materialization | QUEUED | pending | pending |
| #1091 | HIGH | BM-07 command activation | QUEUED | pending | pending |
| #1092 | HIGH | PI-01 runtime collection/reconciliation | QUEUED | pending | pending |
| #1093 | HIGH | PI-02 valuation composition | QUEUED | pending | pending |
| #1094 | HIGH | PI-04 observability composition | QUEUED | pending | pending |
| #1095 | HIGH | Signed Signal control | QUEUED | pending | pending |
| #1096 | HIGH | Grid policy persistence/UI | QUEUED | pending | pending |
| #1097 | HIGH | Exchange connection lifecycle | QUEUED | pending | pending |
| #1098 | MEDIUM | Real API-mode browser E2E | QUEUED | pending | pending |
| #1099 | HIGH | Desired-state outbox activation | QUEUED | pending | pending |
| #1100 | HIGH | PI-07 credential broker composition | QUEUED | pending | pending |
| #1101 | MEDIUM | Canonical completeness ledger | QUEUED | pending | pending |
| #1102 | HIGH | AI/learning/model lifecycle | QUEUED | pending | pending |
| #1103 | MEDIUM | Administration workflows | QUEUED | pending | pending |
| #1104 | MEDIUM | Notification channels/rules | QUEUED | pending | pending |
| #1107 | HIGH | Pagination and retention | QUEUED | pending | pending |
| #1108 | MEDIUM | Correlation/causation propagation | QUEUED | pending | pending |
| #1109 | MEDIUM | Generated contracts/error envelope | QUEUED | pending | pending |
| #1110 | MEDIUM | BFF bounded transport | QUEUED | pending | pending |
| #1111 | HIGH | Canonical append-only audit | QUEUED | pending | pending |
| #1112 | HIGH | Transactional outbox/domain events | QUEUED | pending | pending |
| #1113 | HIGH | Idempotency and optimistic concurrency | QUEUED | pending | pending |
| #1114 | MEDIUM | Browser security headers | QUEUED | pending | pending |
| #1115 | MEDIUM | Inbound request limits | QUEUED | pending | pending |
| #1116 | MEDIUM | Exact-image SBOM/provenance | QUEUED | pending | pending |
| #1117 | MEDIUM | Capability-aware UI | QUEUED | pending | pending |
| #1118 | MEDIUM | Tenant selection/switching | QUEUED | pending | pending |
| #1119 | HIGH | Freshness-aware operational updates | QUEUED | pending | pending |
| #1120 | HIGH | Hierarchical kill switch | QUEUED | pending | pending |
| #1121 | MEDIUM | Session inventory/revocation | QUEUED | pending | pending |
| #1122 | HIGH | Migration/schema/dialect integrity | QUEUED | pending | pending |
| #1123 | MEDIUM | Partial upstream failure isolation | QUEUED | pending | pending |
| #1124 | HIGH | Liquid20 current-session authorization | READY | `FTAI-20260803-portal-remediation-1124` to create | pending |
| #1126 | HIGH | AI/Learning permissions | READY_AFTER_1124_CLAIM | pending | pending |
| #1127 | HIGH | Canonical secret classification | READY_AFTER_1124_CLAIM | pending | pending |
| #1128 | MEDIUM | OIDC flow quotas/cleanup | QUEUED | pending | pending |
| #1129 | MEDIUM | Bounded semantic fields | QUEUED | pending | pending |
| #1130 | MEDIUM | OIDC response/algorithm/rotation bounds | QUEUED | pending | pending |
| #1132 | MEDIUM | Back-channel logout replay protection | QUEUED | pending | pending |
| #1134 | MEDIUM | Tenant workload budgets | QUEUED | pending | pending |
| #1135 | MEDIUM | Identity key rotation | QUEUED | pending | pending |
| #1136 | MEDIUM | Clock-skew/monotonic evidence | QUEUED | pending | pending |
| #1137 | MEDIUM | Atomic OIDC state claim | QUEUED | pending | pending |
| #1139 | HIGH | Backup/restore/DR | QUEUED | pending | pending |
| #1140 | MEDIUM | Accessibility/responsive acceptance | QUEUED | pending | pending |
| #1142 | MEDIUM | Session touch write amplification | QUEUED | pending | pending |

Inventory count: `50`.

## Dependency graph and integration waves

The graph is evidence-driven and must be revised when exact code/Issue analysis disproves a dependency.

### Wave S0 — immediate containment

- `#1124` current-session authorization for Liquid20 local-file reads: first READY task; no shared producer dependency is required for a complete bounded fix.
- `#1126` AI/Learning explicit service permissions: independent after ownership preflight.
- `#1127` canonical sensitive-field classification: independent producer; consumers must not create competing alias sets.
- `#1137`, `#1132`, `#1130`, `#1128`, `#1135`: identity hardening sequence, ordered by shared identity persistence/migration ownership.

### Wave F1 — shared persistence, contract and reliability foundations

- `#1122` owns production migration authority, schema revision readiness and dialect parity.
- `#1109` owns generated transport schemas and canonical error envelope.
- `#1108` owns trusted request/correlation/causation propagation.
- `#1110` consumes `#1109` and `#1108` for the shared bounded BFF transport.
- `#1115` and `#1129` own inbound and semantic field/collection limits; both feed contract generation.
- `#1111` owns the canonical audit writer/read projection.
- `#1112` owns event taxonomy, transactional outbox publisher and inbox/poison substrate.
- `#1113` owns durable mutation replay/CAS policy and shared store.
- `#1134` owns application workload limiter/admission substrate.
- `#1142` depends on production-dialect decisions in `#1122` and workload evidence in `#1134`.
- `#1107` consumes pagination contracts, migration indexes and workload/retention rules.

### Wave R2 — trusted runtime composition

- `#1100` is the sole credential broker producer.
- `#1092` is the authoritative private runtime read/reconciliation producer.
- `#1093` depends on the runtime identity/read boundary from `#1092`.
- `#1094` composes the approved observability source and consumes redaction/correlation rules.
- `#1086` composes PI-08 and consumes `#1100`, `#1111`, `#1112`, `#1113`, `#1120` policy and runtime reconciliation.
- `#1091` consumes `#1100`, `#1086` for exposure-increasing replacements, and `#1092` for reconciliation.
- `#1099` consumes `#1112`, `#1092`, `#1091` and runtime provisioning.
- `#1120` owns kill-switch hierarchy/contracts and must integrate with all exposure paths; repository implementation may begin after shared audit/outbox/idempotency contracts stabilize.
- `#1136` provides source-time integrity before runtime/valuation/telemetry freshness can be called complete.

### Wave P3 — durable product vertical slices

- `#1090`, `#1095`, `#1096`, `#1097` consume migration, audit, outbox and idempotency foundations.
- `#1097` additionally consumes the sole credential broker `#1100`.
- `#1085` consumes generated contracts, audit/idempotency and authoritative strategy persistence.
- `#1102` consumes AI permissions `#1126`, events `#1112`, audit `#1111`, correlation `#1108` and runtime evidence.
- `#1104` consumes shared events/audit/idempotency; real external channel acceptance may remain separately WAITING after repository-owned work.
- `#1103`, `#1117`, `#1118`, `#1121` form the identity/capability/admin UI sequence.
- `#1119` consumes bounded reads, freshness/source-time policy, event publication and API-mode runtime.
- `#1123` consumes the canonical error and bounded transport contracts.
- `#1087` requires an explicit owner-approved language policy before final acceptance; implementation must not guess it.
- `#1140` spans all final user-facing workflows and runs after principal UI contracts stabilize.

### Wave D4 — deployment, evidence and closeout

- `#1089` composes the authenticated complete API runtime and consumes shared migration/runtime producers.
- `#1098` establishes real API-mode browser acceptance and is a downstream gate for user-facing Issues.
- `#1114` and `#1116` validate the exact deployed candidate and supply-chain/browser boundary.
- `#1139` implements repository-owned backup/restore tooling after schema/dialect authority is stable; protected isolated restore acceptance remains separately authorized.
- `#1101` reconciles the canonical status ledger only from verified terminal evidence.
- Final fresh independent audit runs after all repository-owned fixes are merged.

## Shared-contract ownership

Exactly one task may hold each producer lease. Consumers may edit exclusive module paths but may not create substitutes.

| Shared mechanism | Sole producer Issue | Initial owned path families |
|---|---|---|
| Production migration/schema authority | #1122 | `ai_platform/portal/**/migrations/**`, schema readiness and migration tooling |
| Transport schema and error envelope | #1109 | canonical OpenAPI/schema generator, generated TS transport contracts, shared errors |
| Correlation propagation | #1108 | trusted BFF/backend context middleware and event propagation contract |
| BFF control-plane transport | #1110 | one server-only bounded transport module |
| Canonical audit writer/projection | #1111 | audit contract/writer/store/read projection |
| Transactional outbox/publisher/inbox | #1112 | event taxonomy, outbox abstraction, publisher and dedup substrate |
| Durable idempotency/CAS | #1113 | mutation inventory, key store and common replay/CAS interfaces |
| Sensitive metadata classifier | #1127 | shared secret-key/value classification and corpus |
| Credential broker | #1100 | PI-07 Vault broker composition and narrow consumer interfaces |
| Workload limiter | #1134 | route/action budgets and shared limiter/admission interfaces |
| Product runtime composition root | #1089 | authenticated production/staging app composition and provider wiring |
| API-mode browser harness | #1098 | disposable real control-plane/browser environment and evidence profile |

A child task records exact path ownership and any shared lease before mutation. Overlap requires serialization or explicit producer/consumer integration order.

## Programme barriers

| Barrier | Current state | Exit evidence |
|---|---|---|
| Audit baseline | COMPLETE | PR #1082 merged at `ba4173e975b6ae40c8b0266e3c15cb1b19a0755d` |
| Immediate security containment | READY | #1124, #1126, #1127 terminal |
| Shared foundations | NOT_STARTED | producer PRs merged with exact-head tests and no competing contracts |
| Runtime composition | NOT_STARTED | canonical dry-run runtime and providers selected fail closed |
| Product vertical slices | NOT_STARTED | issue-specific real API-mode journeys and restart evidence |
| Deployment package | NOT_STARTED | exact API-mode images, migrations, security and supply-chain gates |
| Protected target acceptance | EXTERNAL_BOUNDARY | separately authorized Synology/Auth/Cloudflare/Vault/private-runtime checks only |
| Final independent audit | NOT_STARTED | zero open material findings on final `develop` |

## Current programme state

```yaml
completed:
  - audit PR #1082 merged into develop at ba4173e975b6ae40c8b0266e3c15cb1b19a0755d
active:
  - coordinator task FTAI-20260803-portal-remediation-program
ready:
  - issue: 1124
    reason: active application authorization bypass; bounded paths; no unresolved producer dependency
  - issue: 1126
    reason: independent service-level permission containment after ownership preflight
  - issue: 1127
    reason: independent canonical secret-classifier producer after ownership preflight
waiting: []
blocked: []
closed_issues: 0
active_issues: 0
waiting_issues: 0
blocked_issues: 0
```

## Protected-target acceptance boundary

Repository-safe dry-run/staging validation and existing trusted Synology runners are authorized. The following remain separate and cannot be inferred from repository CI:

- irreversible production deployment;
- real credential, Vault secret or identity-key mutation;
- live trading, withdrawals, live-capital activation or capital allocation;
- owner-managed Cloudflare/Authentik/Vault/private Freqtrade acceptance requiring protected secrets or approval;
- destructive restore against a real protected environment.

Repository-owned work must be complete before any task is classified `WAITING` on one exact external authority/resource.

## Terminal completion criteria

The programme is terminal only when:

1. all 50 authorized Issues are closed by verified terminal outcomes or accurately classified by one exact external blocker after all repository-owned work is complete;
2. every linked implementation/audit/validation/archive PR is intentionally terminal;
3. no HIGH or material MEDIUM finding remains;
4. canonical deployment runs API mode and cannot use fixtures in staging/production;
5. representative browser → same-origin BFF → authenticated control plane → persistence/provider → refreshed UI journeys pass without interception/fallback;
6. current session, tenant, permissions, CSRF and MFA are backend-authoritative;
7. migrations, persistence, concurrency, idempotency, audit, events and recovery are restart-safe;
8. exact images pass SBOM, vulnerability, provenance, runtime and security validation;
9. accessibility and backup/isolated restore acceptance are complete where applicable;
10. fresh independent audit reports zero open material findings on exact final `develop`;
11. all tasks are archived/terminal and all path ownership/leases are released;
12. safety flags remain false for live capital, withdrawals, secret recording and fixture-as-production claims.

## Programme next action

Create and claim durable child task `FTAI-20260803-portal-remediation-1124` from the current exact `develop` head, assign only the Liquid20/local-file BFF authorization paths, reproduce the cookie-presence bypass and implement the smallest complete current-session authorization repair.
