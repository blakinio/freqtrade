# FTAI-CI-1309 — cancel-aware required CI gates

```yaml
task_id: FTAI-CI-1309-cancel-aware-ci-gates
programme_id: FTAI-CI-INFRASTRUCTURE
project_lane: freqtrade-assurance
issue: 1309
status: complete_on_merge
claim_id: ftai-ci-1309-20260807T072400Z-gpt56
owner: repair-worker-1309-20260807T072400Z
base_branch: develop
original_base_head: 094f3751d1109d82cc7254f4b5957cf808641c91
branch: repair/1309-cancel-aware-ci-gates
pull_request: 1310
validated_implementation_head: de9f1eabec50ae2818179f84c0f9c8340230709c
completion_claim: repository_ci_boundary
ownership_release: on_merge
blocked_task_to_resume: issue_1304_pr_1308
```

## Delivered outcome

- `CI Gate` and the distribution-build bridge are cancellation-aware with `always() && !cancelled()`.
- `Component CI Gate` and every chained component job that depends on `always()` are cancellation-aware.
- Ordinary failed or skipped dependency evaluation remains fail-closed because `always()` is preserved for non-cancelled runs.
- Central routing outputs, selected-job rules, action pins, permissions, required check names and product/runtime behavior are unchanged.
- Deterministic repository tests reject job-level `always()` without `!cancelled()` in both central PR workflows.

## Runtime supersession evidence

```yaml
runtime_e2e:
  result: PASS
  system_boundary: GitHub pull_request concurrency and required-gate lifecycle
  superseded_head: e338d75c90111511053bed180e8c71b5ac3a0081
  superseding_head: de9f1eabec50ae2818179f84c0f9c8340230709c
  freqtrade_ci:
    superseded_run: 31119323088
    result: terminal_cancelled
    ci_gate: cancelled
    distribution_build: cancelled
    queued_or_in_progress_remaining: 0
  component_ci:
    superseded_run: 31119323805
    result: terminal_cancelled_or_skipped
    component_ci_gate: cancelled
    chained_jobs_terminal: true
    queued_or_in_progress_remaining: 0
  newest_generation_created_jobs: true
```

This reproduces the original defect boundary with materialized jobs and proves that superseding a generation no longer leaves an always-run gate queued behind the newer exact-head generation.

## Validation evidence before archive transition

```yaml
implementation_head: de9f1eabec50ae2818179f84c0f9c8340230709c
required_checks:
  freqtrade_ci:
    run: 31133800724
    result: PASS
  risk_aware_component_ci:
    run: 31133800528
    result: PASS
  codeql:
    run: 31119427482
    result: PASS
  zizmor:
    run: 31119427432
    result: PASS
focused_contract:
  evidence_source: Freqtrade CI lightweight required PR gate
  required_repository_validator: tools/ci/validate_workflows.py
  required_tests: tests/ci/test_workflow_validation.py
```

## Acceptance reconciliation

```yaml
acceptance:
  superseded_generation_terminates_completely: PASS
  obsolete_generation_has_no_queued_or_running_jobs: PASS
  newest_generation_creates_jobs: PASS
  normal_non_cancelled_gate_remains_fail_closed: PASS_BY_UNCHANGED_GATE_BODY_AND_REQUIRED_CI
  workflow_syntax_routing_action_pin_security_tests: PASS
  exact_head_required_ci_before_archive: PASS
material_findings_open: 0
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: repair-worker-1309-20260807T072400Z
  session_started_at: 2026-08-07T07:24:00Z
  checkpointed_at: 2026-08-07T07:28:00Z
  last_progress_at: 2026-08-07T07:28:00Z
  phase: close
  exact_head: SELF_AFTER_ARCHIVE_TRANSITION
  pull_request: 1310
  active_operation: final exact-head CI and merge closeout
  external_run_ids: []
  operation_started_at: null
  wait_deadline_at: null
  check_generation: archive-final
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: archive transition committed and PR #1310 unchanged
  next_action: run a fresh final-diff audit, verify zero review threads, then observe the required exact-head CI generation and merge only after every required check passes
```

## Closeout contract

This archive transition changes PR #1310 after the implementation-head validation above. PR #1310 may merge only after a fresh audit of the complete final diff, zero unresolved review threads and all required checks pass on the exact archive-transition head. Merge closes #1309, releases ownership and removes the CI-lifecycle blocker from #1304 / PR #1308.

## Safety boundary

No Portal runtime, deployment, credentials, protected environment, trading, withdrawals, model promotion or live-capital state is changed or authorized.
