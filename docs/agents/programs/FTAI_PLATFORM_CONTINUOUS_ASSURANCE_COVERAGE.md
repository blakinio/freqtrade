# Platform Continuous Assurance Coverage Ledger

```yaml
programme_id: FTAI-20260805-platform-continuous-assurance
repository: blakinio/freqtrade
status: active
started_at: 2026-08-05T14:34:00Z
baseline_develop_head: 35ee3e5672c1773a10f80f09e2d7c2b23bc21d95
last_completed_wave: wave-004-ci-governance-and-coordinator-terminality
active_wave: wave-005-terminal-reconciliation-and-current-base-gates
open_findings: []
active_repairs:
  - 1284
active_delivery:
  - 1215
completed_delivery:
  - 1217
  - 1253
  - 1256
  - 1258
  - 1259
  - 1270
  - 1271
  - 1275
  - 1255
  - 1261
  - 1283
  - 1288
  - 1292
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
- `WAITING_CURRENT_BASE` — content is audited but must be merged forward and validated on current `develop`.
- `UNKNOWN_REQUIRED_GATE` — a required gate failed and its exact root cause is not yet proven.
- `RESOLVED_WITH_EVIDENCE` — the finding and delivery lifecycle are terminal with exact-head evidence.
- `CLEAR_WITHIN_SCOPE` — no material gap was found inside the exact recorded scope; this is not an exhaustive platform claim.

## Domain coverage

| Domain | Status | Last exact head | Evidence | Next exact action |
|---|---|---|---|---|
| Governance and durable coordination | RESOLVED_WITH_EVIDENCE | `35ee3e5672c1773a10f80f09e2d7c2b23bc21d95` | Issues #1250/#1251/#1252/#1264/#1272; PRs #1275/#1255/#1261/#1270/#1292 | keep the ledger aligned with live terminal state |
| Security and identity | UNKNOWN_REQUIRED_GATE | `d63f6073d413c2a5dce6735c4be3fbecc4318068` | Issue #1132 / PR #1284; risk-aware and zizmor pass; Freqtrade CI run 31078169298 fails Python 3.14 | inspect the exact failing output, preserve owner scope and complete independent final audit after repair |
| Correctness and data integrity | CLEAR_WITHIN_SCOPE | `3efa46ae7d953ca38c83a7bca27537680fed94d5` | Issue #1282 / PR #1283 repaired the optional XGBoost import boundary | re-audit after material identity/schema integration |
| Reliability, recovery and deployment | NOT_REVIEWED | — | active operations and WickHunter work remain separately owned | select the next unowned bounded deployment/recovery journey after current gates |
| Performance and resource bounds | RESOLVED_WITH_EVIDENCE | `3b1ae6271405d87dc616070ea617c63bd62c1e21` | Issue #1257 / PR #1258 exact-head bounded online CI | retain regression contract; no further action in this wave |
| Architecture, CI and workflow lifecycle | RESOLVED_WITH_EVIDENCE | `35ee3e5672c1773a10f80f09e2d7c2b23bc21d95` | PRs #1255/#1261/#1270/#1288/#1292 | review only after material architecture or workflow changes |
| Contribution forms and Projects metadata | WAITING_CURRENT_BASE | `132ad4ba37b766ea641bbd17f84178d4acaea48d` | PR #1215; three paths clear; prior external test defect resolved by #1283 | merge-forward to current develop preserving three blobs and run fresh focused-core CI |
| Frontend product quality and accessibility | NOT_REVIEWED | — | active Portal ownership remains separate | audit an unowned user journey after identity ownership becomes terminal |
| Strategy, signal and research quality | NOT_REVIEWED | — | active WickHunter ownership remains separate | audit reproducibility and leakage boundaries after active ownership releases |

## Wave history

### Wave 001 — governance and durable-state consistency

- Issue `#1250` recorded stale Portal coordination.
- PR `#1253` merged as `37e12c1e7b118196543f23c5626959d870012748`.

### Wave 002 — pull-request terminality and operational blocker

- PRs `#1217` and `#1215` were ordered.
- Issue `#1254` recorded unavailable trusted-runner evidence.
- PR `#1256` merged as `8093f546eddf567b4d775a1cfa664fd8384d67f3`.

### Wave 003 — required CI bounds and terminal delivery

- PR `#1217` merged as `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4`.
- Issue `#1257` / PR `#1258` added bounded online CI and merged as `3b1ae6271405d87dc616070ea617c63bd62c1e21`.
- PR `#1259` merged as `74d1ba5ca603d7b116a36f966592fac7f49cee08`.
- Issue `#1254` later closed after structured runner recovery.

### Wave 004 — CI, architecture and repository governance

- Issue `#1265` / PR `#1271` repaired focused-core xdist and merged as `29aa61d97472cd3ef4cdcb85171bf55b7d168ed9`.
- Issue `#1250` / PR `#1275` reconciled Portal coordination and merged as `8ee4f6b2527b7bffb7d6967adb3c0f1abd1be56b`.
- Issue `#1251` / PR `#1255` established architecture authority and merged as `7fe304c098aa69b523ec33cf37909a20d5953df0`.
- Issue `#1252` / PR `#1261` established workflow lifecycle governance and merged as `c4e9a94a84e86e9ad6b26f9b14fb11d2e9de7ac4`.
- Issue `#1264` / PR `#1270` established repository policy and merged as `f595d633fd09d4df58b391e28e979d29d1436d1a`.
- Issue `#1282` / PR `#1283` repaired optional XGBoost isolation and merged as `3efa46ae7d953ca38c83a7bca27537680fed94d5`.
- Issue `#1272` completed GitHub-native security controls; PR `#1292` merged as current `develop@35ee3e5672c1773a10f80f09e2d7c2b23bc21d95`.

### Wave 005 — terminal reconciliation and current-base gates

- Reconstructed live `develop`, open PR state, exact heads and required CI outcomes.
- Classified PR `#1215` as content-clear but waiting for current-base validation after merged dependency repair `#1283`.
- Classified Issue `#1132` / PR `#1284` as actively owned with a failed required Python 3.14 lane; no duplicate finding or implementation task was created.
- Superseded stale, merge-conflicted checkpoint PR `#1273` with a new current-base ledger update.
- No new atomic material finding was created in this bounded wave.

## Selection policy

After each terminal wave, select the next area in this order:

1. unowned P0/P1 or equivalent critical/high safety finding;
2. unresolved required gate or operational blocker;
3. overdue area whose evidence predates material merges;
4. widest unreviewed high-risk domain;
5. lower-risk hygiene and drift.

Before creating any task, branch, Issue or PR, search current GitHub durable state and active ownership. Existing work is resumed or linked; duplicates are prohibited.

## Next exact action

Merge-forward PR `#1215` to current `develop` while preserving exactly its three owned files and require a fresh focused-core pass. In parallel, inspect the Python 3.14 failure in PR `#1284` run `31078169298`, then complete its independent exact-head audit without taking implementation ownership.
