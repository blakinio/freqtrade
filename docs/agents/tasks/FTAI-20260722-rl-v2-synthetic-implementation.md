---
task_id: FTAI-20260722-rl-v2-synthetic-implementation
status: done
branch: feat/rl-v2-synthetic-implementation
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "107"
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json
  - ai_platform/scripts/rl_v2_synthetic_reference.py
  - tests/ai_platform/test_rl_v2_synthetic_reference.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
search_first:
  - merged PR #107 and current develop before any RL-v2 runtime integration work
  - active tasks overlapping RL-v2 research ownership
optional_reads:
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
  - ai_platform/freqaimodels/LongOnlyReinforcementLearner.py
  - ai_platform/strategies/AiLongOnlyRLResearchStrategy.py
---

# RL-v2 Synthetic Implementation

## Goal

Implement the first design-contract-conformant RL-v2 reference layer using deterministic synthetic/static evidence only. Select exactly one allowed design mode, prove reward and inference semantics without market data or model fitting, and provide the observability primitives required by the merged RL-v2 design contract before any future FreqAI model or strategy implementation is authorized.

## Selected design mode

`position_independent_action_semantics`

The policy-facing action contract expresses the desired position rather than a position-dependent transition:

- `0 = target_flat`
- `1 = target_long`

The semantic meaning of an action therefore does not change with hidden current position state. Environment state may still be used by a pure transition adapter or reward calculation, but the policy-facing action itself always means the same desired position during synthetic training-style and inference-style evaluation.

## Frozen synthetic reward parameters

These values were declared prospectively before implementation and may not be searched or tuned inside this task:

```yaml
flat_neutral_reward: -0.01
valid_long_entry_reward: 0.0
holding_profit_clip_abs: 0.02
holding_duration_penalty_per_step: 0.0001
holding_duration_penalty_cap: 0.01
exit_profit_clip_abs: 0.05
invalid_action_penalty: -1.0
```

Required synthetic reward semantics:

- while flat, `target_long` reward `0.0` is strictly greater than `target_flat` reward `-0.01`;
- a perpetual-flat/target-flat episode accumulates negative reward and is not an unpenalized zero-reward optimum;
- while long and targeting long, reward is current decision-time unrealized profit clipped to `[-0.02, 0.02]` minus a bounded duration penalty of `min(duration_steps * 0.0001, 0.01)`;
- while long and targeting flat, reward is current decision-time unrealized profit clipped to `[-0.05, 0.05]`;
- unsupported actions receive `-1.0`;
- no reward input may use future candles or post-decision market information.

These values are synthetic implementation constants only. They authorize no historical performance claim and may not be altered in response to consumed OOS.

## Required synthetic parity semantics

The pure transition adapter implements:

```text
current flat + target_flat -> hold_flat
current flat + target_long -> enter_long
current long + target_long -> hold_long
current long + target_flat -> exit_long
```

Tests prove the same desired-position mapping for training-style and inference-style calls. No runtime path in this task assumes `add_state_info` is available to the policy.

## Required observability harness

The synthetic accumulator preserves, per pair and in total where applicable:

- deterministic desired-position action counts, including zero-count actions;
- `do_predict` accepted and rejected counts;
- pre-trade entry and exit signal counts;
- raw backtest trade count;
- strict-OOS input, included, and excluded trade counts.

The snapshot is deterministic, JSON serializable, and tested without market data. Strict-OOS counts fail closed unless `included + excluded = input`.

## Non-negotiable boundaries

