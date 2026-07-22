---
task_id: FTAI-20260722-rl-v2-runtime-integration
status: active
branch: feat/rl-v2-runtime-integration-v1
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "pending"
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-runtime-integration.md
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - tests/ai_platform/test_rl_v2_runtime_integration.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json
  - ai_platform/scripts/rl_v2_synthetic_reference.py
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
search_first:
  - current develop and open PRs before runtime integration work
  - active tasks or PRs overlapping RL-v2 model/strategy ownership
optional_reads:
  - freqtrade/freqai/prediction_models/ReinforcementLearner.py
  - freqtrade/freqai/RL/BaseEnvironment.py
---

# RL-v2 Runtime Integration

## Goal

Add a bounded, non-executing RL-v2 FreqAI runtime integration that reuses the frozen synthetic desired-position semantics, reward reference, and observability contract without training, backtesting, historical evaluation, future evaluation-window declaration, or protected-final-holdout access.

## Implemented runtime surface

The dedicated implementation branch adds only:

- `DesiredPositionReinforcementLearner` with a two-action long-only `DesiredPositionEnvironment`;
- `AiDesiredPositionRLResearchStrategy` mapping `target_long` to entry intent and `target_flat` to exit intent under `do_predict == 1`;
- machine-readable descriptor `rl-v2-runtime-integration-v1`;
- direct binding to the merged synthetic transition, reward, label and observability primitives;
- dependency-light synthetic/static tests;
- runtime-integration documentation.

The environment exposes exactly `0=target_flat` and `1=target_long`. Both are valid policy outputs in either flat or long state. Current position is used only by the canonical transition and reward adapters; it does not change policy-facing action meaning.

## Frozen integration choices

- backend family: Stable-Baselines3 through existing FreqAI `ReinforcementLearner`;
- algorithm family: PPO;
- policy family: MLP policy;
- long-only spot semantics;
- no short actions;
- no reward, feature, or hyperparameter search.

## Non-negotiable boundaries

- No training or model fitting.
- No backtest, historical execution, or market-data download.
- No training config, experiment manifest, or run request.
- No Hyperopt, reward sweep, feature search, or hyperparameter search.
- No strict-OOS execution or performance extraction.
- No use of consumed historical OOS `20260501-20260630`.
- No access to protected final holdout `20260801-20260930`.
- No future evaluation-window declaration.
- No modification of `rl-research-v1` evidence.
- Frozen thresholds `0.006/-0.009` and Phase 6 `selected_model = null` remain unchanged.
- No PyTorch-vs-RL ranking, promotion, profitability, or superiority claim.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T23:50:00+02:00
head: cc5f567db0847725cd18bc98772da276c5241b16
branch: feat/rl-v2-runtime-integration-v1
pr: pending
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/scripts/rl_v2_synthetic_reference.py
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-runtime-integration.md
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - tests/ai_platform/test_rl_v2_runtime_integration.py
proven:
  - RL-v2 design contract PR #102 and synthetic implementation PR #107 are merged and frozen.
  - Runtime-integration task declaration PR #142 was squash-merged as 5ad498e6a2538690ff371fd7b061bdd363820bf5 and checkpoint handoff PR #145 as 14616beb9310a469767b6c01340a8481aca1d1ec.
  - No open PR at implementation start overlapped the declared RL-v2 model or strategy owned paths.
  - DesiredPositionEnvironment exposes exactly two desired-position actions through Discrete(2).
  - Runtime transition behavior delegates to the canonical desired_position_transition function.
  - Runtime reward behavior delegates to the prospectively frozen reference_reward function and does not redefine reward constants.
  - Both target_flat and target_long remain valid policy outputs regardless of flat or long current position.
  - Strategy mapping uses do_predict == 1 with target_long for enter_long and target_flat for exit_long and introduces no short semantics.
  - Runtime observability factory returns the canonical RLV2ObservabilityAccumulator with zero-count action buckets and separate prediction, signal, raw-trade and strict-OOS layers.
  - Runtime descriptor freezes PPO, MlpPolicy, long-only spot and exact action/binding semantics while authorizing no result-producing execution.
  - Dependency-light tests use pure synthetic semantics and static source binding instead of importing or executing the heavy RL runtime.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden.
  - Frozen thresholds 0.006/-0.009 and authoritative Phase 6 selected_model null remain unchanged.
derived:
  - The runtime adapter now removes the RL-v1 position-dependent action-numbering mismatch by expressing desired position directly.
  - A later execution-preflight task can bind a config only after this integration is merged and frozen.
unknown:
  - Whether full heavy freqai_rl runtime import succeeds in all repository CI environments; lightweight tests intentionally do not require it.
  - Whether a later execution preflight will require additional config-specific adapter checks.
conflicts: []
first_failure:
  marker: none
  evidence: Runtime integration implementation is prepared without training, backtesting, data download, evaluation-window selection, or holdout access; repository CI has not run yet.
rejected_hypotheses:
  - Train or backtest while implementing the runtime adapter.
  - Add a run request, historical timerange, or evaluation window to this task.
  - Retune frozen synthetic reward constants using consumed OOS evidence.
  - Add short actions or hidden position-dependent policy action meanings.
  - Modify completed Phase 6 or frozen Phase 5 thresholds.
changed_paths:
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - ai_platform/experimental_model_research/rl-v2-runtime-integration-v1.json
  - tests/ai_platform/test_rl_v2_runtime_integration.py
  - docs/ai_platform/RL_V2_RUNTIME_INTEGRATION.md
  - docs/agents/tasks/FTAI-20260722-rl-v2-runtime-integration.md
validation:
  - command: live repository and overlap preflight
    result: PASS
    evidence: Current open PRs are portal or WickHunter work and do not overlap the RL-v2 runtime owned paths.
  - command: static implementation review against merged RL-v2 design and synthetic contracts
    result: PASS
    evidence: New runtime code imports canonical desired_position_transition, reference_reward, desired_position_label and RLV2ObservabilityAccumulator and declares no execution artifact.
blockers: []
next_action: Open the RL-v2 runtime integration PR against develop, fix only contract, test, lint, documentation or CI failures, merge only when all required repository gates are green, then update this checkpoint to the merge SHA and declare the next bounded execution-preflight task without selecting an evaluation window.
```
