---
task_id: FTAI-20260809-portal-runtime-isolation-1354
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: implementing
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

Issue `#1354` remains open and PR `#1464` remains the sole delivery PR. This task is **implementing**, not completed. Exact-head CI and the privileged runtime-isolation E2E passed on `745a53fc72b11c250efb8c1796a7b04d8ea8c400`, but fresh audit opened two material closeout findings that must be repaired before merge: unconditional workflow cleanup may remove a recorded nftables table when its Docker network removal failed, and the host-controlled readiness probe has no driver-owned subprocess deadline.

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

Material findings repaired in the branch include stale formatting/type failures, missing workflow registry normalization, root UID/GID guardrails, approved-state-root protection, pre-release re-attestation, approved DNS enforcement, canonical nftables comparison, immutable quarantine bootstrap, concrete Linux isolation E2E, effective log-rotation evidence, real Btrfs quota overrun evidence, paused-runtime stale-release handling, Btrfs runtime owner/mode enforcement, qgroup header parsing, state-owner E2E, explicit nftables cleanup, STARTING stop semantics, durable RUNNING log re-attestation, host-controlled application readiness after a successful pairlist probe, forged-stdout rejection, and real privileged memory/swap, PID and CPU-throttling probes.

These repairs are candidate evidence only until the final unchanged head earns all required gates.

## Remaining closeout gates

```yaml
closeout:
  implementation_candidate_present: true
  implementation_complete: false
  outcome_verified: false
  audit:
    result: remediation_required
    material_findings_open: 2
  e2e:
    result: passed_on_pre_repair_head_745a53fc72b11c250efb8c1796a7b04d8ea8c400
  final_ci:
    result: passed_on_pre_repair_head_745a53fc72b11c250efb8c1796a7b04d8ea8c400
  pull_requests:
    sole_delivery_pr: blakinio/freqtrade#1464
    historical_delivery_pr: blakinio/freqtrade#1431 closed-unmerged
  task_status: implementing
  task_archived: false
  ownership_released: false
```

## Required next actions

1. repair fail-closed nftables cleanup so a table remains whenever its corresponding Docker network teardown fails;
2. add a driver-owned finite deadline to the host-controlled readiness subprocess and fail closed on timeout;
3. run focused validation, then the dedicated privileged E2E and affected exact-head CI;
4. obtain a fresh independent exact-head audit and remediate every remaining material finding;
5. verify zero unresolved review threads and squash-merge PR `#1464` only after all closeout gates are green;
6. perform terminal lifecycle/archive reconciliation after the merge is verified.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-12T06:36:00Z
head: 745a53fc72b11c250efb8c1796a7b04d8ea8c400
head_role: pre_final_audit_repair_candidate
branch: fix/portal-runtime-isolation-1354
pr: 1464
status: implementing
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
  - exact-head 745a53fc72b11c250efb8c1796a7b04d8ea8c400 passed Portal Runtime Isolation E2E, Freqtrade CI, CodeQL, Exact-Image, risk-aware, zizmor and browser E2E checks
  - source-independent readiness no longer trusts strategy stdout
  - STARTING runtimes are stopped on request
  - active RUNNING re-attestation uses bounded current Docker logs rather than bootstrap markers
  - host isolation cleanup removes Docker network before deleting its nftables table
  - privileged E2E contains real memory/swap, PID and CPU-throttling negative probes
unknown:
  - post-repair exact-head CI and privileged E2E result
  - fresh post-repair independent audit result
conflicts: []
material_findings:
  - id: PRRT_kwDOTdDTU86YZdA9
    severity: P1
    summary: unconditional workflow cleanup deletes task nftables tables even when Docker network removal fails
  - id: PRRT_kwDOTdDTU86YZdBB
    severity: P2
    summary: readiness docker-exec subprocess is not bounded by a driver-owned timeout
changed_paths:
  - docs/agents/tasks/active/FTAI-20260809-portal-runtime-isolation-1354.md
validation:
  - head: 745a53fc72b11c250efb8c1796a7b04d8ea8c400
    result: PASS_WITH_AUDIT_FINDINGS
    evidence: all required workflows green; two current review findings remain
blockers: []
next_action: Implement the two current audit repairs with focused validation, then remove any temporary validation workflow before exact-head E2E and CI.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: chat-20260812-0836-paper-closeout-1354
  session_started_at: 2026-08-12T06:36:00Z
  checkpointed_at: 2026-08-12T06:36:00Z
  last_progress_at: 2026-08-12T06:36:00Z
  phase: implement_final_audit_repairs
  exact_head: 745a53fc72b11c250efb8c1796a7b04d8ea8c400
  pull_request: 1464
  active_operation: prepare bounded repair and focused validation
  external_run_ids: []
  operation_started_at: null
  wait_deadline_at: null
  check_generation: null
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: branch remains the sole delivery lane and no conflicting writer owns PR #1464
  next_action: Repair fail-closed nftables cleanup and bound the readiness subprocess, then run focused validation.
```
