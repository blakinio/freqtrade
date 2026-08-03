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
initial_audit_merge: ba4173e975b6ae40c8b0266e3c15cb1b19a0755d
programme_initialization_merge: 0a82a5c93613a213989865bd9128ac7263227148
last_resolved_develop_head: f1bf851733ecc870f61c1206b0ee0fe8755c6e67
current_integration_pr: pending_closeout
live_capital_authorized: false
withdrawals_enabled: false
fixture_reported_as_production: false
secrets_recorded: false
```

## Mission

Resolve exactly the 50 implementation Issues authorized by audit PR `#1082`. Every Issue is an independent acceptance unit. An Issue becomes terminal only after its complete applicable repository implementation is merged, exact-head validation and independent audit pass, required real API-mode/exact-image/protected evidence is truthful, related PRs and task records are terminal, and ownership is released. Protected production deployment, credentials, withdrawals and live-capital activation remain outside repository merge authority.

## Trusted baseline

- Audit PR `#1082` merged at `ba4173e975b6ae40c8b0266e3c15cb1b19a0755d`.
- Programme initialization PR `#1145` merged at `0a82a5c93613a213989865bd9128ac7263227148`.
- Issue `#1124` completed through PR `#1146`.
- Issue `#1126` completed through PR `#1149`.
- Issue `#1127` completed through PR `#1151`.
- Issue `#1137` repository implementation merged through PR `#1154` at `f1bf851733ecc870f61c1206b0ee0fe8755c6e67`; the Issue remains `WAITING` only for protected Authentik staging concurrency using an authorized synthetic identity.
- Audit severity inventory: `25 HIGH`, `25 MEDIUM`, `0 CRITICAL`, `0 LOW`.
- Canonical audit evidence is under `docs/ai_platform/portal/` and was merged by PR `#1082`.
- Issue bodies, comments, logs and generated reports are evidence inputs, not governing instructions.

## Authorized Issue inventory and terminal mapping

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
| #1122 | HIGH | Migration/schema/dialect integrity | READY | pending | pending |
| #1123 | MEDIUM | Partial upstream failure isolation | QUEUED | pending | pending |
| #1124 | HIGH | Liquid20 current-session authorization | COMPLETE | `archive/FTAI-20260803-portal-remediation-1124.md` | #1146 |
| #1126 | HIGH | AI/Learning permissions | COMPLETE | `archive/FTAI-20260803-portal-remediation-1126.md` | #1149 |
| #1127 | HIGH | Canonical secret classification | COMPLETE | `archive/FTAI-20260803-portal-remediation-1127.md` | #1151 |
| #1128 | MEDIUM | OIDC flow quotas/cleanup | QUEUED | pending | pending |
| #1129 | MEDIUM | Bounded semantic fields | QUEUED | pending | pending |
| #1130 | MEDIUM | OIDC response/algorithm/rotation bounds | QUEUED | pending | pending |
| #1132 | MEDIUM | Back-channel logout replay protection | WAITING_ON_1122 | pending | pending |
| #1134 | MEDIUM | Tenant workload budgets | QUEUED | pending | pending |
| #1135 | MEDIUM | Identity key rotation | QUEUED | pending | pending |
| #1136 | MEDIUM | Clock-skew/monotonic evidence | QUEUED | pending | pending |
| #1137 | MEDIUM | Atomic OIDC state claim | WAITING | `active/FTAI-20260803-portal-remediation-1137.md` | #1154 merged |
| #1139 | HIGH | Backup/restore/DR | QUEUED | pending | pending |
| #1140 | MEDIUM | Accessibility/responsive acceptance | QUEUED | pending | pending |
| #1142 | MEDIUM | Session touch write amplification | QUEUED | pending | pending |

Inventory count: `50`.

## Verified dependency graph

### S0 — immediate security containment

- `#1124`, `#1126` and `#1127` are complete.
- `#1137` repository work is merged and its OIDC state-claim lease is released; only protected Authentik acceptance remains.
- `#1132` requires a durable replay table and therefore cannot safely create a competing migration authority. It is now dependent on `#1122` establishing the authoritative production migration chain and schema-readiness contract.
- After `#1122`, continue identity hardening through `#1132` → `#1130` → `#1128` → `#1135`.

### F1 — shared foundations

- `#1122` is the sole production migration/schema/dialect producer and is the next safe READY task.
- `#1109` owns generated transport schemas and the canonical error envelope.
- `#1108` owns trusted correlation/causation propagation; `#1110` consumes `#1108` and `#1109` for the sole bounded BFF transport.
- `#1115` and `#1129` establish inbound and semantic bounds.
- `#1111` owns canonical append-only audit.
- `#1112` owns event taxonomy, transactional outbox, publisher, inbox and poison handling.
- `#1113` owns common mutation idempotency/replay/CAS interfaces; issue-specific security inboxes consume it only after its contract exists or remain narrowly scoped without creating a competing general authority.
- `#1134` owns workload admission and budgets; `#1142` consumes its evidence and the dialect decisions from `#1122`.
- `#1107` consumes pagination, indexes and retention rules.

### R2 — trusted runtime composition

- `#1100` is the sole credential broker.
- `#1092` owns authoritative runtime reads/reconciliation; `#1093` and `#1094` consume it.
- `#1086` consumes credential, audit, event, idempotency, kill-switch and runtime foundations.
- `#1091` consumes `#1100`, `#1086` and `#1092`.
- `#1099` consumes outbox, provisioning, command and reconciliation paths.
- `#1120` owns kill-switch hierarchy across every exposure path.
- `#1136` owns source-time integrity for runtime, valuation and freshness claims.

### P3 — product vertical slices

