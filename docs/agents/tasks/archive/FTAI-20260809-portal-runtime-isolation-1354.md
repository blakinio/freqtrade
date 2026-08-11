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
- exact digest-pinned hardened runtime image;
- non-root UID/GID, no-new-privileges, capability-drop-all, default seccomp and read-only root;
- hard memory/swap/PID/CPU, tmpfs and bounded local-log limits;
- bounded durable state under an approved Btrfs state root;
- generation-scoped deny-by-default network isolation with explicit public market-data allow rules;
- structural and effective pre-release attestation plus quarantine release gating;
- real Docker E2E and negative isolation tests;
- fail-closed behavior when required host enforcement is unavailable.

No Runtime Supervisor authority from #1355 is implemented here.

## Fresh repair/audit findings

The combined repair/audit pass found and remediated four material defects before closeout:

1. stale Ruff/noqa formatting in the real-Docker E2E;
2. missing workflow-registry tracking for the new E2E workflow;
3. `runtime_user` rejected root UID but allowed root GID (`1000:0`); both UID and GID zero are now rejected with regression coverage;
4. Btrfs storage validation allowed the approved state root itself to be converted/replaced; runtime state must now be a child path, with a no-host-command regression test.

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
    journey: Portal Runtime Isolation E2E using real DockerCliRuntimeDriver, exact image, quarantine, bounded writable state and denied public egress fixture
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

## Safety boundary

PAPER remains the only authorized operational mode. No private exchange credentials, real-order submission, withdrawals, protected production deployment, LIVE/live-capital authority, or host-firewall mutation is authorized or introduced by this closeout.
