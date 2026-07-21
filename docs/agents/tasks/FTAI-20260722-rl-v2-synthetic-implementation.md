---
task_id: FTAI-20260722-rl-v2-synthetic-implementation
status: active
branch: docs/rl-v2-synthetic-implementation-task
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
  - merged PR #102 and closure PR #104 before synthetic implementation work
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

The reference action contract will express the desired position rather than a position-dependent transition:

- `0 = target_flat`
- `1 = target_long`

The semantic meaning of an action therefore does not change with hidden current position state. Environment state may still be used to calculate a transition/reward, but the policy-facing action itself always means the same desired position during synthetic training-style and inference-style evaluation.

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
updated_at: 2026-07-22T01:30:00+02:00
head: b2f9635cfe87d7d2e0349b4bf55c6734610d3edb
branch: docs/rl-v2-synthetic-implementation-task
pr: pending
status: ready
context_routes:
  - docs/ai_platform/RL_V2_DESIGN_CONTRACT.md
  - ai_platform/experimental_model_research/rl-v2-design-contract-v1.json
  - ai_platform/scripts/rl_v2_design_contract.py
owned_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
  - docs/ai_platform/RL_V2_SYNTHETIC_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-synthetic-implementation-v1.json
  - ai_platform/scripts/rl_v2_synthetic_reference.py
  - tests/ai_platform/test_rl_v2_synthetic_reference.py
proven:
  - RL-v2 design contract implementation PR #102 was squash-merged as c1834ef876e3c64bce89559ad20d93f7b6104f88 and closure PR #104 was squash-merged as b2f9635cfe87d7d2e0349b4bf55c6734610d3edb.
  - The merged contract permits exactly explicit position-state parity or position-independent action semantics as future design modes; no mode was selected by the contract task itself.
  - The merged contract requires flat-neutral reward to be strictly below valid long-entry reward, invalid-action penalties, bounded holding behavior, decision-time-only reward inputs and synthetic parity proof.
  - The merged contract requires action, do_predict, pre-trade signal, raw-trade and strict-OOS observability before future performance interpretation.
  - Consumed historical OOS and protected final holdout remain forbidden and no future evaluation window has been selected.
  - Frozen thresholds 0.006/-0.009 and authoritative Phase 6 selected_model null remain unchanged.
derived:
  - Position-independent desired-position actions are the smallest synthetic design that removes hidden current-position dependence from the policy-facing action meaning without assuming add_state_info support during backtesting.
  - A pure reference reward and telemetry layer can prove contract invariants before any FreqAI integration is attempted.
unknown:
  - Whether this synthetic reference will later map cleanly into a concrete FreqAI model/strategy implementation; that integration is intentionally outside this task.
conflicts: []
first_failure:
  marker: none
  evidence: This is a new prospective synthetic-only work package following the merged design contract.
rejected_hypotheses:
  - Implement a new FreqAI RL model or strategy in the same task as the synthetic proof.
  - Tune reward constants against consumed historical OOS.
  - Use a backtest to prove the desired-position action semantics.
  - Select or consume a future evaluation window before implementation is separately frozen.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-rl-v2-synthetic-implementation.md
validation:
  - command: live repository and overlap preflight
    result: PASS
    evidence: develop is b2f9635cfe87d7d2e0349b4bf55c6734610d3edb after RL-v2 design-contract closure and superseded PR #103 is closed without merge.
blockers: []
next_action: Merge this bounded task declaration, then implement only the desired-position synthetic reference, pure reward invariants, observability accumulator, descriptor validation, unit tests and documentation on a dedicated branch without any FreqAI model execution.
```
