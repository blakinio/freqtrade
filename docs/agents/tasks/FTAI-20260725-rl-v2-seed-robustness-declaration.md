---
task_id: FTAI-20260725-rl-v2-seed-robustness-declaration
status: active
branch: docs/rl-v2-seed-robustness-declaration-20260725
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: ""
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-robustness-declaration.md
  - docs/ai_platform/RL_V2_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-seed-robustness-declaration-v1.json
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260725-rl-v2-paired-attribution-interpretation.md
  - docs/ai_platform/RL_V2_PAIRED_ATTRIBUTION_INTERPRETATION.md
  - ai_platform/experimental_model_research/rl-v2-paired-attribution-interpretation-v1.json
  - ai_platform/configs/rl_v2_training_research.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
search_first:
  - current develop and open PRs overlapping RL-v2 seeds, stochastic repeatability, execution infrastructure or protected data
---

# RL-v2 Seed Robustness Declaration

## Goal

Prospectively freeze a finite seed set, evidence schema and mechanism-consistency criteria for the
unchanged lifecycle-aligned RL-v2 variant.

This task is declaration-only. It does not authorize or perform training, backtesting, market-data
access, cache restore, baseline rerun or seed execution.

## Frozen seed set

The five new seeds are derived deterministically from namespace
`rl-v2-lifecycle-seed-robustness-v1`:

`1192187410, 1844572788, 250243770, 2049007791, 363304639`

The immutable anchor seed `42` is not in the new set and must not be rerun.

## Primary question

Across all five prospectively frozen seeds, does the lifecycle-aligned strategy continue to prevent an
ROI exit while the strategy's entry signal remains active?

A raw ROI exit followed by a 15-minute re-entry is not automatically a mechanism failure. The future
evidence must record whether the entry signal was active at the exit boundary, so a legitimate signal
transition is not confused with the inherited lifecycle conflict.

## Non-negotiable boundaries

- Freeze model, strategy, reward, features, thresholds, pairs, timeframes, fees and evaluation geometry.
- Permit only the seed value and a deterministic seed-specific FreqAI identifier to differ per run.
- Execute exactly five new variant seeds only in a separately authorized task.
- Do not rerun seed `42` or the immutable baseline.
- Do not access consumed historical OOS `20260501-20260630`.
- Do not access protected final holdout `20260801-20260930`.
- Keep profitability descriptive and non-gating.
- Do not rank, promote, deploy, retune or alter Phase 6 `selected_model=null`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T10:19:24+02:00
head: 9bf961c5adec1d4bbfccaa9316cfddbd7e3d4c5c
branch: docs/rl-v2-seed-robustness-declaration-20260725
pr: null
status: active
context_routes:
  - docs/agents/tasks/FTAI-20260725-rl-v2-paired-attribution-interpretation.md
  - docs/ai_platform/RL_V2_PAIRED_ATTRIBUTION_INTERPRETATION.md
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-robustness-declaration.md
  - docs/ai_platform/RL_V2_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-seed-robustness-declaration-v1.json
proven:
  - Develop head 9bf961c5adec1d4bbfccaa9316cfddbd7e3d4c5c contains the completed paired-attribution interpretation and terminal checkpoint.
  - No open RL-v2 seed-robustness PR existed at declaration start.
  - The immutable anchor used seed 42 and remains bound to run 30131273189 and artifact digest sha256:11e9d9a8e5f8e65474406524445c7b04fe3d9af5afa6d137847c913f8e66ae04.
  - The committed config passes model_training_parameters.seed to PPO, and the custom model adapter passes the same seed to the RL environment.
  - The new five-seed set is deterministically derived before execution and excludes seed 42.
  - Primary criteria inspect entry-signal state at ROI exit boundaries, avoiding false attribution from legitimate signal transitions.
  - Profitability, ranking, superiority, promotion, deployment and protected-data claims remain forbidden.
derived:
  - Five unseen deterministic seeds provide a bounded stochastic-repeatability probe without rerunning the observed anchor.
  - Active-entry state must be exported at external exits before the original lifecycle mechanism can be classified seed by seed.
  - Any execution failure or degenerate seed makes the result inconclusive rather than allowing selective exclusion.
unknown:
  - Whether all five seeds preserve the active-entry ROI lifecycle invariant.
  - Whether the unchanged model produces non-degenerate behavior for every declared seed.
conflicts: []
first_failure:
  marker: NONE
  evidence: This declaration changes no executable behavior and authorizes no execution.
rejected_hypotheses:
  - Select or replace seeds after observing results.
  - Rerun seed 42 or the immutable baseline.
  - Use profit as a seed-selection or pass criterion.
  - Treat reused development data as strict OOS or protected validation.
  - Access consumed OOS or the protected final holdout.
  - Combine seed testing with PPO, reward, feature, threshold or strategy changes.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-robustness-declaration.md
  - docs/ai_platform/RL_V2_SEED_ROBUSTNESS_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-seed-robustness-declaration-v1.json
validation:
  - command: deterministic seed derivation
    result: PASS
    evidence: SHA-256 namespace c70f5612edf1f2748eea6abafa2160af15a796bffe9c1df9ba59eed7c955d333 deterministically yields the five declared 31-bit seeds.
  - command: machine-readable declaration parse
    result: PASS
    evidence: The declaration is valid JSON and records execution_authorized_by_this_declaration=false.
blockers: []
next_action: Merge this declaration only after checkpoint, JSON, documentation and repository CI pass; then create a separate inert infrastructure task that can parameterize and evidence exactly the five frozen seeds without executing them.
```
