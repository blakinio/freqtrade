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
updated: 2026-08-11
live_capital_authorized: false
production_deployment_authorized: false
host_firewall_mutation_authorized: false
---

# Portal runtime isolation and resource boundaries

## Current truth

Issue `#1354` remains open and PR `#1464` remains the sole delivery PR. This task is **validating**, not completed. The final five exact-head audit repairs have been published to the existing branch and the temporary publication workflow has been removed. Fresh independent audit, exact-final-head CI/E2E, review-thread cleanup, merge, and post-merge terminal lifecycle reconciliation are still required.

PAPER remains the only authorized operational mode. LIVE/live-capital authority, private exchange credentials, real-order submission, withdrawals, protected production deployment and target-host firewall mutation are not authorized by this task.

## Implemented candidate scope

The current delivery candidate provides the ADR-020 generation-bound isolation envelope for Portal-managed PAPER/dry-run Freqtrade runtimes, including:

- immutable isolation profile and resolved-plan binding;
- digest-pinned hardened runtime image and quarantine bootstrap;
- non-root UID/GID, no-new-privileges, capability-drop-all, default seccomp and read-only root;
- hard memory/swap/PID/CPU, tmpfs, local-log and durable-state bounds;
- Btrfs qgroup enforcement and exact runtime-state owner/mode attestation;
- generation-scoped deny-by-default networking with explicit public market-data and DNS policy;
- structural/effective nftables attestation before release;
- fail-closed paused-runtime handling requiring reprovisioning before release;
- real Docker plus concrete Linux nftables/Btrfs E2E, including non-root state writeability;
- unconditional task-owned Docker/Btrfs/nftables cleanup with post-cleanup verification.

No Runtime Supervisor authority from `#1355` is implemented here.

## Repair/audit findings addressed in the candidate

Material findings repaired in the branch include stale formatting/type failures, missing workflow registry normalization, root UID/GID guardrails, approved-state-root protection, pre-release re-attestation, approved DNS enforcement, canonical nftables comparison, immutable quarantine bootstrap, concrete Linux isolation E2E, effective log-rotation evidence, real Btrfs quota overrun evidence, paused-runtime stale-release handling, Btrfs runtime owner/mode enforcement, qgroup header parsing, state-owner E2E, explicit nftables cleanup, STARTING stop semantics, durable RUNNING log re-attestation, application-level readiness after initial pairlist refresh, and real privileged memory/swap, PID and CPU-throttling probes.

These repairs are candidate evidence only until the final unchanged head earns all required gates.

## Remaining closeout gates

```yaml
closeout:
  implementation_candidate_present: true
  implementation_complete: false
  outcome_verified: false
  audit:
    result: pending
    material_findings_open: unknown_until_fresh_audit
  e2e:
    result: pending_exact_final_head
  final_ci:
    result: pending_exact_final_head
  pull_requests:
    sole_delivery_pr: blakinio/freqtrade#1464
    historical_delivery_pr: blakinio/freqtrade#1431 closed-unmerged
  task_status: validating
  task_archived: false
  ownership_released: false
```

## Required next actions

1. obtain a fresh independent audit of the exact current PR head and remediate every material finding;
2. run the dedicated real Docker/Linux isolation E2E and all applicable required CI on that unchanged final head;
3. verify zero unresolved material review threads;
4. squash-merge PR `#1464` only after all closeout gates are proven on the exact final head;
5. perform terminal lifecycle/archive reconciliation only after the merge is verified.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T21:06:00Z
head: 92beceffe51b9270cedc001ce09c5b1b0eec0825
head_role: published_code_and_temporary_workflow_cleanup_parent
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
  - tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py
  - .github/workflows/portal-runtime-isolation-e2e.yml
  - docs/agents/tasks/active/FTAI-20260809-portal-runtime-isolation-1354.md
proven:
  - paused runtimes cannot use docker unpause and exact in-session generations have a fresh reprovision path
  - release requires independently re-hashed read-only Gateway artifact and versioned contract evidence
  - integrated Linux E2E invokes driver.start, runs a successful Freqtrade list-pairs public-data operation and checks sustained running
  - exact nftables table identifiers are persisted before network creation for unconditional cleanup
  - STARTING runtimes are stopped on request instead of continuing after lifecycle cancellation
  - ongoing RUNNING attestation uses durable local-log backend usage evidence after bootstrap markers rotate
  - immutable quarantine readiness is emitted only after Freqtrade completes its initial pairlist refresh
  - privileged E2E contains real memory/swap, PID and CPU-throttling negative probes
  - FTAI-ARCH-RUNTIME-ISOLATION remains open in ARCHITECTURE_REGISTRY.yaml
  - focused execution suite passed with 142 tests and 6 privileged-environment skips
derived:
  - this checkpoint commit is metadata-only; fresh audit and CI must target the actual PR head returned by GitHub after this commit
unknown:
  - exact-head GitHub CI and privileged Linux E2E result
  - unresolved review-thread state after publication
conflicts: []
first_failure:
  marker: privileged_linux_e2e_not_available_locally
  evidence: six environment-gated tests skipped because the local repair checkout lacks the dedicated privileged Btrfs/nftables runner fixture
rejected_hypotheses:
  - isolation-plan Gateway digest labels alone are sufficient artifact evidence
changed_paths:
  - ai_platform/portal/execution/driver.py
  - tests/ai_platform/portal/execution/test_driver.py
  - tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py
  - tests/ai_platform/portal/execution/test_runtime_image.py
  - ai_platform/portal/execution/runtime_image/portal-runtime-quarantine
  - .github/workflows/portal-runtime-isolation-e2e.yml
  - docs/agents/tasks/active/FTAI-20260809-portal-runtime-isolation-1354.md
validation:
  - command: python -m pytest -q -o addopts='' --confcutdir=tests/ai_platform tests/ai_platform/portal/execution
    result: PASS
    evidence: 142 passed and 6 privileged-environment tests skipped
  - command: python -m mypy ai_platform/portal/execution/driver.py tests/ai_platform/portal/execution/test_linux_isolation_backend_e2e.py
    result: PASS
    evidence: no issues found
  - command: python -m ruff check changed Python paths
    result: PASS
    evidence: all checks passed
  - command: git apply --check exact Codex diff from PR comment 5258787558
    result: PASS
    evidence: temporary bounded publisher applied the exact diff and completed successfully
blockers: []
next_action: Resolve the current PR head from GitHub, run fresh independent audit plus privileged Linux E2E and required CI on that exact unchanged SHA, remediate any material finding, then merge only if all closeout gates are green.
```