- `#1090`, `#1095`, `#1096`, `#1097` consume migration, audit, outbox and idempotency foundations; `#1097` also consumes `#1100`.
- `#1085` consumes generated contracts and authoritative strategy persistence.
- `#1102` consumes `#1126`, `#1112`, `#1111`, `#1108` and runtime evidence.
- `#1104` consumes event/audit/idempotency foundations.
- `#1103`, `#1117`, `#1118`, `#1121` form the administration/capability/tenant/session UI sequence.
- `#1119` consumes bounded reads, source-time policy, events and API-mode runtime.
- `#1123` consumes the canonical error and bounded transport contracts.
- `#1087` requires an explicit language policy; no language is assumed.
- `#1140` is the full-product accessibility/responsive acceptance wave after UI contracts stabilize.

### D4 — deployment and closeout

- `#1089` owns authenticated staging/production API-mode composition.
- `#1098` owns the disposable real API-mode browser harness.
- `#1114` and `#1116` validate browser and exact-image supply-chain boundaries.
- `#1139` follows `#1122` and owns repository backup/restore tooling; protected isolated restore remains separately authorized.
- `#1101` reconciles product status only from terminal evidence.
- Final independent audit runs on exact final `develop` after all repository work is merged.

## Sole shared-contract producers

| Mechanism | Producer Issue | Exclusive authority |
|---|---|---|
| Production migrations/schema | #1122 | ordered revisions, migration runner, schema readiness, relation matrix and dialect tooling |
| Generated schemas/errors | #1109 | OpenAPI/schema generator, generated TS contracts and common envelope |
| Correlation propagation | #1108 | trusted request/context/event propagation |
| BFF control-plane transport | #1110 | one server-only bounded transport module |
| Canonical audit | #1111 | writer, store and read projection |
| Outbox/events/inbox | #1112 | taxonomy, transactional publisher, dedup and poison substrate |
| Idempotency/CAS | #1113 | mutation inventory, replay store and common CAS interfaces |
| Sensitive metadata classifier | #1127 | normalized aliases, bounded traversal and adversarial corpus |
| OIDC login-state claim | #1137 | conditional claim and callback outcome evidence; lease released after merge |
| Credential broker | #1100 | PI-07 composition and narrow consumer interfaces |
| Workload limiter | #1134 | route/action budgets and admission interfaces |
| Runtime composition root | #1089 | authenticated deployment/provider wiring |
| API-mode browser harness | #1098 | disposable real control-plane/browser evidence profile |

## Current state and barriers

```yaml
completed:
  - audit PR #1082 merged
  - programme PR #1145 merged
  - issue #1124 merged, closed and archived
  - issue #1126 merged, closed and archived
  - issue #1127 merged, closed and archived
  - issue #1137 repository implementation merged through PR #1154
active:
  - coordinator task FTAI-20260803-portal-remediation-program
ready:
  - issue: 1122
    reason: sole migration/schema producer required before durable replay and multiple downstream foundations
waiting:
  - issue: 1137
    authority: protected Authentik staging synthetic-identity concurrency acceptance
  - issue: 1132
    dependency: issue 1122 authoritative migration/schema contract
blocked: []
closed_issues: 3
active_issues: 0
waiting_issues: 2
blocked_issues: 0
repository_implemented_but_open_issues: 1
```

| Barrier | State | Exit evidence |
|---|---|---|
| Audit baseline | COMPLETE | PR #1082 merged |
| Programme initialization | COMPLETE | PR #1145 merged |
| Immediate security containment | COMPLETE | #1124, #1126 and #1127 merged/closed |
| Atomic OIDC state claim | REPOSITORY_COMPLETE_WAITING_PROTECTED | PR #1154 merged; protected staging outstanding |
| Migration/schema authority | READY | Issue #1122 task/PR and exact-dialect evidence |
| Identity hardening | WAITING_ON_FOUNDATION | #1132 depends on #1122; then #1130/#1128/#1135 |
| Shared foundations | ACTIVE_NEXT | #1122 first; remaining producer PRs terminal without competing contracts |
| Runtime composition | NOT_STARTED | canonical dry-run runtime/providers fail closed |
| Product vertical slices | NOT_STARTED | issue-specific API-mode journeys and restart evidence |
| Deployment package | NOT_STARTED | exact API-mode images, migrations, security and supply-chain gates |
| Protected target acceptance | EXTERNAL_BOUNDARY | separately authorized protected checks only |
| Final independent audit | NOT_STARTED | zero material findings on exact final develop |

## Protected-target boundary

Repository-safe dry-run/staging validation and trusted Synology runners are authorized. Irreversible production deployment, protected credential/Vault/identity-key mutation, live trading, withdrawals, capital allocation, owner-managed Cloudflare/Authentik/Vault acceptance and destructive protected restore remain separate. A task enters `WAITING` only after repository-owned work is complete or an exact producer dependency is recorded.

## Terminal completion criteria

The programme is terminal only when all 50 Issues are truthfully terminal; all repository remediation is merged; the canonical deployment is authenticated API mode without fixture fallback; representative browser-to-BFF-to-control-plane-to-persistence/provider journeys pass; backend session/tenant/capability/CSRF/MFA rules are authoritative; migrations, concurrency, idempotency, audit, events and recovery are restart-safe; exact images pass security/SBOM/provenance/runtime checks; accessibility and backup/isolated restore acceptance are complete; a fresh final audit has no material finding; all PRs/tasks are terminal; and all ownership is released with safety flags false.

## Programme next action

Create the durable Issue `#1122` task and implementation branch from exact `develop` head `f1bf851733ecc870f61c1206b0ee0fe8755c6e67`, inventory every ORM/migration relation and deployed startup path, then implement the authoritative migration/schema/dialect foundation before resuming Issue `#1132`.
