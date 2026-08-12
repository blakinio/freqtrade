---
task_id: FTAI-20260812-portal-runtime-supervisor-1355
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: implementing
task_kind: implementation
priority: critical
repository: blakinio/freqtrade
base_branch: develop
branch: codex/portal-runtime-supervisor-1355
related_pr: 1496
issue: 1355
created: 2026-08-12
updated: 2026-08-12
live_capital_authorized: false
production_deployment_authorized: false
---

# Runtime Supervisor producer

## Result

Issue #1355 implements the ADR-020 generation-bound Runtime Supervisor over the merged #1354 runtime-isolation driver. The delivery remains PAPER-only and has no LIVE, production-deployment, exchange-credential, order, withdrawal, or live-capital authority.

The exact clean candidate `d01ad8de3b877da345fd30f140f794a44d2c7147` passed real Runtime Isolation E2E, CodeQL, zizmor, exact-image and browser validation, but the fresh independent review on that exact SHA opened three remaining material findings. Merge is blocked until they are repaired and a new exact final head passes fresh audit, E2E, required CI and review hygiene.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-12T14:20:00Z
phase: implement
execution_mode: chat_github
context_pressure: medium
context_growth: stable
decomposition_decision: phased
head_before_checkpoint: d7c61024785f306d3c7368f3e41fbd13eddd1f8e
branch: codex/portal-runtime-supervisor-1355
pr: 1496
status: implementing
owned_paths:
  - ai_platform/portal/runtime_supervisor/**
  - ai_platform/portal/execution/driver.py
  - tests/ai_platform/portal/runtime_supervisor/**
  - tests/ai_platform/portal/execution/test_driver.py
  - docs/agents/tasks/active/FTAI-20260812-portal-runtime-supervisor-1355.md
open_material_findings:
  - id: PRRT_kwDOTdDTU86YloWR
    severity: P1
    summary: lifecycle execution is synchronous in the sole UDS accept loop
  - id: PRRT_kwDOTdDTU86YloWV
    severity: P1
    summary: reconstruction can stop a reused foreign runtime before ownership verification
  - id: PRRT_kwDOTdDTU86YloWY
    severity: P2
    summary: historical command_id locks grow without bound
proven:
  - generation-bound request surface rejects raw engine authority
  - PAPER authorization is mandatory for exposure-creating operations while containment remains available
  - journal and trusted-provider active-generation authorities are checked independently
  - running reconciliation invokes driver re-attestation
  - restart-observed CREATED/STARTING generations are reconstructed fail closed
  - retirement deletion verifies immutable runtime/network ownership
  - bounded machine-readable driver failure reason codes are preserved without exception text
  - final clean pre-repair head d01ad8de passed Portal Runtime Isolation E2E 31601775079
  - final clean pre-repair head d01ad8de passed CodeQL 31601775095 and zizmor 31601775140
  - final clean pre-repair head d01ad8de passed Portal Exact-Image 31601775104, API Browser 31601775166 and WickHunter Browser E2E 31601775106
unknown:
  - focused validation result for the three new audit repairs
  - fresh post-repair audit result
  - exact-head final CI result after repair
conflicts: []
repair_cycles_for_current_gate: 0
identical_failure_retries: 0
ci_checks_for_current_head: 0
unchanged_state_checks: 0
blockers: []
next_action: Run the bounded GitHub Actions repair workflow to apply and validate the three exact fresh-audit findings, then inspect only its first actionable failure or resulting repair head.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: chat-github-20260812-1617
  session_started_at: 2026-08-12T14:17:00Z
  checkpointed_at: 2026-08-12T14:20:00Z
  last_progress_at: 2026-08-12T14:20:00Z
  phase: implement
  exact_head: d7c61024785f306d3c7368f3e41fbd13eddd1f8e
  pull_request: 1496
  active_operation: prepare bounded repair workflow
  external_run_ids: []
  operation_started_at: null
  wait_deadline_at: null
  check_generation: final-audit-repair-1
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: branch still owns PR #1496 and the three review findings remain open
  next_action: Create and trigger the one-shot final-audit repair workflow against the checkpointed branch head.
```
