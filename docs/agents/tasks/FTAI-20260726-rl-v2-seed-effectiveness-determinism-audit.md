---
task_id: FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit
status: done
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "356"
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
  - docs/ai_platform/RL_V2_SEED_EFFECTIVENESS_DETERMINISM_AUDIT.md
  - ai_platform/experimental_model_research/rl-v2-seed-effectiveness-determinism-audit-v1.json
  - ai_platform/scripts/rl_v2_seed_effectiveness_audit.py
  - tests/ai_platform/test_rl_v2_seed_effectiveness_audit.py
search_first:
  - current develop and open PRs overlapping RL-v2, PPO, seed propagation, determinism, model artifacts, action observability or model-selection ownership
optional_reads:
  - ai_platform/configs/rl_v2_training_research.json
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/scripts/rl_v2_action_observability_execution_run_request.py
  - freqtrade/freqai/prediction_models/ReinforcementLearner.py
  - freqtrade/freqai/RL/BaseReinforcementLearningModel.py
  - freqtrade/freqai/RL/BaseEnvironment.py
  - .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
---

# RL-v2 Seed Effectiveness And Determinism Audit

## Goal

Perform a code-first, non-executing audit of the seed path used by the completed RL-v2 action-observability matrix. Determine what the repository can prove about seed propagation into the materialized runtime config, PPO constructor and Gym environment, identify remaining determinism/provenance gaps, and add fail-closed static evidence without rerunning any model or accessing market data.

## Terminal outcome

The static audit completed successfully and merged through PR 356 as `47427d99948427d74d82267e8e54843d7002244f` from exact final implementation head `1e30fdc7bd07e25b421316adbe6d3a6a7cbcc85e`.

The delivered package contains:

- a dependency-light fail-closed validator bound to the exact Git blob hashes of the frozen config, runtime materializer, project model, inherited learner, environment and request-gated workflow;
- a machine-readable descriptor with bounded conclusions and all execution authorizations set to false;
- a human-readable seed-effectiveness and determinism audit;
- focused tests for exact per-seed config materialization, source drift, descriptor tampering, request absence and retained provenance gaps.

No canonical request was created. No market data, cache, model, training, backtest, inference, replay, Hyperopt, prior seed, completed seed, consumed historical OOS or protected final holdout was accessed or executed. No upstream Freqtrade path, PPO behavior, reward, feature, lifecycle strategy, action telemetry or workflow behavior changed.

## Bounded findings

1. Runtime materialization replaces the frozen base seed with the declared per-run seed and assigns a distinct runtime identifier.
2. `DesiredPositionReinforcementLearner` copies the same seed into the environment dictionary.
3. The inherited learner passes `model_training_parameters`, including the seed, into the PPO constructor.
4. `BaseEnvironment` seeds its Gymnasium NumPy generator from the supplied seed.
5. The only identified Python-global `random.randint()` episode-start branch was inactive because the completed matrix froze `randomize_starting_position=false`.
6. The inspected official Stable-Baselines3 on-policy source at commit `06f613544574aa3157eba0ccee8570f5a8a8e1c9` calls `set_random_seed` before policy construction and seeds Python, NumPy, PyTorch, action space and environment.
7. The exact Stable-Baselines3 and Torch versions used by the completed execution were not retained, so the official-source review is supporting evidence rather than proof of the exact runtime bytes.

Repository evidence therefore supports effective seed wiring and does not support an incomplete-seed-propagation defect. It does not explain why seeds `271828182` and `628318530` produced identical complete timelines or why BTC outputs were invariant across all four seeds.

Compatible unresolved explanations remain policy-output collision, deterministic convergence and pair-specific action-boundary saturation. No runtime code change, seed rerun, ranking, selection or promotion is authorized.

## Required future provenance

Before any future RL execution, a separate prospective contract must freeze and retain:

- exact Python and dependency versions with immutable hashes, including Stable-Baselines3 and Torch;
- device and Torch deterministic-algorithm flags;
- effective runtime-config digest;
- seed and RNG provenance;
- per-pair initial policy-state digest before learning;
- per-pair final policy-state digest after learning;
- serialized trained-policy artifact digest.

These requirements do not authorize repeating the completed four-seed matrix.

## Frozen boundaries preserved

