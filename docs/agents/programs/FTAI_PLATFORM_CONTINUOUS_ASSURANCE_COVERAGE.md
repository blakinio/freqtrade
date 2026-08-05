# Platform Continuous Assurance Coverage Ledger

```yaml
programme_id: FTAI-20260805-platform-continuous-assurance
repository: blakinio/freqtrade
status: active
started_at: 2026-08-05T14:34:00Z
baseline_develop_head: 108eff8149f3c5dba77bfcdeaea0c63c8a22b551
last_completed_wave: wave-003-required-ci-bounds-and-terminal-delivery
active_wave: wave-004-focused-core-ci-and-coordinator-contract-repair
open_findings:
  - 1250
  - 1257
  - 1265
resolved_findings:
  - 1254
active_repairs:
  - 1258
  - 1271
  - 1275
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
| Governance and durable coordination | REPAIR_ACTIVE | `689bd511f0b34a8e0c3853eaffd04b722d43c753` | Issue #1250 / PR #1275; checkpoint PRs #1253/#1256/#1259/#1273 | finish exact-head PR #1275 and #1273 checks; dispatch #1132 only after #1275 merges |
| Security and identity | FINDING_OPEN | `689bd511f0b34a8e0c3853eaffd04b722d43c753` | stale #1122/#1132 dependency reconciled in PR #1275; #1137 remains protected-target waiting | after #1275 merge, create exactly one #1132 child task/branch/PR |
| Correctness and data integrity | CLEAR_WITHIN_SCOPE | `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4` | PR #1217 exact-head matrix and merge | no further mypy 2.1 action in this wave |
| Reliability, recovery and deployment | RESOLVED_WITH_EVIDENCE | `74d1ba5ca603d7b116a36f966592fac7f49cee08` | Issue #1254 closed after fresh heartbeat, connected sources and acceptable disk capacity | review on the next material operations change |
| Performance and resource bounds | REPAIR_ACTIVE | `5a487222573d2eadd2e3746e5e15bb06128455eb` | Issue #1257 / PR #1258; prior exact-head green, current-base security green | finish current-base Freqtrade/risk-aware CI and protected merge |
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

### Wave 004 — focused-core CI and coordinator contracts

- PR `#1215` run `31019942269`, job `92354598878`, passed compile, Ruff and mypy but failed before collection with `ModuleNotFoundError: No module named 'xdist'`.
- The `core-light` job ran `pytest -n auto` while omitting `pytest-xdist` from its bounded dependency installation.
- Issue `#1265` is the canonical P1/high-risk finding.
- Issues `#1266`, `#1267` and `#1268` are closed intentional duplicates and contain no unique work.
- PR `#1271` is the deduplicated two-path repair on exact head `3ff2b1ded28617175ab29dfa1f4b9977f6fa5fdd` and current `develop@108eff8149f3c5dba77bfcdeaea0c63c8a22b551`.
- Independent diff inspection found pinned `pytest-xdist==3.8.0` and a regression contract coupling it to `pytest -n auto`; no material finding or review thread remains.
- A parallel worker already owned the repair branch. The coordinator respected live ownership and did not overwrite it.
- Security, routing, pre-commit, documentation, online compatibility and all completed matrix jobs for PR `#1271` passed. Python 3.12 coverage remained active at the latest detailed snapshot. GitHub created replacement workflow generations on the same exact SHA after cancelling a superseded risk-aware run.
- PR `#1258` was merged forward without force-push from exact head `4351c01fa5ae1d04773062f95ee5909c892a7b4b` to `5a487222573d2eadd2e3746e5e15bb06128455eb` on current `develop`. Prior exact-head workflows were green; current-base security is green and other required workflows remain queued.
- The current-base merge for PR `#1258` was constructed from the verified current `develop` tree and overlaid only its two audited paths after proving intervening changes were disjoint.
- Issue `#1250` was independently revalidated against PR `#1159`, the archived `#1122` task, open Issue `#1132`, Issue `#1137` protected-target status and live PR/branch ownership.
- PR `#1275` reconciles `#1122` as COMPLETE and `#1132` as READY, corrects programme/coordinator counts and barriers, and adds a deterministic consistency test. Its final audited exact head is `689bd511f0b34a8e0c3853eaffd04b722d43c753`; changed paths are limited to two coordination records and one test, review threads are empty and fresh required CI is pending.
- During independent audit, unrelated execution metadata and programme detail removed during drafting were restored before the final head.
- Runtime E2E is `NOT_APPLICABLE`: these internal CI/governance workflows are the real system boundary and exact-head CI must execute their contracts.
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

Observe terminal aggregate states without resetting counters or continuous polling. Prioritize protected completion of PR `#1271`; after it merges, update PR `#1215` to the resulting `develop` baseline without force-push and run fresh exact-head CI. Complete current-base PR `#1258`, coordinator repair PR `#1275` and checkpoint PR `#1273` only after their exact-head required gates pass. Dispatch exactly one Issue `#1132` child task only after PR `#1275` merges.
