---
task_id: FTAI-20260812-portal-runtime-supervisor-1355
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: blocked
task_kind: implementation
priority: critical
repository: blakinio/freqtrade
base_branch: develop
branch: codex/portal-runtime-supervisor-1355
related_pr: 1496
issue: 1355
created: 2026-08-12
updated: 2026-08-13
live_capital_authorized: false
production_deployment_authorized: false
---

# Runtime Supervisor producer

## Result

Issue #1355 implements the ADR-020 generation-bound Runtime Supervisor over the merged #1354 runtime-isolation driver. The delivery remains PAPER-only and grants no LIVE, production-deployment, exchange-credential, order, withdrawal, or live-capital authority.

The implementation now includes strict lifecycle-only requests, exact generation/digest/version fencing, durable command replay fingerprints, durable independent active-generation fencing, fail-closed PAPER and retirement authorization, restart-safe lifecycle reconstruction, immutable ownership checks before runtime/network mutation, bounded machine-readable driver failure classes, finite host/engine command deadlines, and a protected host-local UDS boundary with `SO_PEERCRED`, bounded framing/concurrency/shutdown and fixed `/run/quant-platform` ancestor validation.

The ordinary `FreqtradeExecutionAdapter` no longer accepts raw runtime-driver lifecycle authority. Provision/start/pause/stop and runtime inspection cross the narrow Supervisor client boundary only. Restart-observed RUNNING/PAUSED/CREATED/STARTING states are not accepted from liveness alone: exact current-generation evidence is required or the runtime is reconstructed fail-closed. Pause/stop/retire use immutable ownership verification before mutating an existing runtime.

The last material test-only repair replaced socket-inode polling in the hung-worker shutdown regression with the server's listener-ready event, removing the verified bind-before-listen race.

## Current checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
phase: validate
execution_mode: chat_github
head_before_checkpoint: 182abeabb37768d5d1bd44365c1a103554e6ba21
branch: codex/portal-runtime-supervisor-1355
pr: 1496
status: blocked
owned_paths:
  - ai_platform/portal/runtime_supervisor/**
  - ai_platform/portal/execution/driver.py
  - ai_platform/portal/execution/runtime.py
  - ai_platform/portal/execution/host_isolation.py
  - tests/ai_platform/portal/runtime_supervisor/**
  - tests/ai_platform/portal/execution/**
  - .github/workflows/portal-runtime-isolation-e2e.yml
  - tools/portal_audit/ledger/**
  - docs/agents/tasks/active/FTAI-20260812-portal-runtime-supervisor-1355.md
open_material_findings: []
unresolved_review_threads: 0
proven:
  - strict lifecycle-only generation-bound request surface rejects caller-controlled raw engine parameters
  - ordinary execution adapter retains no raw RuntimeDriver lifecycle capability and routes lifecycle/inspection through RuntimeSupervisorClient
  - exact identity/version/digest fencing, independent active-generation authorities, and replay conflict protection are fail closed
  - retryable engine failures preserve durable command fingerprints without permanently caching retryable outcomes
  - PAPER authorization gates exposure-creating provision/run while authenticated containment stays available; retirement is separately authorized
  - RUNNING reconciliation re-attests; restart-observed CREATED/STARTING/PAUSED/STOPPED states reconstruct safely when exact current-generation evidence is absent
  - immutable ownership is verified before pause, stop, retire, container deletion and network deletion
  - bounded driver reason codes preserve machine-readable failure classes without exception text
  - UDS uses SO_PEERCRED, bounded one-line framing, request deadlines, bounded workers/inflight admission, listener-ready signalling and bounded fail-closed shutdown
  - production UDS root is fixed at /run/quant-platform and every existing ancestor is lstat-validated before bind
  - ordinary concrete subprocess-backed Docker/nftables/Btrfs operations have a finite 30-second default command deadline
  - command/bot keyed lock registries preserve serialization without retaining historical keys
  - all known PR #1496 review threads are resolved after direct current-code verification and the listener-readiness repair
pre_checkpoint_exact_head_ci:
  head: 182abeabb37768d5d1bd44365c1a103554e6ba21
  success:
    - CodeQL Security Analysis
    - GitHub Actions Security Analysis with zizmor
    - Portal API Mode Browser
    - Portal WickHunter Browser E2E
    - Portal Runtime Isolation E2E
    - Portal Exact-Image Supply Chain
  pending_at_last_observation:
    - Risk-aware component CI
    - Freqtrade CI
unknown:
  - fresh independent audit result on the exact final candidate head
  - final all-required-CI result on the checkpoint commit created by this record update
  - final current-develop synchronization decision/evidence before merge
conflicts: []
blockers:
  - A genuinely fresh independent validator is mandatory before terminal completion. Existing automated reviews are historical and do not cover the current candidate head.
  - Repository policy forbids consuming owner-funded Codex/OpenAI/paid-AI quota without separate explicit authorization, and no permitted local/free separate validator is exposed in the current environment.
next_action: Use a permitted genuinely fresh separate validator on the exact final candidate. If it reports zero material findings, verify every required CI/E2E check on that exact head, reconcile current develop/base freshness as required, then merge PR #1496 without bypass and perform terminal task/archive/ownership cleanup.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 6
  phase: validate
  exact_product_head_before_checkpoint: 182abeabb37768d5d1bd44365c1a103554e6ba21
  pull_request: 1496
  active_operation: fresh independent exact-head audit and final exact-head CI
  status: blocked
  safe_to_resume: true
  resume_condition: PR #1496 remains open on the same branch and no new material finding is unresolved
  next_action: Obtain one permitted genuinely fresh independent audit; do not invoke owner-funded Codex/OpenAI/paid AI without separate explicit authorization.
```
