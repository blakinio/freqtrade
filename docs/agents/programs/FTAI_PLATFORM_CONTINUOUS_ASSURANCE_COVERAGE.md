# Platform Continuous Assurance Coverage Ledger

```yaml
programme_id: FTAI-20260805-platform-continuous-assurance
repository: blakinio/freqtrade
status: active
started_at: 2026-08-05T14:34:00Z
baseline_develop_head: 8093f546eddf567b4d775a1cfa664fd8384d67f3
last_completed_wave: wave-002-pr-terminality-and-operational-blockers
active_wave: wave-003-required-ci-bounds-and-terminal-delivery
open_findings:
  - 1250
  - 1254
  - 1257
active_repairs:
  - 1217
  - 1258
waiting_revalidation:
  - 1215
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
| Governance and durable coordination | FINDING_OPEN | `8093f546eddf567b4d775a1cfa664fd8384d67f3` | Issue #1250; PRs #1253/#1256 | owning Portal lane reconciles stale #1122/#1132 state and adds deterministic consistency validation |
| Security and identity | NOT_REVIEWED | — | existing owned product Issues remain separate | select the highest-risk unowned identity boundary after current terminal checks |
| Correctness and data integrity | ACTIVE | `50a42194caafb6d15a1aef652cf67ab0bc1acd5f` | PR #1217 exact-head matrix | merge #1217 only after required CI Gate succeeds |
| Reliability, recovery and deployment | FINDING_OPEN | `8093f546eddf567b4d775a1cfa664fd8384d67f3` | Issue #1254 | restore trusted `freqtrade-staging` runner and obtain a structured health result |
| Performance and resource bounds | REPAIR_ACTIVE | `b24a0f6406680396a703289962b8fb2717ba5681` | Issue #1257 / PR #1258 | finish exact-head workflow and risk-aware validation; auto-merge only on full success |
| Frontend product quality and accessibility | NOT_REVIEWED | — | active owned Portal work remains separate | inspect current Portal state after existing owners become terminal |
| Strategy, signal and research quality | NOT_REVIEWED | — | active WickHunter work remains separate | inspect reproducibility and leakage boundaries after ownership releases |
| Dependencies, CI, documentation and operations drift | ACTIVE | `8093f546eddf567b4d775a1cfa664fd8384d67f3` | PRs #1217/#1215/#1258; Issues #1254/#1257 | complete #1217, update #1215 to new develop and rerun, complete #1258, preserve runner blocker |

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

- Baseline: `8093f546eddf567b4d775a1cfa664fd8384d67f3`.
- PR `#1217` current exact head `50a42194caafb6d15a1aef652cf67ab0bc1acd5f`: online lane and every completed job are green; Python 3.12 coverage remains active; auto-merge is enabled.
- PR `#1215` must wait for `#1217`, then receive the latest `develop` by a non-force merge commit and rerun exact-head CI.
- Finding `#1257`: required `online-tests` had neither a job-level timeout nor an explicit pytest item timeout.
- Repair PR `#1258` adds a 30-minute job bound, a 300-second per-item bound and a fail-closed contract test. The limits are based on four successful 14m05s–15m46s job samples and an observed approximately 158-second slowest test item. Exact-head full and risk-aware CI are active; auto-merge is enabled.
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

Allow branch protection to finish PRs `#1217` and `#1258`. After `#1217` merges, update `#1215` to the latest `develop` without force-push and rerun exact-head CI. Preserve Issue `#1254` until a trusted runner returns a structured health result. Then checkpoint terminal outcomes and select the next unowned high-risk wave.