- canonical request absent;
- market-data access false;
- cache restore false;
- model training, backtest, inference, replay and Hyperopt false;
- seed rerun or replacement false;
- runtime and upstream-core change false;
- consumed historical OOS `20260501-20260630` access false;
- protected final holdout `20260801-20260930` access false;
- ranking, promotion, dry-run and live false;
- Phase 6 remains authoritative with `selected_model=null`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T13:39:00+02:00
head: 47427d99948427d74d82267e8e54843d7002244f
branch: develop
pr: 356
status: done
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
  - docs/ai_platform/RL_V2_SEED_EFFECTIVENESS_DETERMINISM_AUDIT.md
  - ai_platform/experimental_model_research/rl-v2-seed-effectiveness-determinism-audit-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
  - docs/ai_platform/RL_V2_SEED_EFFECTIVENESS_DETERMINISM_AUDIT.md
  - ai_platform/experimental_model_research/rl-v2-seed-effectiveness-determinism-audit-v1.json
  - ai_platform/scripts/rl_v2_seed_effectiveness_audit.py
  - tests/ai_platform/test_rl_v2_seed_effectiveness_audit.py
proven:
  - One-file task declaration PR 354 passed exact-head CI and merged as 74d25ff0930b6424a302bb69a044f8ad58e9dd01.
  - Implementation PR 356 contains exactly four audit files and merged from final head 1e30fdc7bd07e25b421316adbe6d3a6a7cbcc85e as 47427d99948427d74d82267e8e54843d7002244f.
  - Final-head AI Platform CI run 30199859368, run number 1492, completed successfully.
  - Final-head Freqtrade CI run 30199859354, run number 1806, completed successfully, including pre-commit, documentation, Python 3.11 through 3.14, Python 3.12 coverage, smoke tests, Ruff, Ruff format, mypy, distribution build and CI Gate.
  - Final-head zizmor run 30199859383, run number 1671, completed successfully.
  - Diagnostic PR 357 isolated exact Ruff 0.15.21 output, changed only its temporary workflow, and closed without merge.
  - The exact seven repository source bindings remained unchanged after unrelated develop movement and before final implementation merge.
  - The validator proves exact per-run seed materialization, project-model environment propagation, inherited PPO-constructor propagation, environment seeding and request absence.
  - Official Stable-Baselines3 source review supports seeding before policy construction, but the completed execution did not retain its exact installed version.
  - No retained evidence proves an incomplete seed-propagation defect or explains the identical policy outputs.
  - No model, data, cache, training, backtest, inference, replay, seed rerun, ranking or promotion occurred in this task.
  - Phase 6 remains authoritative with selected_model null.
derived:
  - Repository wiring is consistent with effective seed propagation through the completed path.
  - Identical trajectories remain compatible with policy-output collision, deterministic convergence or pair-specific action-boundary saturation.
  - Stronger future diagnosis requires prospective dependency manifests and trained-policy state digests rather than a retrospective rerun.
unknown:
  - Whether seeds 271828182 and 628318530 produced byte-identical trained policies or distinct policies with identical deterministic actions.
  - Whether invariant BTC outputs reflect convergence, action-boundary saturation or another pair-specific deterministic path.
conflicts: []
first_failure:
  marker: NONE
  evidence: The final implementation head passed all required repository checks and merged without any execution-capable change.
rejected_hypotheses:
  - Treat identical timelines as proof of a seed defect.
  - Rerun any completed seed to obtain missing provenance.
  - Change upstream Freqtrade, PPO, reward, features, lifecycle or workflow behavior inside this audit.
  - Add data access, model execution, ranking, promotion, dry-run or live behavior.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
validation:
  - command: exact-final-head AI Platform CI
    result: PASS
    evidence: Workflow run 30199859368, run 1492, completed successfully on 1e30fdc7bd07e25b421316adbe6d3a6a7cbcc85e.
  - command: exact-final-head Freqtrade CI
    result: PASS
    evidence: Workflow run 30199859354, run 1806, completed successfully on 1e30fdc7bd07e25b421316adbe6d3a6a7cbcc85e, including CI Gate.
  - command: exact-final-head zizmor
    result: PASS
    evidence: Workflow run 30199859383, run 1671, completed successfully on 1e30fdc7bd07e25b421316adbe6d3a6a7cbcc85e.
  - command: static audit descriptor validation
    result: PASS
    evidence: AI Platform tests validated exact source bindings, canonical descriptor equality, materialized config seeds and all false authorizations.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md --require-checkpoint
    result: NOT_RUN
    evidence: The one-file closure PR must run the canonical checkpoint validation before merge.
blockers: []
next_action: Create a separate prospective RL-v2 provenance-hardening contract before any future RL execution, freezing exact dependency and runtime manifests plus per-pair initial and final trained-policy digests; do not run a model or access data in that declaration.
```
