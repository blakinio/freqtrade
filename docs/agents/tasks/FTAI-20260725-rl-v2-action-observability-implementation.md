---
task_id: FTAI-20260725-rl-v2-action-observability-implementation
status: active
branch: docs/rl-v2-action-observability-implementation-task
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: "TBD"
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-implementation-v1.json
  - ai_platform/scripts/rl_v2_action_observability.py
  - tests/ai_platform/test_rl_v2_action_observability.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-declaration-v1.json
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - ai_platform/scripts/rl_v2_synthetic_reference.py
search_first:
  - current develop and open PRs overlapping RL-v2 action observability, strategy signals, PPO configuration, run requests, workflows or model-selection ownership
optional_reads:
  - tests/ai_platform/test_rl_v2_synthetic_reference.py
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
---

# RL-v2 Action-Level Observability Implementation

## Goal

Implement the merged action-observability declaration as a pure project-specific recorder, validator, deterministic serializer and focused test suite. The package must remain disabled by default and must not integrate an execution workflow or run a model, training job, backtest, market-data job or cache restore.

## Bounded implementation contract

Allowed work:

- normalize synthetic inference dataframes into the frozen per-candle row schema;
- deterministically serialize JSONL timeline evidence;
- emit and validate manifest and summary JSON files;
- reject malformed, duplicate, non-UTC or secret-bearing evidence;
- prove disabled-mode no-op and enabled-versus-disabled signal equivalence using synthetic dataframes;
- document the implementation and bind it to the merged prospective declaration.

Forbidden work:

- modification of upstream `freqtrade/` core;
- strategy, model, reward, feature, trade-state or lifecycle behavior changes;
- workflow, run-request, config or evaluation-window additions;
- model execution, training, backtesting, market-data access or cache restore;
- consumed OOS or protected final-holdout access;
- seed rerun, replacement, retuning, ranking or promotion.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T23:50:00+02:00
head: 4e5a72b59e93be2584e1e4a661ae968818cbbcd2
branch: docs/rl-v2-action-observability-implementation-task
pr: null
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-declaration-v1.json
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - ai_platform/scripts/rl_v2_synthetic_reference.py
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-implementation-v1.json
  - ai_platform/scripts/rl_v2_action_observability.py
  - tests/ai_platform/test_rl_v2_action_observability.py
proven:
  - Develop head 4e5a72b59e93be2584e1e4a661ae968818cbbcd2 contains the merged declaration and its terminal closure.
  - The declaration freezes the exact row schema, deterministic artifact names, behavioral invariants and isolation boundaries.
  - Existing strategy predicates use action target_long plus accepted prediction and positive volume for entry, and target_flat plus accepted prediction for exit.
  - Existing synthetic reference defines desired-position labels and deterministic transition semantics.
  - Open PRs 307, 304 and 109 are portal or UI work and do not overlap the owned RL-v2 paths.
  - This task declaration changes only this task record and authorizes no execution.
derived:
  - A pure dataframe recorder can prove the frozen schema and signal equivalence without modifying strategy integration points.
  - Runtime position state can remain outside this implementation and be reconstructed only in a later evidence-analysis task.
unknown:
  - Whether a later execution package can wire the recorder through project-specific hooks without upstream core changes.
  - Which fresh unconsumed window a future execution declaration will select.
conflicts: []
first_failure:
  marker: NONE
  evidence: The prospective declaration is merged and live repository ownership has no RL-v2 overlap.
rejected_hypotheses:
  - Add execution integration or workflow wiring in this task.
  - Capture runtime trade state, raw features, model weights, credentials or private endpoints.
  - Modify strategy predicates or model behavior to simplify recording.
  - Access consumed OOS 20260501-20260630 or protected holdout 20260801-20260930.
  - Rerun or replace any prior seed.
  - Reopen Phase 6 or change selected_model=null.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md
validation:
  - command: live develop and overlapping open-PR preflight
    result: PASS
    evidence: Develop contains the merged declaration and no open PR overlaps the owned RL-v2 implementation paths.
  - command: implementation scope review
    result: PASS
    evidence: The task is limited to project-specific recorder, validator, serializer, documentation, descriptor and synthetic tests.
blockers: []
next_action: Implement the bounded disabled-by-default recorder, validator, deterministic serializer, descriptor, documentation and focused synthetic tests on a dedicated feature branch without any execution operation.
```
