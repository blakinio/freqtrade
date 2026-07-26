---
task_id: FTAI-20260726-rl-v2-action-observability-execution-infrastructure
status: active
branch: feat/rl-v2-action-observability-execution-infrastructure
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "322"
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-infrastructure.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-contract-v1.json
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy.py
  - ai_platform/scripts/rl_v2_action_observability_execution_run_request.py
  - ai_platform/scripts/rl_v2_action_observability_execution_evidence.py
  - tests/ai_platform/test_rl_v2_action_observability_execution.py
  - .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-declaration-v1.json
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md
  - ai_platform/scripts/rl_v2_action_observability.py
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-execution.md
search_first:
  - current develop and open PRs overlapping RL-v2 action observability, lifecycle strategies, run requests, workflows, data windows, seeds or evidence ownership
---

# RL-v2 Action Observability Execution Infrastructure

## Goal

Implement the merged prospective execution declaration as inert, request-gated infrastructure. Add only the declared project-specific observable subclass, immutable execution contract, canonical request generator/validator, bounded workflow, deterministic action-versus-trade evidence tooling, tests and documentation.

The canonical request file remains absent. Infrastructure review performs no market-data access, model training, backtest, cache restore or prior-seed operation.

## Implementation result

The observable subclass calls inherited exit-signal evaluation unchanged, then records the frozen inference fields only when explicitly enabled. It fails closed on duplicate pair capture, malformed rows or missing provenance and writes the existing deterministic timeline, manifest and summary.

The request validator freezes the fresh geometry, four new seeds and all runtime hashes. The workflow triggers only on an exact-one-file canonical request, downloads fresh data without cache restore, executes exactly four seed backtests, retains immutable telemetry plus raw archives and emits descriptive aggregate evidence with `decision: null`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T09:10:00+02:00
head: 7fac7664899126cc9be687e6e6d73eec0874ff88
branch: feat/rl-v2-action-observability-execution-infrastructure
pr: 322
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-declaration-v1.json
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_INFRASTRUCTURE.md
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-infrastructure.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-contract-v1.json
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy.py
  - ai_platform/scripts/rl_v2_action_observability_execution_run_request.py
  - ai_platform/scripts/rl_v2_action_observability_execution_evidence.py
  - tests/ai_platform/test_rl_v2_action_observability_execution.py
  - .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
proven:
  - Develop contains the merged and closed prospective execution declaration and bounded infrastructure task.
  - PR 322 changes exactly the eight prospectively owned paths.
  - The canonical request path is absent from the branch and develop.
  - The observable subclass leaves inherited signals unchanged and records only after super populate_exit_trend.
  - Disabled telemetry returns after inherited evaluation without inspecting inference columns or writing files.
  - Enabled telemetry captures each pair once and fails closed on duplicates or missing provenance.
  - The contract freezes fresh 20250601-20251101 data, 20250901-20251101 execution and exactly four new seeds.
  - Runtime config materialization changes only strategy, identifier, train/backtest periods and the frozen seed.
  - The workflow uses same-run data artifacts and contains no cache restore action.
  - Per-seed evidence validates telemetry, runtime config, raw archive accounting and action-versus-position reconciliation.
  - The aggregate accepts exactly four frozen seed files and emits no automatic mechanism decision.
derived:
  - Infrastructure review remains execution-inert because the only workflow trigger path is absent.
  - A separate execution task and exact canonical request can later activate the frozen workflow without changing runtime inputs.
unknown:
  - Whether the full backtest lifecycle calls the subclass capture hook exactly once per pair.
  - Whether all four fresh runs complete and retain both pair timelines.
conflicts: []
first_failure:
  marker: NONE
  evidence: Python sources compile in an isolated syntax check; repository CI and lint are pending.
rejected_hypotheses:
  - Add or merge the canonical request in this task.
  - Restore a prior cache or reuse the March-April 2026 runtime identifiers.
  - Execute a previous seed, baseline or anchor.
  - Modify the parent lifecycle strategy, model, PPO, reward, features or upstream core.
  - Produce an automatic supported, not-supported, ranking or promotion decision.
  - Access consumed OOS 20260501-20260630 or protected holdout 20260801-20260930.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-infrastructure.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-contract-v1.json
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy.py
  - ai_platform/scripts/rl_v2_action_observability_execution_run_request.py
  - ai_platform/scripts/rl_v2_action_observability_execution_evidence.py
  - tests/ai_platform/test_rl_v2_action_observability_execution.py
  - .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
validation:
  - command: isolated Python compilation of new strategy, validator, evidence and tests
    result: PASS
    evidence: All four Python files parse successfully.
  - command: exact develop-to-branch scope comparison
    result: PASS
    evidence: The implementation changes exactly the eight owned paths and no canonical request.
  - command: canonical request absence check
    result: PASS
    evidence: The trigger file does not exist on the implementation branch.
blockers: []
next_action: Resolve any PR 322 CI, lint or review defect, merge the inert eight-file infrastructure, close this task, then create a separate execution task before materializing the exact canonical request.
```
