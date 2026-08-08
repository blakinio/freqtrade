# FTAI-20260808 WickHunter WH09 Runtime Test Contract Repair 1373

```yaml
policy_version: 2
prompting_standard_version: 2.1
task_id: FTAI-20260808-wickhunter-wh09-runtime-test-contract-repair-1373
repository: blakinio/freqtrade
project_lane: freqtrade-wickhunter
programme: WickHunter
phase: WH-09
issue: 1373
related_issue: 1144
mode: implementation
status: completed
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
validation_level: focused_then_routed_ci
base_branch: develop
base_head: 4910f906f0bdf268c77f2ca104143e1bab5e0a66
implementation_pr: 1375
implementation_head: cc87ec927584598f1549ca526c36ad1328758d0a
merge_commit: 2b4a4304b589a992b349883a88e0b00090caf1b6
implementation_authorized: test_contract_only
live_capital_authorized: false
protected_production_deployment_authorized: false
orders_submitted: 0
```

## Objective

Repair three stale WickHunter integration-test contracts exposed by full Freqtrade CI run `31246886198` without changing runtime semantics, candidate science, activation/parity behavior, deployment behavior or trading authority.

## Completed repair

PR #1375 changed only the three stale integration-test contracts plus the required task record:

1. the parity-service replay fixture is now dataclass-shaped and exercises the production immutable `dataclasses.replace()` replay path;
2. the PAPER reliability contract now expects the approved `candidate_paper_runtime_parity_supervisor` container entrypoint while retaining restart-safe supervisor telemetry/early-fail assertions;
3. the position-sizing fixture now supplies explicit healthy model/data drift states.

No product/runtime code, thresholds, candidate criteria, calibration/data selection, activation identities, replay-manifest binding, parity enforcement or deployment behavior changed.

## Terminal validation

Exact implementation head `cc87ec927584598f1549ca526c36ad1328758d0a` reached terminal success:

- Freqtrade CI run `31249425628`: success; pre-commit, documentation and required PR gate all passed;
- Risk-aware component CI run `31249425692`: success; AI Platform tests and lint passed, including the affected WickHunter tests;
- CodeQL run `31249425625`: success;
- GitHub Actions Security/zizmor run `31249425626`: success.

PR #1375 was squash-merged without bypass as `2b4a4304b589a992b349883a88e0b00090caf1b6`; issue #1373 closed completed.

## Safety closeout

No deployment was requested or performed. No PAPER acceptance window was started. Protected holdout access, automatic promotion, trading credentials, order adapter, execution and live-capital authority remained disabled; `orders_submitted=0`.

## Handover

The repair task is terminal and archived. WH09 Runtime / Acceptance Validator resumes from current trusted `develop` and may stop at `READY_FOR_CANDIDATE` until the Coordinator proves one independently verified operational candidate from the authorized 900-second lane.

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T11:00:00+02:00
phase: archived
status: completed
issue: 1373
pull_request: 1375
merge_commit: 2b4a4304b589a992b349883a88e0b00090caf1b6
terminal_ci:
  freqtrade_ci: 31249425628
  risk_aware_component_ci: 31249425692
  codeql: 31249425625
  zizmor: 31249425626
blockers: []
next_action: Return to WH09 Runtime validation and require an independently verified operational candidate before any staging preflight.
```