- No RL-v2 FreqAI model class.
- No RL-v2 strategy class.
- No RL-v2 config or experiment manifest.
- No training, model fitting, backtest, market-data download, OOS execution, Hyperopt, reward sweep, feature search, hyperparameter search, or performance evaluation.
- No future evaluation window declaration.
- Do not modify `rl-research-v1` code or evidence.
- Do not reuse consumed historical OOS `20260501-20260630` for tuning or validation.
- Do not access protected final holdout `20260801-20260930`.
- Do not change frozen thresholds `0.006/-0.009`.
- Do not change completed Phase 6 or authoritative `selected_model = null`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T08:55:00+02:00
head: 43e595681780a21e9d5905cf7523a964705b4a42
branch: feat/rl-v2-synthetic-implementation
pr: 107
status: done
context_routes:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json
  - ai_platform/scripts/rl_v2_synthetic_reference.py
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json
  - ai_platform/scripts/rl_v2_synthetic_reference.py
  - tests/ai_platform/test_rl_v2_synthetic_reference.py
proven:
  - RL-v2 design contract implementation PR #102 was squash-merged as c1834ef876e3c64bce89559ad20d93f7b6104f88 and closure PR #104 was squash-merged as b2f9635cfe87d7d2e0349b4bf55c6734610d3edb.
  - Canonical synthetic task declaration PR #105 was squash-merged as 36d9014b54f28caeb2d0a61900c624694b081430 before implementation began.
  - The selected design mode is position_independent_action_semantics with stable desired-position meanings target_flat/target_long.
  - Synthetic reward constants were frozen prospectively in the task declaration and are represented exactly in the descriptor/reference code.
  - Pure reward semantics make target_long strictly preferable to target_flat while flat and make perpetual flat-neutral episodes accumulate negative reward.
  - Holding reward is bounded by clipped decision-time unrealized profit and capped duration penalty; exit reward uses only supplied decision-time unrealized profit.
  - Training-style and inference-style transition adapters call the same canonical desired-position transition function.
  - Synthetic observability preserves zero-count actions, do_predict accepted/rejected counts, pre-trade entry/exit signals, raw trades, and strict-OOS input/included/excluded counts separately.
  - Descriptor validation first validates the merged RL-v2 design contract and then exact synthetic descriptor identity.
  - No RL-v2 FreqAI model, strategy, config, manifest, workflow, market data, training, backtest, OOS execution, performance evaluation, or future evaluation window was created or used.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden.
  - Frozen thresholds 0.006/-0.009 and completed Phase 6 selected_model null remain unchanged.
  - PR #107 pre-close gates passed on head 43e595681780a21e9d5905cf7523a964705b4a42: AI Platform CI 29877479814, zizmor 29877479791, and Freqtrade CI 29877479866 including pre-commit, documentation build, core matrix, and CI Gate.
derived:
  - A later runtime-integration-only task may reuse these pure semantics and counters after this task is merged and frozen.
  - Historical execution and a fresh prospective evaluation window remain separate later work packages.
unknown:
  - Whether the pure desired-position semantics integrate cleanly with a concrete FreqAI RL model/strategy surface; runtime integration is intentionally deferred.
conflicts: []
first_failure:
  marker: none
  evidence: Synthetic implementation and repository validation completed without an unresolved test, lint, security, documentation, or CI failure.
rejected_hypotheses:
  - Implement a new FreqAI RL model or strategy in the same task as the synthetic proof.
  - Tune reward constants against consumed historical OOS.
  - Use a backtest to prove desired-position action semantics.
  - Select or consume a future evaluation window before implementation is separately frozen.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json
  - ai_platform/scripts/rl_v2_synthetic_reference.py
  - tests/ai_platform/test_rl_v2_synthetic_reference.py
validation:
  - command: repository and overlap preflight
    result: PASS
    evidence: No open PR overlapped the canonical synthetic-only scope; implementation branch started from merged task declaration 36d9014b54f28caeb2d0a61900c624694b081430.
  - command: PR #107 repository gates before task-close commit
    result: PASS
    evidence: AI Platform CI 29877479814, zizmor 29877479791, and Freqtrade CI 29877479866 completed successfully; pre-commit, documentation build, core matrix, and CI Gate passed.
blockers: []
next_action: none. This synthetic-only implementation task is complete. Any RL-v2 runtime integration must begin as a new separately declared bounded task and must still prohibit historical training, backtesting, evaluation-window declaration, and protected-final-holdout access.
```
