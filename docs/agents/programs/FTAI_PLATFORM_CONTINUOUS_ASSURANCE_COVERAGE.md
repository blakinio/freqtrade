# Platform Continuous Assurance Coverage Ledger

```yaml
programme_id: FTAI-20260805-platform-continuous-assurance
repository: blakinio/freqtrade
status: active
started_at: 2026-08-05T14:34:00Z
baseline_develop_head: 5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4
last_completed_wave: wave-002-pr-terminality-and-operational-blockers
active_wave: wave-003-required-ci-bounds-and-terminal-delivery
open_findings:
  - 1250
  - 1254
  - 1257
active_repairs:
  - 1258
active_delivery:
  - 1215
  - 1259
completed_delivery:
  - 1217
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Status vocabulary

- `NOT_REVIEWED` — no fresh bounded assurance wave is recorded.
- `ACTIVE` — a bounded wave is in progress.
- `FINDING_OPEN` — a material finding has a durable open Issue.
- `REPAIR_ACTIVE` — a deduplicated implementation PR has exact-head validation in progress.
- `CLEAR_WITHIN_SCOPE` — no material gap was found inside the exact recorded scope; this is not an exhaustive platform claim.
- `WAITING` — repository-owned work is complete or blocked by an explicit dependency or external authority.

## Domain coverage

| Domain | Status | Last exact head | Evidence | Next exact action |
|---|---|---|---|---|
| Governance and durable coordination | FINDING_OPEN | `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4` | Issue #1250; PRs #1253/#1256/#1259 | owning Portal lane reconciles stale #1122/#1132 state; finish checkpoint #1259 exact-head CI |
| Security and identity | NOT_REVIEWED | — | existing owned product Issues remain separate | select highest-risk unowned identity boundary after current terminal checks |
| Correctness and data integrity | CLEAR_WITHIN_SCOPE | `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4` | PR #1217 merged after exact-head matrix | no further mypy 2.1 baseline action in this wave |
| Reliability, recovery and deployment | FINDING_OPEN | `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4` | Issue #1254 | restore trusted `freqtrade-staging` runner and obtain structured health result |
| Performance and resource bounds | REPAIR_ACTIVE | `4351c01fa5ae1d04773062f95ee5909c892a7b4b` | Issue #1257 / PR #1258 | finish current-base Freqtrade, risk-aware and security CI; auto-merge only on full success |
| Frontend product quality and accessibility | NOT_REVIEWED | — | active owned Portal work remains separate | inspect current Portal state after existing owners become terminal |
| Strategy, signal and research quality | NOT_REVIEWED | — | active WickHunter work remains separate | inspect reproducibility and leakage boundaries after ownership releases |
| Dependencies, CI, documentation and operations drift | ACTIVE | `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4` | PR #1217 merged; PRs #1215/#1258/#1259 active; Issues #1254/#1257 | finish exact-head delivery while preserving runner blocker |

## Wave history

### Wave 001 — governance and durable-state consistency

- Baseline: `cbf9f57ea8d5783f85d19fe0f8557dfe3178705a`.
- Finding: Issue `#1250` for stale Portal remediation coordinator state.
- Terminal delivery: PR `#1253` merged as `37e12c1e7b118196543f23c5626959d870012748`.

### Wave 002 — pull-request terminality and operational blockers

- Baseline: `37e12c1e7b118196543f23c5626959d870012748`.
- PRs `#1217` and `#1215` were updated without force-push and their dependency ordering was proven.
- Finding: Issue `#1254` for unavailable trusted `freqtrade-staging` runner; component health remains unverified rather than proven failed.
- Terminal delivery: PR `#1256` merged as `8093f546eddf567b4d775a1cfa664fd8384d67f3`.

### Wave 003 — required CI bounds and terminal delivery

- Baseline advanced to `5dadfe32c7cc2ba7af95652b06c4e0624d2f11b4` after PR `#1217` passed exact-head CI and auto-merged.
- PR `#1215` is updated without force-push to exact head `d4cd9e0a512c12abee9ef5c2482c570aba50e8fc`; security analysis passed, required Freqtrade and risk-aware CI are queued, and auto-merge is enabled.
- Finding `#1257`: required `online-tests` had neither a job-level timeout nor an explicit pytest item timeout.
- Repair PR `#1258` adds a 30-minute job bound, a 300-second per-item bound and a fail-closed contract test. The limits are based on four successful 14m05s–15m46s job samples and an observed approximately 158-second slowest item.
- PR `#1258` is updated without force-push to exact head `4351c01fa5ae1d04773062f95ee5909c892a7b4b`; fresh Freqtrade, risk-aware and security CI are queued, and auto-merge is enabled.
- Checkpoint PR `#1259` is reconciled to the post-`#1217` baseline and must pass exact-head CI.
- Issue `#1254` remains externally blocked with job `92339899025` queued and `runner_id=0`.
- No force-push, gate bypass, test weakening, credential change, protected deployment, trading action, withdrawal or live-capital mutation occurred.

## Selection policy

After each terminal wave, select the next area in this order:

1. unowned P0/P1 or equivalent critical/high safety finding;
2. unresolved operational blocker;
3. overdue area whose evidence predates material merges;
4. widest unreviewed high-risk domain;
5. lower-risk hygiene and drift.

Before creating any task, branch, Issue or PR, search current GitHub durable state and active ownership. Existing work is resumed or linked; duplicates are prohibited.

## Next exact action

Allow branch protection to finish PRs `#1215` and `#1258`. Validate and merge checkpoint PR `#1259` only after its reconciled exact head passes required CI. Preserve Issue `#1254` until a trusted runner returns a structured health result. Then checkpoint terminal outcomes and select the next unowned high-risk wave.
