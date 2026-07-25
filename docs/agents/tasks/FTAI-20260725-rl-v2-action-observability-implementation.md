---
task_id: FTAI-20260725-rl-v2-action-observability-implementation
status: active
branch: feat/rl-v2-action-observability-implementation
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

Implement the merged action-observability declaration as a pure project-specific recorder, validator, deterministic serializer and focused test suite. The package remains disabled by default and contains no execution workflow, model run, training job, backtest, market-data job or cache restore.

## Implementation result

The implementation normalizes inference dataframes into the frozen per-candle schema, emits deterministic JSONL plus manifest and summary artifacts, and independently validates schema, ordering, identity, digest and summary reconciliation.

Disabled mode performs a strict no-op. Enabled mode reads but never mutates the supplied dataframe. Runtime position state remains outside the recorder and no strategy, model, reward, feature, configuration, workflow or lifecycle path is changed.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T23:58:00+02:00
head: 0673a0e50889bfb5888f02a7496488d0503152d6
branch: feat/rl-v2-action-observability-implementation
pr: null
status: validating
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
  - Develop contains the merged prospective declaration and bounded implementation task.
  - The recorder is disabled by default and disabled capture and artifact methods return without inspecting inputs or writing files.
  - Enabled capture requires date, action, do_predict and volume and does not mutate the input dataframe.
  - Entry and exit booleans reproduce the existing strategy predicates exactly.
  - Timeline rows are deterministically sorted by pair, UTC timestamp and source-row ordinal.
  - Duplicate pair/timestamp rows, non-UTC timestamps, invalid actions, non-finite volume and metadata drift fail closed.
  - Manifest row count, pair set and SHA-256 digest and the summary counts are independently reconciled.
  - The implementation descriptor keeps strategy and workflow integration and every execution operation unauthorized.
  - Seventeen focused synthetic tests pass in an isolated local harness.
derived:
  - The pure evidence package can be reviewed and validated without touching Freqtrade runtime or historical datasets.
  - A later execution declaration can bind the validated library to project-specific hooks without changing this artifact schema.
unknown:
  - Whether a later execution package can wire the recorder through existing project-specific hooks without upstream core changes.
  - Which fresh unconsumed window a future execution declaration will select.
conflicts: []
first_failure:
  marker: NONE
  evidence: Recorder, descriptor, documentation and focused tests are complete within the prospectively declared paths.
rejected_hypotheses:
  - Add strategy integration or workflow wiring in this task.
  - Capture runtime trade state, raw features, model weights, credentials or private endpoints.
  - Modify strategy predicates or model behavior to simplify recording.
  - Emit an enabled artifact with zero rows or silently accept ambiguous evidence.
  - Access consumed OOS 20260501-20260630 or protected holdout 20260801-20260930.
  - Rerun or replace any prior seed.
  - Reopen Phase 6 or change selected_model=null.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-implementation-v1.json
  - ai_platform/scripts/rl_v2_action_observability.py
  - tests/ai_platform/test_rl_v2_action_observability.py
validation:
  - command: isolated pytest tests/ai_platform/test_rl_v2_action_observability.py
    result: PASS
    evidence: Seventeen tests passed, covering disabled no-op, signal parity, immutability, deterministic bytes, fail-closed validation and tamper detection.
  - command: Python AST compilation and maximum-line scan
    result: PASS
    evidence: The module and tests parse successfully and contain no line longer than 100 characters.
  - command: exact implementation scope review
    result: PASS
    evidence: Only the five declared project-specific code, test, descriptor, documentation and task paths are changed.
blockers: []
next_action: Open the focused five-file implementation PR, obtain AI Platform, Freqtrade and workflow-security validation, resolve any review or CI defect, then merge without executing a model or backtest.
```
