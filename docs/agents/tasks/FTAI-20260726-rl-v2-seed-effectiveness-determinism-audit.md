---
task_id: FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit
status: active
branch: docs/rl-v2-seed-effectiveness-determinism-audit-task
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: pending
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
  - docs/ai_platform/RL_V2_SEED_EFFECTIVENESS_DETERMINISM_AUDIT.md
  - ai_platform/experimental_model_research/rl-v2-seed-effectiveness-determinism-audit-v1.json
  - ai_platform/scripts/rl_v2_seed_effectiveness_audit.py
  - tests/ai_platform/test_rl_v2_seed_effectiveness_audit.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
  - ai_platform/configs/rl_v2_training_research.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/scripts/rl_v2_action_observability_execution_run_request.py
  - freqtrade/freqai/prediction_models/ReinforcementLearner.py
  - freqtrade/freqai/RL/BaseReinforcementLearningModel.py
  - freqtrade/freqai/RL/BaseEnvironment.py
search_first:
  - current develop and open PRs overlapping RL-v2, PPO, seed propagation, determinism, model artifacts, action observability or model-selection ownership
optional_reads:
  - .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
  - tests/ai_platform/test_rl_v2_action_observability_execution.py
---

# RL-v2 Seed Effectiveness And Determinism Audit

## Goal

Perform a code-first, non-executing audit of the seed path used by the completed RL-v2 action-observability matrix. Determine what the repository can prove about seed propagation into the materialized runtime config, PPO constructor and Gym environment, identify remaining determinism/provenance gaps, and add fail-closed static evidence without rerunning any model or accessing market data.

## Frozen boundaries

- no canonical run request;
- no market-data download or cache restore;
- no model training, backtest, inference, replay or Hyperopt;
- no rerun, replacement or reinterpretation of seeds `271828182`, `628318530`, `1414213562` or `1618033988`;
- no change to PPO, model, reward, features, lifecycle strategy, action telemetry or execution workflow;
- no modification of upstream `freqtrade/` code;
- no ranking, selection, promotion, dry-run or live authority;
- consumed historical OOS `20260501-20260630` and protected final holdout `20260801-20260930` remain forbidden;
- Phase 6 remains authoritative with `selected_model=null`.

## Audit questions

1. Does runtime config materialization replace the frozen base seed with the declared per-run seed?
2. Does `DesiredPositionReinforcementLearner` pass that seed to the environment?
3. Does the inherited learner pass the same seed to the PPO constructor?
4. Does the inspected Stable-Baselines3 on-policy setup seed Python, NumPy, PyTorch, action space and environment before policy construction?
5. Is any active experiment path using an unseeded random source?
6. Which missing retained artifacts prevent distinguishing policy-output collision from a seed-propagation or runtime-determinism defect?

## Expected deliverables

- one human-readable audit document;
- one machine-readable audit descriptor with source hashes and bounded conclusions;
- one dependency-light static validator that fails closed on seed-path drift;
- focused tests for config materialization, source-binding and forbidden execution surfaces;
- no runtime behavior change.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T12:10:00+02:00
head: 9eda2b79f62296790ce99e43ecd93a78c059954e
branch: docs/rl-v2-seed-effectiveness-determinism-audit-task
pr: null
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
  - docs/ai_platform/RL_V2_SEED_EFFECTIVENESS_DETERMINISM_AUDIT.md
  - ai_platform/experimental_model_research/rl-v2-seed-effectiveness-determinism-audit-v1.json
  - ai_platform/scripts/rl_v2_seed_effectiveness_audit.py
  - tests/ai_platform/test_rl_v2_seed_effectiveness_audit.py
proven:
  - Develop head 9eda2b79f62296790ce99e43ecd93a78c059954e contains the terminal RL-v2 action-observability checkpoint f49929bd151df878de8b83f83a909e68a70dcad8.
  - No open PR overlaps RL-v2, PPO, DesiredPosition, seed propagation, determinism or action-observability ownership before this declaration.
  - The completed matrix retained identical full timelines for seeds 271828182 and 628318530 and invariant BTC action summaries across all four seeds.
  - Runtime materialization writes the declared seed into freqai.model_training_parameters.seed and uses a distinct runtime identifier.
  - DesiredPositionReinforcementLearner copies model_training_parameters.seed into the environment dictionary.
  - ReinforcementLearner forwards model_training_parameters into the PPO constructor.
  - The inspected Stable-Baselines3 on-policy setup invokes set_random_seed before policy construction; its base implementation seeds Python, NumPy, PyTorch, action space and environment.
  - The frozen RL config has randomize_starting_position false, so BaseEnvironment.reset does not enter its global random.randint branch in the completed matrix.
derived:
  - Current code evidence supports effective seed wiring and does not by itself support an incomplete-seed-propagation defect.
  - Identical action outputs remain compatible with policy-output collision or deterministic convergence.
  - Missing exact dependency versions and trained-policy parameter hashes prevent a stronger post-hoc conclusion from the retained evidence.
unknown:
  - Whether the two identical full trajectories came from byte-identical trained policies or distinct policies with identical deterministic actions.
  - Whether BTC invariance reflects convergence, action-boundary saturation or another pair-specific deterministic path.
conflicts: []
first_failure:
  marker: NONE
  evidence: This declaration adds only a task record and has no run request or execution surface.
rejected_hypotheses:
  - Treat identical timelines as proof of a seed defect before the code-first audit is complete.
  - Rerun any completed seed to obtain missing policy hashes.
  - Change upstream Freqtrade or Stable-Baselines3 behavior inside this audit.
  - Add model execution, data access, ranking, promotion, dry-run or live behavior.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
validation:
  - command: live develop and open-PR preflight
    result: PASS
    evidence: Develop was 9eda2b79f62296790ce99e43ecd93a78c059954e; open PRs 350, 339, 338 and 109 did not overlap this task ownership.
  - command: repository seed-path source review
    result: PASS
    evidence: Materializer, project model, inherited learner, environment and inspected Stable-Baselines3 seed setup were traced without running a model.
  - command: execution-surface absence review
    result: PASS
    evidence: This declaration contains no request, workflow, data, training or backtest path.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md --require-checkpoint
    result: NOT_RUN
    evidence: Repository CI must perform canonical checkpoint validation before merge.
blockers: []
next_action: Merge this one-file audit declaration only after exact-head CI passes, then create a separate implementation PR that adds the dependency-light static validator, machine-readable descriptor, focused tests and human-readable audit without running any model or accessing data.
```
