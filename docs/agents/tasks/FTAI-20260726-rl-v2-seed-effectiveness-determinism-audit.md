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

Perform a code-first, non-executing audit of the seed path used by the completed RL-v2 action-observability matrix, identify remaining determinism and provenance gaps, and retain fail-closed static evidence without rerunning a model or accessing market data.

## Terminal outcome

The audit implementation merged through PR 356 as `47427d99948427d74d82267e8e54843d7002244f`. The task closure merged through PR 362 as `768d28224a65a3217846a4efc0d8d7e7486a4599`.

Repository evidence supports effective seed propagation from runtime materialization through the project model, inherited PPO constructor and Gymnasium environment. It does not support an incomplete-seed-propagation defect and does not explain why two seeds produced identical complete trajectories or why BTC outputs were invariant across all four seeds.

No model execution, seed rerun, market-data access, cache restore, runtime change, ranking, promotion, dry-run or live action is authorized. Phase 6 remains authoritative with `selected_model=null`.

## Governance status note

The task frontmatter uses `status: done` to record task completion. The shared checkpoint contract does not define a terminal `done` value; its valid handoff state for a completed task with a concrete next action is `status: ready`. Diagnostic PR 363 exposed and validated the correction. It must be closed without merge.

## Required future provenance

Before any future RL execution, a separate prospective contract must freeze exact Python and dependency versions with hashes, device and Torch determinism flags, effective runtime-config digest, seed and RNG provenance, per-pair initial and final policy-state digests, and serialized trained-policy artifact digests. This does not authorize repeating the completed four-seed matrix.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T18:39:00+02:00
head: b807029a308127e68079d684cfa634cc7068fa87
branch: develop
pr: 362
status: ready
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
  - Audit declaration PR 354 passed exact-head CI and merged as 74d25ff0930b6424a302bb69a044f8ad58e9dd01.
  - Audit implementation PR 356 merged as 47427d99948427d74d82267e8e54843d7002244f from final head 1e30fdc7bd07e25b421316adbe6d3a6a7cbcc85e.
  - Final implementation AI Platform CI 30199859368, Freqtrade CI 30199859354 and zizmor 30199859383 completed successfully.
  - Task closure PR 362 passed Freqtrade CI 30200593598 and zizmor 30200593563 and merged as 768d28224a65a3217846a4efc0d8d7e7486a4599.
  - Runtime materialization writes the declared per-run seed and a distinct identifier.
  - The project model passes the seed to the environment and the inherited learner passes it to PPO.
  - The completed path keeps randomize_starting_position false, so the identified global random start branch is inactive.
  - Official Stable-Baselines3 source review supports seeding before policy construction, but the exact completed runtime version was not retained.
  - No retained evidence proves an incomplete seed-propagation defect or explains the identical policy outputs.
  - Canonical run request remains absent and no model, data, cache, seed rerun, ranking or promotion occurred in this audit.
derived:
  - Repository wiring is consistent with effective seed propagation through the completed path.
  - Identical trajectories remain compatible with policy-output collision, deterministic convergence or pair-specific action-boundary saturation.
  - Stronger diagnosis requires prospective dependency manifests and trained-policy state digests rather than a retrospective rerun.
unknown:
  - Whether seeds 271828182 and 628318530 produced byte-identical trained policies or distinct policies with identical deterministic actions.
  - Whether invariant BTC outputs reflect convergence, action-boundary saturation or another pair-specific deterministic path.
conflicts: []
first_failure:
  marker: CHECKPOINT_STATUS_UNSUPPORTED
  evidence: Diagnostic workflow run 30200854072 rejected checkpoint status done because the governance contract allows investigating, implementing, validating, blocked or ready.
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
    evidence: Workflow run 30199859368 completed successfully on implementation head 1e30fdc7bd07e25b421316adbe6d3a6a7cbcc85e.
  - command: exact-final-head Freqtrade CI
    result: PASS
    evidence: Workflow run 30199859354 completed successfully on implementation head 1e30fdc7bd07e25b421316adbe6d3a6a7cbcc85e, including CI Gate.
  - command: exact-final-head zizmor
    result: PASS
    evidence: Workflow run 30199859383 completed successfully on implementation head 1e30fdc7bd07e25b421316adbe6d3a6a7cbcc85e.
  - command: static audit descriptor validation
    result: PASS
    evidence: AI Platform tests validated exact source bindings, canonical descriptor equality, materialized config seeds and false execution authorizations.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md --require-checkpoint and python tools/agents/resume.py --task docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
    result: PASS
    evidence: Diagnostic PR 363 workflow run 30210862796 returned checkpoint_status=0 and resume_status=0; artifact 8634401292 digest sha256:8bae6d1554d3886dfd9a500595830c2521beba38e380285d826bb1e9df6bcb79 retained both outputs without stderr.
blockers: []
next_action: Create a separate prospective RL-v2 provenance-hardening contract before any future RL execution, freezing exact dependency and runtime manifests plus per-pair initial and final trained-policy digests; do not run a model or access data in that declaration.
```
