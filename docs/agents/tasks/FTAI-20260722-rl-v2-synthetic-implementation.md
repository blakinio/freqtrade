---
task_id: FTAI-20260722-rl-v2-synthetic-implementation
status: implementing
branch: feat/rl-v2-synthetic-reference-v1
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "pending"
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
  - merged task declaration PR #105 and current develop before implementation merge
  - open PRs or active tasks overlapping RL-v2 research ownership
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

The reference action contract expresses the desired position rather than a position-dependent transition:

- `0 = target_flat`
- `1 = target_long`

The semantic meaning of an action therefore does not change with hidden current position state. Environment state may still be supplied explicitly to the pure reward reference, but the policy-facing action itself always means the same desired position in synthetic training-style and inference-style paths.

## Non-negotiable boundaries

- Synthetic/static implementation and tests only.
- Do not create an RL-v2 FreqAI model class, IStrategy, Freqtrade config, experiment manifest, execution workflow, or run request.
- Do not train, backtest, download market data, run Hyperopt, execute strict OOS extraction, or make performance conclusions.
- Do not modify or rerun `rl-research-v1`.
- Consumed historical OOS `20260501-20260630` remains forbidden.
- Protected final holdout `20260801-20260930` remains unused and forbidden.
- Do not select a future evaluation window.
- Frozen thresholds `0.006/-0.009` remain unchanged.
- Completed Phase 6 remains `selected_model = null` and cannot consume RL-v2 results.
- No PyTorch-vs-RL ranking, promotion, profitability, or superiority claim.

## Required implementation proofs

1. **Desired-position action parity**
   - deterministic mapping for `target_flat` and `target_long`;
   - identical action meaning in synthetic training-style and inference-style paths;
   - no action meaning that requires hidden current-position state.
2. **Reward geometry reference**
   - prospective fixed reference values chosen without historical-OOS tuning;
   - staying flat while already flat is strictly worse than choosing `target_long` while flat;
   - perpetual flat-neutral episodes accumulate a negative reward;
   - invalid action codes are penalized;
   - holding reward remains bounded;
   - exit/flatten reward uses only decision-time state supplied explicitly to the pure function.
3. **Observability accumulator**
   - action counts by pair and action, including zero-count actions;
   - `do_predict` accepted/rejected counts by pair;
   - pre-trade entry/exit signal counts by pair;
   - raw backtest trade count field;
   - strict-OOS input/included/excluded count fields;
   - deterministic JSON-serializable snapshot.
4. **Design-contract binding**
   - the synthetic implementation descriptor validates the merged `rl-v2-design-contract-v1` before exposing its reference behavior;
   - selected design mode must be one of the contract's allowed modes and exactly `position_independent_action_semantics` for this bounded task.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T01:45:00+02:00
head: 77efa3881c868fa3a4b5c821f0bddf996d4d5df4
branch: feat/rl-v2-synthetic-reference-v1
pr: pending
status: ready
context_routes:
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
  - Synthetic implementation task declaration PR #105 was squash-merged as 36d9014b54f28caeb2d0a61900c624694b081430 before implementation began.
  - Superseded competing design-contract PR #103 was closed without merge so the merged contract remains the single source of truth.
  - This task selects exactly position_independent_action_semantics and uses desired-position actions 0=target_flat and 1=target_long with identical synthetic training/inference meaning.
  - The pure reward reference prospectively fixes invalid=-1.0, flat-neutral=-0.1, flat-to-long=0.1, bounded long-hold penalty from 0.0 to -0.01, and decision-time supplied unrealized-profit exit reward.
  - The reference reward imports no market data and reads no future candles or global trading state.
  - The observability accumulator preserves zero-inclusive action counts, do_predict accepted/rejected counts, pre-trade signals, raw backtest trade count and strict-OOS input/included/excluded counts as separate JSON-serializable evidence layers.
  - The descriptor authorizes no FreqAI model, strategy, config, manifest, training, backtest, data download, Hyperopt, strict-OOS execution or performance evaluation.
  - Consumed historical OOS 20260501-20260630 and protected final holdout 20260801-20260930 remain forbidden; no future evaluation window was selected.
  - Frozen thresholds 0.006/-0.009 and authoritative Phase 6 selected_model null remain unchanged.
derived:
  - Desired-position semantics remove hidden current-position dependence from the policy-facing action meaning while keeping transition-state handling available to a later adapter.
  - The pure synthetic reference can prove reward, action-parity and observability invariants before any FreqAI integration task is authorized.
unknown:
  - Whether repository CI will expose lint, formatting or static test issues in the new synthetic reference implementation.
  - How a later FreqAI model/strategy adapter will translate desired-position targets into concrete transition/order logic; integration remains outside this task.
conflicts: []
first_failure:
  marker: none
  evidence: No runtime/model/data execution was attempted; implementation is currently static and synthetic only.
rejected_hypotheses:
  - Implement a new FreqAI RL model or strategy in the same task as the synthetic proof.
  - Tune reward constants against consumed historical OOS.
  - Use a backtest to prove desired-position action semantics.
  - Select or consume a future evaluation window before integration is separately frozen.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json
  - ai_platform/scripts/rl_v2_synthetic_reference.py
  - tests/ai_platform/test_rl_v2_synthetic_reference.py
validation:
  - command: task declaration PR #105
    result: PASS
    evidence: Freqtrade CI 29876188174 and zizmor 29876188246 completed successfully before squash merge 36d9014b54f28caeb2d0a61900c624694b081430.
  - command: static synthetic-reference construction review
    result: PASS
    evidence: Implementation is limited to pure action/reward/observability primitives, an exact descriptor, unit tests and documentation with no FreqAI runtime integration.
  - command: targeted synthetic tests and repository CI
    result: PENDING
    evidence: Implementation PR has not yet been opened.
blockers: []
next_action: Open the synthetic reference implementation PR, require AI Platform CI, Freqtrade CI and zizmor to pass, fix only concrete static validation failures, then squash-merge and close the durable checkpoint without starting any FreqAI model execution or historical evaluation.
```
