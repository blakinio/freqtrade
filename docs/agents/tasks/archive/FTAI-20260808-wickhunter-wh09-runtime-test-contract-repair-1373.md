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
status: done
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
validation_level: focused_then_routed_ci
base_branch: develop
base_head: 4910f906f0bdf268c77f2ca104143e1bab5e0a66
branch: fix/wickhunter-wh09-runtime-test-contract-repair-20260808
pull_request: 1375
delivery_head: cc87ec927584598f1549ca526c36ad1328758d0a
merge_commit: 2b4a4304b589a992b349883a88e0b00090caf1b6
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

## Delivered repair

1. Replaced the parity replay test's mutable `SimpleNamespace` request shape with a frozen dataclass-shaped stub so the test truthfully exercises the production `dataclasses.replace()` path.
2. Aligned the reliability contract with the approved `candidate_paper_runtime_parity_supervisor` Docker entrypoint while preserving restart-safe supervisor telemetry and early-fail assertions.
3. Added explicit healthy `model_drift` and `data_drift` state to the position-sizing runtime tick fixture.
4. No product/runtime implementation file was modified.

## Terminal validation

- exact delivery head: `cc87ec927584598f1549ca526c36ad1328758d0a`;
- Freqtrade CI run `31249425628`: `success`;
- Risk-aware component CI run `31249425692`: `success`;
- CodeQL run `31249425625`: `success`;
- Zizmor run `31249425626`: `success`;
- PR diff remained limited to the three declared integration-test files plus this task record;
- WH09 Coordinator independent bounded audit review `4888520184`: `PASS`;
- no inline review threads remained;
- PR #1375 was squash-merged without bypass as `2b4a4304b589a992b349883a88e0b00090caf1b6`;
- Issue #1373 closed as completed.

## Safety closeout

The repair changed test contracts only. It did not change candidate selection, calibration, data science, `no_trade_confidence=0.60`, activation identities, replay-manifest binding, parity enforcement, runtime/deployment semantics, credentials, order adapters, execution, promotion, protected holdout access or live-capital authority. `orders_submitted=0` remains invariant.

## Terminal checkpoint

```yaml
checkpoint_version: 1
phase: archive_test_contract_repair
status: done
issue: 1373
pull_request: 1375
delivery_head: cc87ec927584598f1549ca526c36ad1328758d0a
merge_commit: 2b4a4304b589a992b349883a88e0b00090caf1b6
focused_and_routed_validation: passed
coordinator_audit: passed
blockers: []
next_action: Return WH09 Runtime / Acceptance to read-only readiness and wait for the Coordinator to provide an independently verified H900 operational candidate before candidate-bound preflight or any new PAPER window.
```
