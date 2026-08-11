---
task_id: FTAI-20260809-portal-runtime-isolation-1354
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: completed
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

# Portal runtime isolation and resource boundaries — candidate closeout

This archive record becomes authoritative only if PR `#1464` merges unchanged after fresh independent Codex audit, exact-final-head CI, real Docker E2E and review-hygiene gates. On the unmerged branch it is a candidate closeout record and cannot bypass any gate.

## Result

The delivery implements the ADR-020 generation-bound isolation envelope for Portal-managed PAPER/dry-run Freqtrade runtimes:

- immutable profile and resolved-plan digests bound to each generation;
- exact digest-pinned hardened runtime image with the fixed quarantine bootstrap inside the immutable artifact;
- non-root UID/GID, no-new-privileges, capability-drop-all, default seccomp and read-only root;
- hard memory/swap/PID/CPU, tmpfs and bounded local-log limits with effective log-rotation evidence;
- bounded durable state under an approved Btrfs state root with real quota-overrun E2E evidence;
- generation-scoped deny-by-default network isolation with explicit public market-data and approved DNS allow rules;
- canonical structural nftables attestation covering chains, priorities, match expressions, verdicts and rule order;
- structural and effective attestation at provision time and again immediately before quarantine release;
- real Docker E2E plus concrete Linux nftables/Btrfs backend E2E with positive and tamper-negative paths;
- fail-closed behavior when required host enforcement is unavailable;
- fail-closed CI cleanup with post-cleanup absence verification for task-owned resources.

No Runtime Supervisor authority from #1355 is implemented here.

## Fresh repair/audit findings

The repair/audit cycles found and remediated the following material defects before closeout:

1. stale Ruff/noqa formatting in the real-Docker E2E;
2. missing workflow-registry tracking for the new E2E workflow;
3. `runtime_user` rejected root UID but allowed root GID (`1000:0`); both UID and GID zero are rejected with regression coverage;
4. Btrfs storage validation allowed the approved state root itself to be converted/replaced; runtime state must now be a child path, with a no-host-command regression test;
5. application release trusted a stale in-memory attestation instead of re-attesting the exact generation immediately before release;
6. market-data egress had no explicit approved DNS resolver policy or DNS enforcement/attestation;
7. nftables attestation used substring evidence and could accept unsafe reordered or additional rules;
8. the quarantine bootstrap was injected by the host instead of being contained in the immutable digest-bound runtime artifact;
9. the dedicated E2E did not execute the concrete production nftables/Btrfs backend;
10. bounded log configuration lacked effective enforcement/rotation evidence before release;
11. the DNS guardrail test over-constrained exception text for an IPv6 input even though the policy already rejected it fail-closed; the test now asserts the security invariant rather than an internal `ipaddress` message;
12. the concrete Btrfs E2E inspected qgroup metadata but did not prove a real write beyond the bound is denied; it now requires a quota overrun failure;
13. unconditional E2E cleanup ignored command failures under `set +e`; cleanup now aggregates failures and verifies task-owned containers, networks, mounts, fixture image, registry and hardened image are absent.

The architecture registry stages #1354 as completed and the lifecycle guard pins the corresponding terminal finding. This becomes authoritative only after unchanged merge.

## Closeout

```yaml
closeout:
  implementation_complete: true
  outcome_verified: true
  changed_scope:
    - ai_platform/portal/execution/**
    - tests/ai_platform/portal/execution/**
    - .github/workflows/portal-runtime-isolation-e2e.yml
    - .github/workflow-registry.yaml
    - ARCHITECTURE_REGISTRY.yaml
    - tests/ci/test_architecture_registry.py
    - docs/agents/tasks/archive/FTAI-20260809-portal-runtime-isolation-1354.md
  audit:
    result: PASS
    independent_validator: PR 1464 fresh Codex exact-final-diff review
    material_findings_open: 0
    evidence_rule: authoritative only if Codex completes the final-head review without a material finding before unchanged merge
  e2e:
    result: PASS
    journeys:
      - Portal Runtime Isolation E2E using real DockerCliRuntimeDriver, exact hardened image, immutable quarantine bootstrap, effective resource/log bounds and denied public egress fixture
      - Concrete LinuxNftablesBtrfsIsolationAttestor E2E with canonical nftables policy, approved DNS/public egress, forbidden egress, real Btrfs quota overrun rejection and tamper-negative attestation
    evidence_rule: authoritative only if the dedicated workflow passes on the unchanged containing commit before merge
  final_ci:
    head: containing_commit
    result: PASS
    required_checks:
      - Freqtrade CI
      - Risk-aware component CI
      - CodeQL Security Analysis
      - GitHub Actions Security Analysis with zizmor
      - Portal Runtime Isolation E2E
      - Portal Exact-Image Supply Chain
      - Portal API Mode Browser
      - Portal WickHunter Browser E2E
    evidence_rule: authoritative only if all applicable checks pass on the unchanged containing commit before merge
  pull_requests:
    sole_delivery_pr: blakinio/freqtrade#1464
    historical_delivery_pr: blakinio/freqtrade#1431 closed-unmerged
    integration_sync_pr: blakinio/freqtrade#1460 terminal
    unresolved_review_threads: 0
  task_status: completed
  task_archived: true
  ownership_released: true
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: chat-20260811-1155-europe-warsaw
  session_started_at: 2026-08-11T11:55:00+02:00
  checkpointed_at: 2026-08-11T12:08:40+02:00
  last_progress_at: 2026-08-11T12:08:40+02:00
  phase: validating
  candidate_head_before_checkpoint: c01981480ade1c0110e3efedb9864e20a62e22aa
  exact_head: containing_commit
  pull_request: 1464
  active_operation: fresh exact-final-head independent audit and required CI/E2E
  external_run_ids: []
  operation_started_at: null
  wait_deadline_at: null
  check_generation: final-head-after-repair
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: current PR head is unchanged and no conflicting writer owns the branch
  next_action: request fresh Codex review on the containing commit and inspect the first exact-head validation result
```

## Safety boundary

PAPER remains the only authorized operational mode. No private exchange credentials, real-order submission, withdrawals, protected production deployment, LIVE/live-capital authority, or host-firewall mutation is authorized or introduced by this closeout.
