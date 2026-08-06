# FTAI-CI-1309 — cancel-aware required CI gates

```yaml
task_id: FTAI-CI-1309-cancel-aware-ci-gates
programme_id: FTAI-CI-INFRASTRUCTURE
issue: 1309
status: validating
claim_id: ftai-ci-1309-20260806T161000Z-gpt56
owner: repair-worker-1309-20260806T161000Z
base_branch: develop
base_head: 094f3751d1109d82cc7254f4b5957cf808641c91
branch: repair/1309-cancel-aware-ci-gates
pull_request: 1310
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

## Implemented repair

- `CI Gate` and the distribution-build dependency bridge now use `always() && !cancelled()`.
- `Component CI Gate` and every chained component job that uses `always()` now include `!cancelled()`.
- Ordinary failed/skipped dependency evaluation remains fail-closed because `always()` is preserved.
- Routing outputs, selection logic, action pins, permissions and required gate names are unchanged.
- `tests/ci/test_workflow_validation.py` scans both central workflow files and rejects any job-level `always()` without `!cancelled()`.
- The test includes explicit negative and accepted contract fixtures.

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
  - supersede one queued generation and verify it becomes terminal
  - after Actions recovery, supersede one generation with materialized jobs and verify no queued required gate remains
  - verify the newest generation creates jobs and completes normally
```

## Evidence and checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-06T16:20:00Z
phase: validation
pull_request: 1310
superseded_head: e338d75c90111511053bed180e8c71b5ac3a0081
superseded_runs:
  freqtrade_ci: 31119323088
  component_ci: 31119323805
superseding_head: pending-this-checkpoint-commit
external_incident:
  id: qcvjkzcs7j74
  component: GitHub Actions
  status: partial_outage
  effect: workflow runs may fail to start or stop partway through
focused_validation: pending_actions_execution
full_runtime_supersession_probe: pending_materialized_jobs
blockers:
  - active GitHub Actions partial outage
next_action: verify queued-generation cancellation on this commit, then run focused and runtime acceptance after Actions allocates jobs
```

## Safety boundary

No product code, deployment, credentials, trading, withdrawals, live-capital authority or protected infrastructure mutation is in scope.
