---
task_id: FTAI-20260812-portal-runtime-supervisor-1355
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: validating
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

The isolated producer implements the ADR-020 lifecycle-identity boundary: strict generation-bound
requests, optimistic version/ordinal preconditions, per-bot serialization, active-generation fencing,
global command replay protection, restart-safe SQLite idempotency evidence, bounded machine-readable
outcomes, and a local UDS transport authenticated with Linux peer credentials. Caller-controlled raw
engine parameters are absent from and rejected by the request schema. Existing `RuntimeDriver` and
trusted isolation material remain behind the Supervisor boundary.

The runtime-isolation dependency is merged and this branch is rebased onto current `develop`.
Supervisor integration now also implements explicit generation retirement and stopped-generation
reconstruction through the #1354 quarantine/attestation driver rather than attempting a forbidden
engine restart of stale in-memory release evidence.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-12T00:00:00Z
head: 1393d7daed17ab9fa0addc5f2e3845164fef06f1
head_role: supervisor_producer_candidate
branch: codex/portal-runtime-supervisor-1355
pr: 1496
status: validating
context_routes:
  - issue #1355
  - ADR-020
  - docs/ai_platform/portal/RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md
owned_paths:
  - ai_platform/portal/runtime_supervisor/**
  - tests/ai_platform/portal/runtime_supervisor/**
  - docs/agents/tasks/active/FTAI-20260812-portal-runtime-supervisor-1355.md
proven:
  - caller request schema contains lifecycle identity only and rejects raw engine fields
  - exact tenant, bot, generation, digest, ordinal and state-version binding fails closed
  - retired and conflicting active generations cannot provision or start
  - conflicting command replay is rejected and identical replay has no second side effect
  - SQLite command evidence survives Supervisor reconstruction
  - UDS boundary rejects unauthorized peer uid before request parsing
  - focused tests, Ruff, mypy and diff check pass
  - EnsureRetired removes only the exact stopped/paused generation and generation-scoped network
  - EnsureRunning reconstructs a stopped generation through retire, provision, attestation and release
  - two independent audit rounds produced eleven material findings and every finding was remediated
  - all eleven review threads are resolved; a fresh exact-head audit is pending
derived:
  - deployment composition remains coordinator work because this producer owns no deployment paths
unknown:
  - real Linux UDS peer-credential E2E on the final exact head
  - real Docker Supervisor plus #1354 quarantine/attestation lifecycle E2E
  - final post-remediation independent audit and exact-head GitHub CI
conflicts: []
first_failure:
  marker: linux_and_docker_e2e_unavailable_on_native_windows
  evidence: local host cannot prove Linux SO_PEERCRED or the privileged isolation backend
rejected_hypotheses:
  - the dispatch dependency state was current
changed_paths:
  - ai_platform/portal/runtime_supervisor/**
  - ai_platform/portal/execution/driver.py
  - ai_platform/portal/execution/runtime.py
  - tests/ai_platform/portal/runtime_supervisor/**
  - docs/agents/tasks/active/FTAI-20260812-portal-runtime-supervisor-1355.md
validation:
  - command: python -m pytest -q -o addopts='' --confcutdir=tests/ai_platform tests/ai_platform/portal/runtime_supervisor
    result: PASS
    evidence: 22 passed
  - command: python -m ruff check ai_platform/portal/runtime_supervisor tests/ai_platform/portal/runtime_supervisor
    result: PASS
    evidence: all checks passed
  - command: python -m mypy ai_platform/portal/runtime_supervisor tests/ai_platform/portal/runtime_supervisor
    result: PASS
    evidence: no issues found in 6 source files
  - command: git diff --check
    result: PASS
    evidence: no whitespace errors
  - command: python -m pytest -q -o addopts='' --confcutdir=tests/ai_platform tests/ai_platform/portal/runtime_supervisor tests/ai_platform/portal/execution/test_driver.py
    result: PASS
    evidence: 61 passed after all audit remediation and Linux peer credential test
  - command: Portal Runtime Isolation E2E
    result: NOT_RUN
    evidence: exact-head run 31593372866 pending; scenario enters through RuntimeSupervisor and proves real Docker provision, stop and retire
blockers: []
next_action: Inspect the fresh audit requested for 1393d7daed and aggregate exact-head CI run generation including 31593372866; remediate any finding/failure or merge only after every gate passes.
```
