# Platform Continuous Assurance Coverage Ledger

```yaml
programme_id: FTAI-20260805-platform-continuous-assurance
repository: blakinio/freqtrade
status: active
started_at: 2026-08-05T14:34:00Z
baseline_develop_head: 108eff8149f3c5dba77bfcdeaea0c63c8a22b551
last_completed_wave: wave-003-required-ci-bounds-and-terminal-delivery
active_wave: wave-004-focused-core-ci-contract-repair
open_findings:
  - 1250
  - 1257
  - 1265
resolved_findings:
  - 1254
active_repairs:
  - 1258
  - 1271
active_delivery:
  - 1215
  - 1273
completed_delivery:
  - 1217
  - 1259
terminal_duplicates:
  - 1266
  - 1267
  - 1268
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Status vocabulary

- `NOT_REVIEWED` — no fresh bounded assurance wave is recorded.
- `ACTIVE` — a bounded wave is in progress.
- `FINDING_OPEN` — a material finding has a durable open Issue.
- `REPAIR_ACTIVE` — a deduplicated repair PR has exact-head validation in progress.
- `RESOLVED_WITH_EVIDENCE` — the finding reached a verified terminal state.
- `CLEAR_WITHIN_SCOPE` — no material gap was found inside the exact recorded scope; this is not an exhaustive platform claim.
- `WAITING` — an explicit external or exact-head condition is pending and no worker should poll continuously.

## Domain coverage

| Domain | Status | Last exact head | Evidence | Next exact action |
|---|---|---|---|---|
| Governance and durable coordination | FINDING_OPEN | `108eff8149f3c5dba77bfcdeaea0c63c8a22b551` | Issue #1250; checkpoint PRs #1253/#1256/#1259/#1273 | Portal owner reconciles stale #1122/#1132 state; finish #1273 exact-head checks |
| Security and identity | NOT_REVIEWED | — | owned product work remains separate | select an unowned identity boundary after current delivery becomes terminal |
| Correctness and data integrity | CLEAR_WITHIN_SCOPE | `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4` | PR #1217 exact-head matrix and merge | no further mypy 2.1 action in this wave |
| Reliability, recovery and deployment | RESOLVED_WITH_EVIDENCE | `74d1ba5ca603d7b116a36f966592fac7f49cee08` | Issue #1254 closed after fresh heartbeat, connected sources and acceptable disk capacity | review on the next material operations change |
| Performance and resource bounds | REPAIR_ACTIVE | `5a487222573d2eadd2e3746e5e15bb06128455eb` | Issue #1257 / PR #1258; prior exact-head green, current-base checks queued | finish fresh current-base required CI and protected merge |
| Frontend product quality and accessibility | NOT_REVIEWED | — | active Portal ownership remains separate | inspect after active ownership releases |
| Strategy, signal and research quality | NOT_REVIEWED | — | active WickHunter ownership remains separate | inspect reproducibility and leakage after ownership releases |
| Dependencies, CI and documentation drift | REPAIR_ACTIVE | `3ff2b1ded28617175ab29dfa1f4b9977f6fa5fdd` | Issue #1265 / PR #1271; PR #1215 failure log | finish exact-head repair, then revalidate PR #1215 |

## Wave history

### Wave 001 — governance and durable-state consistency

- Finding `#1250` recorded stale Portal remediation coordinator state.
- PR `#1253` merged as `37e12c1e7b118196543f23c5626959d870012748`.

### Wave 002 — PR terminality and operational blocker

- PRs `#1217` and `#1215` were ordered and updated without force-push.
- Finding `#1254` recorded unavailable trusted runner state.
- PR `#1256` merged as `8093f546eddf567b4d775a1cfa664fd8384d67f3`.

### Wave 003 — required CI bounds and terminal delivery

- PR `#1217` merged as `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4` after exact-head CI.
- Finding `#1257` proved the online compatibility lane lacked job and item timeout bounds.
- Checkpoint PR `#1259` merged as `74d1ba5ca603d7b116a36f966592fac7f49cee08`.
- Issue `#1254` later closed after structured recovery evidence.

### Wave 004 — focused-core CI dependency contract

- PR `#1215` run `31019942269`, job `92354598878`, passed compile, Ruff and mypy but failed before collection with `ModuleNotFoundError: No module named 'xdist'`.
- The `core-light` job ran `pytest -n auto` while omitting `pytest-xdist` from its bounded dependency installation.
- Issue `#1265` is the canonical P1/high-risk finding.
- Issues `#1266`, `#1267` and `#1268` are closed intentional duplicates and contain no unique work.
- PR `#1271` is the deduplicated two-path repair on exact head `3ff2b1ded28617175ab29dfa1f4b9977f6fa5fdd` and current `develop@108eff8149f3c5dba77bfcdeaea0c63c8a22b551`.
- Independent diff inspection found the pinned `pytest-xdist==3.8.0` install and a regression contract coupling it to `pytest -n auto`; no material finding remains against the diff.
- A parallel worker already owned the repair branch. The coordinator respected live ownership and did not overwrite it.
- Security validation for PR `#1271` passed; Freqtrade and risk-aware workflows remain queued after two aggregate observations.
- PR `#1258` was merged forward without force-push from exact head `4351c01fa5ae1d04773062f95ee5909c892a7b4b` to `5a487222573d2eadd2e3746e5e15bb06128455eb` on current `develop`. Prior exact-head workflows were green; fresh current-base workflows `31023854278`, `31023855036` and `31023854101` are queued.
- The current-base merge for PR `#1258` was constructed from the verified current `develop` tree and overlaid only its two audited paths after proving intervening changes were disjoint.
- Runtime E2E is `NOT_APPLICABLE`: the internal CI workflow is the real system boundary and exact-head CI must execute the repaired lanes.
- Checkpoint PR `#1273` records the wave and recovery boundary.

## Selection policy

After each terminal wave, select in this order:

1. unowned P0/P1 or equivalent high safety finding;
2. unresolved operational blocker;
3. overdue evidence after material merges;
4. widest unreviewed high-risk domain;
5. lower-risk hygiene and drift.

Before creating a task, branch, Issue or PR, search live ownership and related work. Existing work is resumed or linked. Duplicates are terminally reconciled.

## Next exact action

Observe terminal aggregate states without resetting counters. Enable protected auto-merge only after every required check passes for PRs `#1271` and `#1258`. After PR `#1271` merges, update PR `#1215` to the repaired `develop` baseline without force-push and run fresh exact-head CI. Merge checkpoint PR `#1273` only after its final documentation/governance checks pass.
