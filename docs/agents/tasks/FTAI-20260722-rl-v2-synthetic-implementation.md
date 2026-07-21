---
task_id: FTAI-20260722-rl-v2-synthetic-implementation
status: active
branch: docs/declare-rl-v2-synthetic-implementation
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/rl_v2/__init__.py
  - ai_platform/rl_v2/semantics.py
  - ai_platform/rl_v2/observability.py
  - tests/ai_platform/test_rl_v2_semantics.py
  - tests/ai_platform/test_rl_v2_observability.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - docs/ai_platform/RL_ZERO_TRADE_FUNCTIONAL_DIAGNOSIS.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
search_first:
  - current develop and open PRs before implementation
  - active tasks overlapping ai_platform/rl_v2 ownership
---

# RL-v2 Synthetic Implementation

## Goal

Implement the smallest reusable, dependency-light RL-v2 semantics and observability harness that proves the selected position-independent design mode synthetically before any FreqAI model/strategy integration or historical execution.

This task selects exactly one design mode allowed by `rl-v2-design-contract-v1`:

`position_independent_action_semantics`

The policy-facing action contract is a desired-position action:

- `0 = target_flat`;
- `1 = target_long`.

The policy therefore does not need hidden current-position state to choose a semantically valid action. A pure transition adapter may use externally owned current trade state to translate desired position into `hold`, `enter_long`, or `exit_long` events.

## Frozen synthetic reward parameters

These values are declared prospectively for this implementation task and may not be searched or tuned here:

```yaml
flat_neutral_penalty: -0.01
valid_long_entry_reward: 0.0
holding_profit_clip: 0.02
holding_duration_penalty_per_step: 0.0001
holding_duration_penalty_cap: 0.01
exit_profit_clip: 0.05
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

The pure transition adapter must implement:

```text
current flat + target_flat -> hold_flat
current flat + target_long -> enter_long
current long + target_long -> hold_long
current long + target_flat -> exit_long
```

Tests must prove the same desired-position mapping for training-style and historical-inference-style calls. No runtime path may assume `add_state_info` is available to the policy.

## Required observability harness

Implement a pure counter/snapshot component that can later be wired into runtime code and that preserves, per pair and in total where applicable:

- deterministic desired-position action counts, including zero-count actions;
- `do_predict` accepted and rejected counts;
- pre-trade entry and exit signal counts;
- rejected-signal count;
- raw backtest trade count;
- strict-OOS input, included, and excluded trade counts.

The harness must be deterministic, serializable to JSON-compatible data, and tested without market data.

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

## Acceptance criteria

- Selected design mode is exactly `position_independent_action_semantics`.
- Desired-position actions and transition mapping are represented by dependency-light pure Python code.
- Frozen synthetic reward parameters above are represented immutably and tested exactly.
- Unit tests prove valid entry is preferred to neutral while flat.
- Unit tests prove a perpetual neutral episode has negative cumulative reward.
- Unit tests prove invalid actions are penalized.
- Unit tests prove holding reward is bounded and duration penalty is capped.
- Unit tests prove exit reward uses only supplied decision-time unrealized profit.
- Synthetic parity tests prove desired-position transition semantics are identical across training-style and inference-style adapters.
- Observability tests prove all mandatory counters, including zero-count actions, are preserved in JSON-compatible snapshots.
- Focused AI Platform CI, pre-commit, documentation build, zizmor and required Freqtrade CI gates pass.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T01:30:00+02:00
head: b2f9635cfe87d7d2e0349b4bf55c6734610d3edb
branch: docs/declare-rl-v2-synthetic-implementation
pr: null
status: active
context_routes:
  - docs/agents/tasks/FTAI-20260722-rl-v2-design-contract.md
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/rl_v2/__init__.py
  - ai_platform/rl_v2/semantics.py
  - ai_platform/rl_v2/observability.py
  - tests/ai_platform/test_rl_v2_semantics.py
  - tests/ai_platform/test_rl_v2_observability.py
proven:
  - RL-v2 design-contract implementation PR #102 was squash-merged as c1834ef876e3c64bce89559ad20d93f7b6104f88.
  - RL-v2 design-contract closure PR #104 was merged as b2f9635cfe87d7d2e0349b4bf55c6734610d3edb.
  - The design contract requires a later task to choose exactly one of two allowed position-state/action-semantics modes.
  - This task prospectively selects position_independent_action_semantics because desired-position actions do not require hidden current-position state in the policy observation.
  - Synthetic reward magnitudes are frozen prospectively in this task before implementation and are not selected from consumed historical OOS.
  - This task owns only pure semantics, observability, tests and documentation; no RL-v2 runtime/model/strategy/config execution surface is owned.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden.
  - Frozen thresholds 0.006/-0.009 and completed Phase 6 selected_model null remain unchanged.
derived:
  - A later runtime-integration task may reuse these pure semantics and counters only after this task is merged and frozen.
  - Historical execution and fresh evaluation-window declaration remain separate later work packages.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: Task declaration is ready for repository validation before implementation begins.
rejected_hypotheses:
  - Use explicit add_state_info-dependent policy state in historical backtesting.
  - Tune reward constants against consumed historical OOS.
  - Implement model/strategy/config or run historical execution in this task.
  - Declare a future evaluation window in this task.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
validation:
  - command: repository and overlap preflight
    result: PASS
    evidence: No open PR overlapped the declared synthetic-only scope at task creation; branch started from current develop b2f9635cfe87d7d2e0349b4bf55c6734610d3edb.
blockers: []
next_action: Open and merge this declaration-only task PR after required repository gates pass; only then create a fresh implementation branch from current develop and implement the owned synthetic semantics/observability paths.
```
