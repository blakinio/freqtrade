---
task_id: FTAI-20260722-rl-v2-runtime-integration
status: active
branch: docs/rl-v2-runtime-integration-task
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

Add a bounded, non-executing RL-v2 FreqAI runtime integration surface that reuses the frozen synthetic desired-position semantics, reward reference, and observability contract without performing training, backtesting, historical evaluation, or final-holdout access.

## Prospective runtime surface

The implementation task may add only:

- `DesiredPositionReinforcementLearner` and its two-action long-only environment adapter;
- `AiDesiredPositionRLResearchStrategy` mapping `target_long` to entry intent and `target_flat` to exit intent;
- a machine-readable runtime-integration descriptor;
- synthetic/static integration tests proving action/reward parity with `rl-v2-synthetic-implementation-v1`;
- observability hooks or adapters that preserve the merged synthetic counter vocabulary;
- documentation.

The runtime adapter must reuse the canonical pure functions from `ai_platform.scripts.rl_v2_synthetic_reference` rather than redefining action or reward semantics independently.

## Frozen integration choices

For variable isolation from `rl-research-v1`, later implementation under this task must keep:

- backend family: Stable-Baselines3 through the existing FreqAI `ReinforcementLearner` integration;
- algorithm family: PPO;
- policy family: MLP policy unless the existing FreqAI base requires another already-frozen default;
- long-only spot semantics;
- desired-position action space: `0=target_flat`, `1=target_long`;
- no short actions;
- no feature-set search or reward-parameter search.

This task does not authorize a training config, experiment manifest, run request, or evaluation timerange.

## Non-negotiable boundaries

- No training or model fitting.
- No backtest or historical execution.
- No market-data download.
- No Hyperopt, reward sweep, feature search, or hyperparameter search.
- No strict-OOS execution or performance extraction.
- Do not reuse consumed historical OOS `20260501-20260630` for validation or tuning.
- Do not access protected final holdout `20260801-20260930`.
- Do not declare a future evaluation window.
- Do not modify `rl-research-v1` code or evidence.
- Do not change frozen thresholds `0.006/-0.009`.
- Do not change completed Phase 6 or authoritative `selected_model = null`.
- No PyTorch-vs-RL ranking, promotion, profitability, or superiority claim.
- Any real execution must be declared by a later separate bounded task after this integration is frozen.

## Required implementation proofs

1. **Model/environment binding**
   - action space is exactly two desired-position actions;
   - environment transition and reward behavior call the merged synthetic reference semantics;
   - both desired-position actions remain valid policy outputs in either current position state;
   - unsupported action codes fail closed or receive the frozen invalid-action penalty as appropriate.
2. **Strategy binding**
   - `do_predict == 1` and `target_long` produce entry intent;
   - `do_predict == 1` and `target_flat` produce exit intent;
   - no hidden current-position state is required to interpret the policy-facing action;
   - no short-entry or short-exit semantics are introduced.
3. **Observability binding**
   - runtime-facing helpers preserve desired-position action labels and zero-count buckets;
   - `do_predict`, pre-trade signal, raw-trade and strict-OOS layers remain separately attributable;
   - this task does not fabricate runtime counts because no execution is authorized.
4. **Heavy-runtime safety**
   - import/static or minimal synthetic construction checks may be used only if they do not train, download data, or run a backtest;
   - if `freqai_rl` dependencies are unavailable in lightweight CI, tests must validate source/contract binding without weakening the runtime contract.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T23:15:00+02:00
head: 73f612557fd2a14d2ab3f8d413a32853b1e7f554
branch: docs/rl-v2-runtime-integration-task
pr: pending
status: ready
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
  - RL-v2 design contract PR #102 and synthetic implementation PR #107 are merged and their task checkpoints are done.
  - Canonical synthetic implementation uses position_independent_action_semantics with desired-position actions target_flat/target_long and frozen prospective reward constants.
  - Synthetic implementation PR #107 passed AI Platform CI 29898244424, zizmor 29898244427, and Freqtrade CI 29898244431 before squash merge d66b3e8d9381563556d7bdf37fe0bafbb3b87881.
  - Duplicate local work PR #139 was closed without merge after canonical PR #107 was discovered on current develop.
  - Current develop at task declaration is 73f612557fd2a14d2ab3f8d413a32853b1e7f554; open PRs #140 and draft #109 do not overlap RL-v2 model/strategy ownership.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden.
  - Frozen thresholds 0.006/-0.009 and authoritative Phase 6 selected_model null remain unchanged.
derived:
  - The next smallest safe step is runtime adapter code plus synthetic/static binding tests, not model execution.
  - Reusing the merged pure synthetic reference prevents a second independent definition of RL-v2 action and reward semantics.
unknown:
  - Whether the heavy `freqai_rl` dependency profile can import the new adapter in repository CI without additional test isolation.
  - Whether a later separately declared execution-preflight task will need a dedicated config/manifest; those artifacts are intentionally out of scope here.
conflicts: []
first_failure:
  marker: none
  evidence: This task is newly declared from the completed synthetic implementation checkpoint; no runtime integration code has been added yet.
rejected_hypotheses:
  - Train or backtest while implementing the runtime adapter.
  - Add a run request, historical timerange, or evaluation window to the integration task.
  - Retune frozen synthetic reward constants using consumed OOS evidence.
  - Modify the completed Phase 6 comparison or frozen Phase 5 thresholds.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-runtime-integration.md
validation:
  - command: live repository and overlap preflight
    result: PASS
    evidence: Current develop is 73f612557fd2a14d2ab3f8d413a32853b1e7f554; no open PR overlaps the declared RL-v2 model/strategy owned paths, and duplicate PR #139 is closed without merge.
blockers: []
next_action: Merge this bounded task declaration, then implement only the RL-v2 model/environment and strategy adapters, runtime-integration descriptor, observability binding, synthetic/static tests and documentation on a dedicated branch without any training, backtest, historical evaluation, evaluation-window declaration or protected-final-holdout access.
```
