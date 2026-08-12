---
task_id: FTAI-20260812-portal-runtime-supervisor-1355
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: ready
task_kind: implementation
priority: critical
repository: blakinio/freqtrade
base_branch: develop
branch: codex/portal-runtime-supervisor-1355
related_pr: pending
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

This branch is stacked on the still-unmerged runtime-isolation producer because live repository state
disproved the dispatch assumption that its PR was merged. It does not edit any path owned by that
active producer. Coordinator integration must rebase the isolated paths onto `develop` after it
lands or otherwise preserve the exact dependency ordering.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-12T00:00:00Z
head: LIVE_BRANCH_HEAD_REQUIRED
head_role: supervisor_producer_candidate
branch: codex/portal-runtime-supervisor-1355
pr: pending
status: ready
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
derived:
  - deployment composition remains coordinator work because this producer owns no deployment paths
unknown:
  - real Linux UDS peer-credential E2E on the final exact head
  - real Docker lifecycle E2E, dependent on the final #1354 producer
  - coordinator independent audit and exact-head GitHub CI
conflicts:
  - dispatch claimed merged #1354/#1464 evidence, but live #1354 PR #1464 remains active and unmerged
first_failure:
  marker: linux_and_docker_e2e_unavailable_on_native_windows
  evidence: local host cannot prove Linux SO_PEERCRED or the privileged isolation backend
rejected_hypotheses:
  - the dispatch dependency state was current
changed_paths:
  - ai_platform/portal/runtime_supervisor/**
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
blockers:
  - final integration is dependency-blocked on the unmerged runtime-isolation producer
next_action: Coordinator performs a fresh independent audit, resolves the #1354 dependency, and runs Linux UDS plus real-Docker integration and exact-head CI; DO NOT MERGE this producer directly.
```
