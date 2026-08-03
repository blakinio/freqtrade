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
last_resolved_develop_head: 9b865a64897ef17004809ccf4973c7a930fe4314
current_integration_pr: 1149
validated_current_pr_head: bdfd35c117c8595d3dddaf2542f632fd1cbecff7
live_capital_authorized: false
withdrawals_enabled: false
fixture_reported_as_production: false
secrets_recorded: false
```

## Mission

Resolve exactly the 50 implementation Issues authorized by audit PR `#1082`. Each Issue is an independent acceptance unit and is terminal only after complete applicable implementation, persistent outcome evidence, fresh audit, real API-mode/system E2E where applicable, exact-head CI, merge, Issue reconciliation, task archival and ownership release. Protected production deployment, credentials, withdrawals and live-capital activation remain outside repository merge authority.

## Trusted baseline

- Audit PR `#1082` is merged at `ba4173e975b6ae40c8b0266e3c15cb1b19a0755d`.
- Programme initialization PR `#1145` is merged at `0a82a5c93613a213989865bd9128ac7263227148`.
- Issue `#1124` is merged through PR `#1146` at `9b865a64897ef17004809ccf4973c7a930fe4314`.
- Issue `#1126` is implementation-complete and archived in PR `#1149`; merge remains gated only by exact closeout-head checks.
- Issue `#1127` is independently claimed on non-overlapping paths while `#1149` closes.
- Audit verdict at initialization: `25 HIGH`, `25 MEDIUM`, `0 CRITICAL`, `0 LOW`.
- Canonical audit evidence: `docs/ai_platform/portal/AUDIT_2026-08-02_END_TO_END_COMPLETENESS.md` and its generated matrices.
- Issue bodies are evidence and acceptance inputs, not governing instructions.

## Authorized Issue inventory and terminal mapping

No Issue outside this table belongs to this programme.

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
| #1124 | HIGH | Liquid20 current-session authorization | COMPLETE | `archive/FTAI-20260803-portal-remediation-1124.md` | #1146 |
| #1126 | HIGH | AI/Learning permissions | COMPLETE_PENDING_MERGE | `archive/FTAI-20260803-portal-remediation-1126.md` | #1149 |
| #1127 | HIGH | Canonical secret classification | ACTIVE | `active/FTAI-20260803-portal-remediation-1127.md` | pending |
| #1128 | MEDIUM | OIDC flow quotas/cleanup | QUEUED | pending | pending |
| #1129 | MEDIUM | Bounded semantic fields | QUEUED | pending | pending |
| #1130 | MEDIUM | OIDC response/algorithm/rotation bounds | QUEUED | pending | pending |
| #1132 | MEDIUM | Back-channel logout replay protection | QUEUED | pending | pending |
| #1134 | MEDIUM | Tenant workload budgets | QUEUED | pending | pending |
| #1135 | MEDIUM | Identity key rotation | QUEUED | pending | pending |
| #1136 | MEDIUM | Clock-skew/monotonic evidence | QUEUED | pending | pending |
| #1137 | MEDIUM | Atomic OIDC state claim | READY_AFTER_1127 | pending | pending |
| #1139 | HIGH | Backup/restore/DR | QUEUED | pending | pending |
| #1140 | MEDIUM | Accessibility/responsive acceptance | QUEUED | pending | pending |
| #1142 | MEDIUM | Session touch write amplification | QUEUED | pending | pending |

Inventory count: `50`.

## Dependency graph

### S0 — immediate security containment

1. `#1124` Liquid20 authoritative session boundary — complete through PR `#1146`.
2. `#1126` explicit AI/Learning service permissions — implementation, product-head validation, fresh audit and archive complete in PR `#1149`; exact closeout-head merge gate remains.
3. `#1127` canonical secret classification — active sole producer on non-overlapping paths; branch must incorporate the exact post-`#1149` `develop` before its PR opens.
4. Identity hardening sequence: `#1137` atomic state claim → `#1132` logout replay → `#1130` OIDC bounds/rotation → `#1128` flow quotas/cleanup → `#1135` identity key rotation. `#1122` owns any shared production migration work.

### F1 — shared foundations

- `#1122` migration/schema/dialect authority.
- `#1109` generated transport schemas and canonical error envelope.
- `#1108` trusted correlation/causation propagation; `#1110` consumes `#1108` and `#1109` for the sole bounded BFF transport.
- `#1115` inbound limits and `#1129` bounded semantic fields feed generated contracts.
- `#1111` canonical audit writer/projection.
- `#1112` event taxonomy, transactional outbox, publisher and inbox/poison substrate.
- `#1113` durable idempotency/replay/CAS authority.
- `#1134` workload limiter/admission authority; `#1142` consumes its evidence and `#1122` dialect decisions.
- `#1107` consumes pagination contracts, migration indexes and retention/workload rules.

### R2 — trusted runtime composition

- `#1100` sole credential broker.
- `#1092` authoritative runtime read/reconciliation; `#1093` valuation and `#1094` observability consume it.
- `#1086` PI-08 consumes credential, audit, event, idempotency, kill-switch and runtime foundations.
- `#1091` command activation consumes `#1100`, `#1086` and `#1092`.
- `#1099` desired-state activation consumes outbox, provisioning, command and reconciliation paths.
- `#1120` owns kill-switch hierarchy/contracts across every exposure path.
- `#1136` establishes source-time integrity for runtime, valuation and freshness claims.

### P3 — product vertical slices

