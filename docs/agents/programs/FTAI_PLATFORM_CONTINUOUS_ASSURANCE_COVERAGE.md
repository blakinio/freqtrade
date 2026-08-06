# Platform Continuous Assurance Coverage Ledger

```yaml
programme_id: FTAI-20260805-platform-continuous-assurance
repository: blakinio/freqtrade
status: active
started_at: 2026-08-05T14:34:00Z
baseline_develop_head: 3a3320646709991b2ef513a81d4a2b457ef155dc
last_completed_wave: wave-005-terminal-reconciliation-and-current-base-gates
active_wave: wave-006-open-pr-terminality-and-dependency-safety
open_findings:
  - 1294
active_repairs:
  - 1284
  - 1291
active_delivery:
  - 1215
  - 1276
  - 1290
completed_delivery:
  - 1217
  - 1253
  - 1255
  - 1256
  - 1258
  - 1259
  - 1261
  - 1270
  - 1271
  - 1275
  - 1283
  - 1288
  - 1292
  - 1293
superseded_checkpoints:
  - 1273
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Status vocabulary

- `NOT_REVIEWED` — no fresh bounded assurance wave is recorded.
- `ACTIVE` — bounded work or exact-head validation is in progress under an existing owner.
- `FINDING_OPEN` — a material finding has durable Issue ownership.
- `CI_MERGE_READY` — the exact changed scope and required checks are green; normal ownership and branch protection remain authoritative.
- `WAITING_CURRENT_BASE` — content is audited but must be merged forward and validated on current `develop`.
- `WAITING_PROSPECTIVE_ACCEPTANCE` — an evidence window or independent acceptance boundary has not yet completed.
- `UNKNOWN_REQUIRED_GATE` — a required gate failed and its exact root cause is not yet proven.
- `RESOLVED_WITH_EVIDENCE` — finding and delivery lifecycle are terminal with exact-head evidence.
- `CLEAR_WITHIN_SCOPE` — no material gap was found inside the exact recorded scope; this is not an exhaustive platform claim.

## Domain coverage

| Domain | Status | Last exact head | Evidence | Next exact action |
|---|---|---|---|---|
| Governance and durable coordination | RESOLVED_WITH_EVIDENCE | `3a3320646709991b2ef513a81d4a2b457ef155dc` | Issues #1250/#1251/#1252/#1264/#1272; PRs #1275/#1255/#1261/#1270/#1292/#1293 | keep the ledger aligned with live terminal state |
| Security and identity | UNKNOWN_REQUIRED_GATE | `d63f6073d413c2a5dce6735c4be3fbecc4318068` | Issue #1132 / PR #1284; risk/security lanes pass; Freqtrade CI run 31078169298 fails Python 3.14 | inspect exact failing output, preserve owner scope and finish independent final audit after repair |
| Dependency and supply-chain safety | FINDING_OPEN | `ae8231e30cd6f2619d4b2b13d340299a86e69a4b` | Issue #1294 / PR #1291; install failure blocks cryptography 50.0.0; exact cause unknown | repair dependency installation, classify CVE applicability and pass complete exact-head matrix |
| Dependency routine updates | CI_MERGE_READY | `3411e37b609ef056147d614a65423dcdb1e5e05d` | PR #1290; one-line aiohttp update; Freqtrade/risk-aware/CodeQL/zizmor pass | merge through normal dependency ownership and branch protection |
| Correctness and data integrity | CLEAR_WITHIN_SCOPE | `3efa46ae7d953ca38c83a7bca27537680fed94d5` | Issue #1282 / PR #1283 repaired optional XGBoost isolation | re-audit after material identity/schema integration |
| Reliability, recovery and deployment | WAITING_PROSPECTIVE_ACCEPTANCE | `b8cf23b2a833edac9214303574116d31cc44a197` | PR #1276; WH-09 PAPER deployment/restart evidence; window ends 2026-08-06T17:45:07.561Z | collect independent terminal acceptance after the window; do not claim early completion |
| Performance and resource bounds | RESOLVED_WITH_EVIDENCE | `3b1ae6271405d87dc616070ea617c63bd62c1e21` | Issue #1257 / PR #1258 exact-head bounded online CI | retain regression contract |
| Architecture, CI and workflow lifecycle | RESOLVED_WITH_EVIDENCE | `3a3320646709991b2ef513a81d4a2b457ef155dc` | PRs #1255/#1261/#1270/#1288/#1292/#1293 | review after material architecture or workflow changes |
| Contribution forms and Projects metadata | WAITING_CURRENT_BASE | `132ad4ba37b766ea641bbd17f84178d4acaea48d` | PR #1215; three paths clear; external defect resolved by #1283 | merge-forward preserving three blobs and run fresh focused-core CI |
| Frontend product quality and accessibility | NOT_REVIEWED | — | active Portal ownership remains separate | audit an unowned user journey after identity ownership becomes terminal |
| Strategy, signal and research quality | NOT_REVIEWED | — | active WickHunter ownership remains separate | audit reproducibility and leakage boundaries after active ownership releases |

## Wave history

### Waves 001–004

- Governance, task-state, trusted-runner, CI bounds, focused-core dependency, Portal coordinator, architecture authority, workflow lifecycle and repository policy findings were created, repaired and terminally merged.
- Exact terminal evidence is retained in the active task and earlier checkpoint PRs `#1253`, `#1256` and `#1259`.

### Wave 005 — terminal reconciliation and current-base gates

- Reconstructed live `develop`, terminalized stale Wave 004 outcomes and closed superseded PR `#1273`.
- Classified PR `#1215` as content-clear but waiting for current-base validation.
- Classified Issue `#1132` / PR `#1284` as actively owned with failed required Python 3.14 CI.
- PR `#1293` passed exact-head gates and merged as `3a3320646709991b2ef513a81d4a2b457ef155dc`.

### Wave 006 — open-PR terminality and dependency safety

- Inspected every remaining open non-checkpoint PR: `#1215`, `#1276`, `#1284`, `#1290`, `#1291`.
- PR `#1290` is one-path, exact-head green and labeled `ci:merge-ready`; no material finding.
- PR `#1276` is truthfully waiting for the prospective WH-09 acceptance window and cannot complete before `2026-08-06T17:45:07.561Z`.
- PR `#1215` remains waiting for current-base merge-forward; PR `#1284` remains blocked by an unknown Python 3.14 gate failure.
- Finding `#1294` records the cryptography 50.0.0 security-update installation failure, exact unknown root cause, required CVE applicability classification and repair acceptance criteria.
- No duplicate implementation branch or repair PR was created.

## Finding queue

| Issue | Priority | Risk | Owner state | Evidence | Required result |
|---|---|---|---|---|---|
| #1294 | P1 | medium | `agent:ready` | PR #1291; Freqtrade CI run 31089481871 fails installation before tests | exact failure/root cause, compatible cryptography 50 delivery, CVE applicability classification, full exact-head gates |

## Selection policy

After each terminal wave, select the next area in this order:

1. unowned P0/P1 or equivalent critical/high safety finding;
2. unresolved required gate or operational blocker;
3. overdue area whose evidence predates material merges;
4. widest unreviewed high-risk domain;
5. lower-risk hygiene and drift.

Before creating any task, branch, Issue or PR, search current GitHub durable state and active ownership. Existing work is resumed or linked; duplicates are prohibited.

## Next exact action

Dispatch Issue `#1294` to the repair lane. Preserve existing ownership for PRs `#1215`, `#1276` and `#1284`. After any exact head or terminal state changes, reconstruct the complete open-PR inventory and then select the widest unowned high-risk product domain.
