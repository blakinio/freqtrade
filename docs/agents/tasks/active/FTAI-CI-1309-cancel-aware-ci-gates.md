# FTAI-CI-1309 — cancel-aware required CI gates

```yaml
task_id: FTAI-CI-1309-cancel-aware-ci-gates
programme_id: FTAI-CI-INFRASTRUCTURE
issue: 1309
status: implementing
claim_id: ftai-ci-1309-20260806T161000Z-gpt56
owner: repair-worker-1309-20260806T161000Z
base_branch: develop
base_head: 094f3751d1109d82cc7254f4b5957cf808641c91
branch: repair/1309-cancel-aware-ci-gates
priority: P1
risk: medium
feature_scope:
  type: ci_lifecycle
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: repository_ci_boundary
owned_paths:
  - .github/workflows/ci.yml
  - .github/workflows/ci-components.yml
  - tools/ci/validate_workflows.py
  - tests/ci/test_workflow_validation.py
  - docs/agents/tasks/active/FTAI-CI-1309-cancel-aware-ci-gates.md
  - docs/agents/tasks/archive/FTAI-CI-1309-cancel-aware-ci-gates.md
forbidden_paths:
  - ai_platform/**
  - deploy/**
  - requirements*.txt
  - pyproject.toml
conflict_groups:
  - central-ci-lifecycle
  - required-ci-gates
```

## Root cause

Central required gates use job-level `always()`. GitHub re-evaluates job conditions during cancellation and `always()` remains true, so a superseded workflow generation can retain a queued gate after all substantive jobs are cancelled. This can prevent the newest exact-head generation from materializing jobs.

## Bounded repair contract

- make every job-level `always()` in the two central PR workflows cancellation-aware with `!cancelled()`;
- preserve evaluation after ordinary dependency failures and skips;
- preserve one fail-closed `CI Gate` and one fail-closed `Component CI Gate`;
- add repository validation that rejects job-level `always()` without `!cancelled()`;
- add deterministic negative tests for both central workflow gates and a chained component job;
- do not change routing outputs, selected job semantics, action pins, permissions, deployment, product runtime or live-capital boundaries.

## Validation plan

```yaml
focused:
  - python -m pytest -q tests/ci/test_workflow_validation.py
  - python tools/ci/validate_workflows.py
required_exact_head:
  - Freqtrade CI
  - Risk-aware component CI
  - CodeQL
  - zizmor
runtime_acceptance:
  - supersede one PR generation and verify the obsolete generation becomes terminal without a queued always-run gate
  - verify the newest generation creates jobs
```

## Checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-06T16:10:00Z
phase: implementation
pull_request: none
exact_head: pending-first-implementation-commit
blockers: []
next_action: implement cancellation-aware conditions and deterministic validator coverage
```

## Safety boundary

No product code, deployment, credentials, trading, withdrawals, live-capital authority or protected infrastructure mutation is in scope.
