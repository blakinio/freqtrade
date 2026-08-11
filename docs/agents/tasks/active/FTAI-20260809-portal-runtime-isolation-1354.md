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

Issue `#1354` remains open and PR `#1464` remains the sole delivery PR. This task is **validating**, not completed: implementation repair has been applied, but current-base synchronization, fresh independent audit, exact-final-head CI/E2E, review-thread cleanup, merge, and post-merge terminal lifecycle reconciliation are still required.

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

Material findings already repaired in the branch include stale formatting/type failures, missing workflow registry normalization, root UID/GID guardrails, approved-state-root protection, pre-release re-attestation, approved DNS enforcement, canonical nftables comparison, immutable quarantine bootstrap, concrete Linux isolation E2E, effective log-rotation evidence, real Btrfs quota overrun evidence, paused-runtime stale-release handling, Btrfs runtime owner/mode enforcement, case-insensitive btrfs-progs qgroup header parsing, execution of the state-owner E2E and explicit nftables cleanup.

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

1. restore architecture-registry truth for `#1354` to non-terminal while the issue/PR are open;
2. synchronize the delivery branch with the current `develop` without force or history bypass;
3. obtain a fresh independent audit of the exact post-sync head and remediate every material finding;
4. run the dedicated real Docker/Linux isolation E2E and all applicable required CI on one unchanged final head;
5. verify zero unresolved material review threads;
6. squash-merge PR `#1464` only after all closeout gates are proven on the exact final head;
7. perform terminal lifecycle/archive reconciliation only after the merge is verified.
