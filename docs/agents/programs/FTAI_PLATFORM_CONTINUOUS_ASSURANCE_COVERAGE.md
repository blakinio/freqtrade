# Platform Continuous Assurance Coverage Ledger

```yaml
programme_id: FTAI-20260805-platform-continuous-assurance
repository: blakinio/freqtrade
status: active
started_at: 2026-08-05T14:34:00Z
baseline_develop_head: 3b1ae6271405d87dc616070ea617c63bd62c1e21
last_completed_wave: wave-003-required-ci-bounds-and-terminal-delivery
active_wave: wave-004-ci-governance-and-coordinator-terminality
open_findings:
  - 1250
  - 1251
  - 1252
  - 1264
  - 1265
resolved_findings:
  - 1254
  - 1257
active_repairs:
  - 1271
  - 1275
active_delivery:
  - 1215
  - 1255
  - 1261
  - 1270
  - 1273
completed_delivery:
  - 1217
  - 1258
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
- `ACTIVE` — bounded work is in progress.
- `FINDING_OPEN` — a material finding has durable ownership or an open Issue.
- `REPAIR_ACTIVE` — a deduplicated repair is being validated.
- `SAFETY_BLOCKED` — merge is intentionally prevented until an exact material finding is removed.
- `RESOLVED_WITH_EVIDENCE` — a finding reached a verified terminal state.
- `CLEAR_WITHIN_SCOPE` — no material gap was found inside the recorded scope; this is not an exhaustive platform claim.
- `WAITING` — an explicit external/exact-head condition is pending and should not be continuously polled.

## Domain coverage

| Domain | Status | Last exact head | Evidence | Next exact action |
|---|---|---|---|---|
| Governance and durable coordination | REPAIR_ACTIVE | `7893f7f41e81e25cd0485d8c24c1bc4839e2161d` | Issue #1250 / PR #1275; PR #1273 | finish fresh current-base #1275; dispatch #1132 only after merge |
| Security and identity | FINDING_OPEN | `7893f7f41e81e25cd0485d8c24c1bc4839e2161d` | #1132 READY only in PR #1275; #1137 protected-target waiting | after #1275 merge, deduplicate then create exactly one #1132 task/branch/PR |
| Correctness and data integrity | CLEAR_WITHIN_SCOPE | `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4` | PR #1217 exact-head matrix and merge | review after material core changes |
| Reliability, recovery and deployment | RESOLVED_WITH_EVIDENCE | `74d1ba5ca603d7b116a36f966592fac7f49cee08` | Issue #1254 closed after structured runner recovery | review on next material operations change |
| Performance and resource bounds | RESOLVED_WITH_EVIDENCE | `3b1ae6271405d87dc616070ea617c63bd62c1e21` | Issue #1257 / PR #1258 exact-head CI, bounded online test and merge | retain regression contract; no further wave action |
| Architecture authority | FINDING_OPEN | `f852092e20755b00f1cbc05c4d4df69599930859` | Issue #1251 / PR #1255 | reconcile exact base, terminal Issue mapping and task archive before merge |
| Workflow lifecycle governance | FINDING_OPEN | `db6e81febbdaaa8ee1a0719bb2892a34bef6fb72` | Issue #1252 / draft PR #1261 | correct live-catalog, all-open-PR ownership, metadata drift and task closeout; no further bulk retirement first |
| Repository contribution governance | FINDING_OPEN | `44ea3d5cd15c8dc6046cdd8526208bb0d1cdcdf6` | Issue #1264 / PR #1270 | add edited-title enforcement, satisfiable CODEOWNERS model and terminal task closeout |
| Dependencies and required CI | SAFETY_BLOCKED | `bb8ff2cf3909ba8b2bea3d32b6dff4bfab41484f` | Issue #1265 / draft PR #1271; PR #1215 | remove privileged helper, re-audit clean two-path head, merge, then revalidate #1215 |
| Frontend product quality and accessibility | NOT_REVIEWED | — | active Portal ownership remains separate | inspect after current identity/Portal ownership releases |
| Strategy, signal and research quality | NOT_REVIEWED | — | active WickHunter ownership remains separate | inspect after active WickHunter ownership releases |

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
- PR `#1259` merged as `74d1ba5ca603d7b116a36f966592fac7f49cee08`.
- Issue `#1254` later closed after structured recovery evidence.

### Wave 004 — CI, governance and coordinator terminality

- Issue `#1257` / PR `#1258` added a 30-minute online-job bound, 300-second per-item bound and fail-closed contract. Exact head passed full Freqtrade CI, actual online validation and risk-aware suites; merged as `3b1ae6271405d87dc616070ea617c63bd62c1e21`.
- Issue `#1265` proves `core-light` omitted `pytest-xdist` while invoking `pytest -n auto`.
- PR `#1271` has the intended two-path xdist repair, but exact head `bb8ff2cf3909ba8b2bea3d32b6dff4bfab41484f` also contains a non-self-removing PR-specific workflow with write permissions. It is draft/safety-blocked until cleanup and fresh exact-head validation.
- PR `#1215` form content, labels and the external Operations v3 native dependency reconciler were independently verified; it waits only for a clean xdist merge and fresh repaired-baseline CI.
- PR `#1275` reconciles completed `#1122`, READY `#1132` and waiting `#1137`, and adds a deterministic consistency test. It was merged forward without force-push to current `develop` at exact head `7893f7f41e81e25cd0485d8c24c1bc4839e2161d`.
- Fresh audits recorded terminality/enforcement gaps on PRs `#1255`, `#1261` and `#1270`. Existing owners retain those branches; findings were added to their PR discussions rather than duplicated.
- No further bulk workflow retirement is authorized until PR `#1261` corrects its open-PR ownership model and live-catalog verification.
- Runtime E2E is `NOT_APPLICABLE_WITH_REASON` for internal documentation/CI/governance contracts; exact-head workflows and durable-state outcomes are the applicable boundary.

## Selection policy

After each terminal bounded result, select in this order:

1. unowned P0/P1 or equivalent high safety finding;
2. unresolved operational blocker;
3. overdue evidence after material merges;
4. widest unreviewed high-risk domain;
5. lower-risk hygiene and drift.

Before creating a task, branch, Issue or PR, search live ownership and related work. Existing work is resumed or linked. Duplicates are terminally reconciled.

## Next exact action

Do not merge PR `#1271` while its privileged helper remains. Audit the cleaned exact head when the parallel owner removes it. Complete fresh current-base validation and protected merge for PR `#1275`; only then deduplicate and dispatch exactly one Issue `#1132` child task. After a clean `#1271` merge, merge-forward PR `#1215` without force-push and run fresh exact-head CI. Keep PRs `#1255`, `#1261` and `#1270` non-terminal until their recorded findings are repaired.
