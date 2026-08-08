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
status: implementing
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
validation_level: focused_then_routed_ci
base_branch: develop
base_head: 4910f906f0bdf268c77f2ca104143e1bab5e0a66
branch: fix/wickhunter-wh09-runtime-test-contract-repair-20260808
implementation_authorized: test_contract_only
live_capital_authorized: false
protected_production_deployment_authorized: false
owned_paths:
  - tests/ai_platform_integration/test_wickhunter_candidate_paper_runtime_parity_service.py
  - tests/ai_platform_integration/test_wickhunter_paper_runtime_reliability_contract.py
  - tests/ai_platform_integration/test_wickhunter_shadow_runtime_position_sizing.py
  - docs/agents/tasks/active/FTAI-20260808-wickhunter-wh09-runtime-test-contract-repair-1373.md
```

## Objective

Repair three stale WickHunter integration-test contracts exposed by full Freqtrade CI run `31246886198` without changing runtime semantics, candidate science, activation/parity behavior, deployment behavior or trading authority.

## Proven failures

The full suite on the PR #1367 merge head (trusted WickHunter runtime code inherited from `develop`) reported exactly three WickHunter failures:

1. parity-service replay test uses a `SimpleNamespace` cast as `ShadowDecisionRequest`, while the runtime now replays an immutable dataclass copy via `dataclasses.replace()`;
2. PAPER reliability contract still expects the pre-parity supervisor Docker entrypoint, while the runtime package now intentionally starts `candidate_paper_runtime_parity_supervisor`, which delegates restart handling to `CandidatePaperRuntimeSupervisor`;
3. position-sizing test constructs `ShadowRuntimeTick` without the mandatory model/data drift fields introduced by the runtime drift contract.

The current `develop` head `4910f906f0bdf268c77f2ca104143e1bab5e0a66` contains the same affected WickHunter files as that failing run; intervening changes were outside this narrowly owned test scope.

## Repair contract

- Use a frozen dataclass-shaped replay request fixture so the parity test exercises the production `replace()` path truthfully.
- Update the deployment assertion to the current parity-supervisor entrypoint while retaining the restart-safe supervisor telemetry/early-fail assertions.
- Supply explicit healthy model/data drift states in the position-sizing tick fixture.
- Do not modify product/runtime code.
- Do not alter thresholds, candidate criteria, calibration/data selection, activation identities, replay-manifest binding or parity enforcement.
- Do not deploy anything and do not start a PAPER acceptance window.
- Preserve `orders_submitted=0` and zero live-capital authority.

## Validation plan

1. run the three affected integration-test modules on the exact PR head;
2. require applicable routed CI to pass;
3. verify the diff remains limited to the three test files plus this task record;
4. merge without bypass only after terminal CI and clean review state;
5. archive this task record and return WH09 Runtime to its independent `READY_FOR_CANDIDATE` gate assessment.

## Recovery checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-08T10:50:00+02:00
phase: implement_test_contract_repair
status: implementing
base_head: 4910f906f0bdf268c77f2ca104143e1bab5e0a66
branch: fix/wickhunter-wh09-runtime-test-contract-repair-20260808
issue: 1373
pull_request: pending
proven:
  - full CI run 31246886198 exposes exactly three stale WickHunter integration contracts
  - current approved container entrypoint is candidate_paper_runtime_parity_supervisor
  - parity supervisor delegates restart handling to CandidatePaperRuntimeSupervisor
  - ShadowRuntimeTick requires explicit model_drift and data_drift
unknown:
  - exact-head focused validation result
  - exact-head routed CI result
blockers: []
next_action: Commit the bounded test-contract repair, open one PR, and validate the exact head.
```
