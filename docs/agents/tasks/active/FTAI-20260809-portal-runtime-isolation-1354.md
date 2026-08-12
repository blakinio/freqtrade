---
task_id: FTAI-20260809-portal-runtime-isolation-1354
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: validating
task_kind: implementation
priority: high
repository: blakinio/freqtrade
base_branch: develop
branch: fix/portal-runtime-isolation-1354
related_pr: 1464
issue: 1354
created: 2026-08-09
updated: 2026-08-12
live_capital_authorized: false
production_deployment_authorized: false
host_firewall_mutation_authorized: false
---

# Portal runtime isolation and resource boundaries

## Current truth

Issue `#1354` remains open and PR `#1464` remains the sole delivery PR. The implementation is frozen for final validation after repairing the two material findings from the previous audit. Current `develop@ec41d2542bff57f74cd10856b7dc22265213d991` is an ancestor of the feature branch through integration commit `ac00dbaaa384c78cef90a14e16aba28a1479f815`; compare reports `behind_by=0`. Integration PR `#1486` is terminal and its changes are represented by that integration commit.

PAPER remains the only authorized operational mode. LIVE/live-capital authority, private exchange credentials, real-order submission, withdrawals, protected production deployment and target-host firewall mutation are not authorized by this task.

## Implemented candidate scope

The delivery candidate provides the ADR-020 generation-bound isolation envelope for Portal-managed PAPER/dry-run Freqtrade runtimes, including immutable plan binding, digest-pinned hardened runtime image and quarantine bootstrap, non-root/no-new-privileges/cap-drop/read-only-root enforcement, hard memory/swap/PID/CPU/tmpfs/log/state bounds, Btrfs qgroups and state ownership attestation, deny-by-default generation networking with explicit public-data/DNS policy, pre-release and active re-attestation, fail-closed paused/reprovision lifecycle, host-controlled application readiness, and real privileged Docker/nftables/Btrfs acceptance coverage.

No Runtime Supervisor authority from `#1355` is implemented here.

## Final audit repairs

The previous exact-head audit findings are repaired in the code parent `ac00dbaaa384c78cef90a14e16aba28a1479f815`:

- `PRRT_kwDOTdDTU86YZdA9` — unconditional workflow cleanup now retains the exact nftables table whenever the corresponding Docker network teardown fails or cannot be proven; cleanup still returns failure and verifies residual state instead of stripping the firewall from a surviving network/runtime.
- `PRRT_kwDOTdDTU86YZdBB` — the host-controlled readiness `docker exec` uses a driver-owned 15-second deadline; `SubprocessCommandRunner` converts `TimeoutExpired` to a bounded failed probe and `inspect()` remains `STARTING` rather than blocking lifecycle control indefinitely.

The readiness repair was focused-validated before publication with `test_driver.py`, Ruff, formatting, mypy and `git diff --check`. The temporary publisher workflow was removed before this final-validation candidate.

## Remaining closeout gates

```yaml
closeout:
  implementation_candidate_present: true
  implementation_complete: true
  outcome_verified: false
  audit:
    result: pending_fresh_exact_head
    material_findings_open: unknown_until_fresh_audit
  e2e:
    result: pending_exact_final_head
  final_ci:
    result: pending_exact_final_head
  pull_requests:
    sole_delivery_pr: blakinio/freqtrade#1464
    current_base_sync_pr: blakinio/freqtrade#1486 terminal
    historical_delivery_pr: blakinio/freqtrade#1431 closed-unmerged
  task_status: validating
  task_archived: false
  ownership_released: false
```

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-12T06:57:00Z
head: ac00dbaaa384c78cef90a14e16aba28a1479f815
head_role: final_code_parent_before_metadata_freeze
branch: fix/portal-runtime-isolation-1354
pr: 1464
status: validating
context_routes:
  - issue #1354
  - pull request #1464
  - docs/ai_platform/portal/RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md
owned_paths:
  - ai_platform/portal/execution/driver.py
  - tests/ai_platform/portal/execution/test_driver.py
  - .github/workflows/portal-runtime-isolation-e2e.yml
  - docs/agents/tasks/active/FTAI-20260809-portal-runtime-isolation-1354.md
proven:
  - current develop ec41d2542bff57f74cd10856b7dc22265213d991 is an ancestor of the delivery branch and compare is behind_by=0
  - previous exact head 745a53fc72b11c250efb8c1796a7b04d8ea8c400 passed Runtime Isolation E2E and all applicable major CI before the final two audit repairs
  - unconditional workflow cleanup no longer deletes a task nftables table when corresponding network teardown failed or is unproven
  - application readiness remains host-controlled and now has a driver-owned finite subprocess deadline
  - STARTING runtimes are stoppable; active RUNNING re-attestation uses bounded current Docker-log evidence
  - privileged E2E contains memory/swap, PID, CPU, storage, networking, ownership and release-path negative/positive probes
unknown:
  - fresh independent audit result on the final metadata head
  - exact-final-head privileged E2E and CI result
  - unresolved review-thread count after final audit reconciliation
conflicts: []
blockers: []
next_action: Resolve the final PR head produced by this metadata commit, request a fresh independent exact-head audit, run/reconcile exact-head E2E and CI, resolve all review threads, and squash-merge PR #1464 only if every closeout gate passes.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: chat-20260812-0836-paper-closeout-1354
  session_started_at: 2026-08-12T06:36:00Z
  checkpointed_at: 2026-08-12T06:57:00Z
  last_progress_at: 2026-08-12T06:57:00Z
  phase: final_exact_head_validation
  exact_head: ac00dbaaa384c78cef90a14e16aba28a1479f815
  pull_request: 1464
  active_operation: fresh independent audit plus exact-head CI/E2E
  external_run_ids: []
  operation_started_at: 2026-08-12T06:57:00Z
  wait_deadline_at: 2026-08-12T07:42:00Z
  check_generation: final-closeout-v1
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: PR #1464 head remains unchanged and no conflicting writer owns the branch
  next_action: Request fresh independent audit on the exact metadata head and reconcile exact-head required CI/E2E before review-thread cleanup and merge.
```