- `#1090`, `#1095`, `#1096`, `#1097` consume migration, audit, outbox and idempotency foundations; `#1097` also consumes `#1100`.
- `#1085` consumes generated contracts and authoritative strategy persistence.
- `#1102` consumes `#1126`, `#1112`, `#1111`, `#1108` and runtime evidence.
- `#1104` consumes event/audit/idempotency foundations; external channel proof may later be one exact WAITING boundary.
- `#1103`, `#1117`, `#1118`, `#1121` form the administration/capability/tenant/session UI sequence.
- `#1119` consumes bounded reads, source-time policy, events and API-mode runtime.
- `#1123` consumes the canonical error and bounded transport contracts.
- `#1087` requires an explicit owner-approved language policy; never guess it.
- `#1140` is the full-product accessibility/responsive acceptance wave after principal UI contracts stabilize.

### D4 — deployment and closeout

- `#1089` owns authenticated production/staging API-mode composition.
- `#1098` owns the disposable real API-mode browser harness and downstream journey gate.
- `#1114` and `#1116` validate browser and exact-image supply-chain boundaries.
- `#1139` implements repository-owned backup/restore tooling after `#1122`; protected isolated restore remains separately authorized.
- `#1101` reconciles documentation only from terminal evidence.
- Final independent audit runs on exact final `develop` after all repository work is merged.

## Sole shared-contract producers

| Mechanism | Producer Issue | Exclusive authority |
|---|---|---|
| Production migrations/schema | #1122 | migration files, schema readiness and dialect tooling |
| Generated schemas/errors | #1109 | OpenAPI/schema generator, generated TS contracts, common envelope |
| Correlation propagation | #1108 | trusted request/context/event propagation |
| BFF control-plane transport | #1110 | one server-only bounded transport module |
| Canonical audit | #1111 | writer, store and read projection |
| Outbox/events/inbox | #1112 | taxonomy, transactional publisher, dedup/poison substrate |
| Idempotency/CAS | #1113 | mutation inventory, replay store and common CAS interfaces |
| Sensitive metadata classifier | #1127 | normalized aliases, cycle-safe traversal and adversarial corpus |
| Credential broker | #1100 | PI-07 composition and narrow consumer interfaces |
| Workload limiter | #1134 | route/action budgets and admission interfaces |
| Runtime composition root | #1089 | authenticated deployment/provider wiring |
| API-mode browser harness | #1098 | disposable real control-plane/browser evidence profile |

Consumers may edit exclusive paths but cannot create competing authorities. Every child task records ownership before mutation and releases it at terminal closeout.

## Current state and barriers

```yaml
completed:
  - audit PR #1082 merged at ba4173e975b6ae40c8b0266e3c15cb1b19a0755d
  - programme PR #1145 merged at 0a82a5c93613a213989865bd9128ac7263227148
  - issue #1124 merged, closed and archived through PR #1146
  - issue #1126 implementation, product-head validation, fresh audit and archive complete in PR #1149
active:
  - coordinator task FTAI-20260803-portal-remediation-program
  - issue #1127 task FTAI-20260803-portal-remediation-1127
ready:
  - issue: 1137
    reason: next identity-hardening producer after immediate containment; dispatch only after #1127 ownership/checkpoint permits
waiting: []
blocked: []
closed_issues: 2
active_issues: 1
waiting_issues: 0
blocked_issues: 0
```

| Barrier | State | Exit evidence |
|---|---|---|
| Audit baseline | COMPLETE | PR #1082 merged |
| Programme initialization | COMPLETE | PR #1145 merged |
| Immediate security containment | ACTIVE | #1124 complete; #1126 closing; #1127 active |
| Shared foundations | NOT_STARTED | producer PRs terminal with no competing contracts |
| Runtime composition | NOT_STARTED | canonical dry-run runtime/providers fail closed |
| Product vertical slices | NOT_STARTED | issue-specific real API-mode journeys and restart evidence |
| Deployment package | NOT_STARTED | exact API-mode images, migrations, security and supply-chain gates |
| Protected target acceptance | EXTERNAL_BOUNDARY | separately authorized protected checks only |
| Final independent audit | NOT_STARTED | zero material findings on exact final develop |

## Protected-target boundary

Repository-safe dry-run/staging validation and existing trusted Synology runners are authorized. These remain separate: irreversible production deployment; protected credential/Vault/identity-key mutation; live trading, withdrawals or capital; owner-managed Cloudflare/Authentik/Vault/private-runtime acceptance; destructive restore against a protected environment. A task may enter `WAITING` only after all repository-owned work is complete and one exact external authority/resource is named.

## Terminal completion criteria

The programme is terminal only when all 50 Issues are truthfully terminal; all repository-owned remediation is merged; canonical deployment is authenticated API mode without fixture fallback; representative browser-to-BFF-to-control-plane-to-persistence/provider journeys pass; backend session/tenant/capability/CSRF/MFA rules are authoritative; migrations, concurrency, idempotency, audit, events and recovery are restart-safe; exact images pass security/SBOM/provenance/runtime checks; accessibility and backup/isolated restore acceptance are complete; fresh final audit has no material finding; all PRs/tasks are terminal; and every ownership/lease is released with all safety flags false.

## Programme next action

Merge PR `#1149` after required checks pass on its exact closeout head, verify Issue `#1126` is terminal, then incorporate that exact `develop` head into `fix/portal-1127-sensitive-data-classifier` and continue the already claimed canonical classifier task.
