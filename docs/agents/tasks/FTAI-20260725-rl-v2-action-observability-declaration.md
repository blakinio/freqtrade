---
task_id: FTAI-20260725-rl-v2-action-observability-declaration
status: done
branch: develop
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: "305"
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-declaration-v1.json
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS.md
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - ai_platform/scripts/rl_v2_synthetic_reference.py
search_first:
  - current develop and open PRs overlapping RL-v2 action observability, prediction timelines, strategy signals, PPO configuration, run requests, workflows or model-selection ownership
optional_reads:
  - ai_platform/scripts/rl_v2_lifecycle_seed_robustness_evidence.py
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedResearchStrategy.py
---

# RL-v2 Action-Level Observability Declaration

## Goal

Prospectively freeze a disabled-by-default, research-only inference action-timeline contract before any recorder implementation or instrumented execution. This declaration defines capture fields, provenance, deterministic serialization, behavioral invariants, isolation and the required future sequence only.

## Declaration result

The merged contract limits future recording to immutable observation of per-pair inference rows after FreqAI prediction columns and deterministic pre-trade signal predicates exist. It authorizes no action, dataframe, signal, reward, feature, trade-state or lifecycle mutation.

Current position and transition classes remain post-hoc derivations from immutable completed-trade intervals plus the desired-position timeline. No implementation, model execution, backtest, data access, cache restore, seed rerun, retuning, ranking or promotion occurred in this task.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T23:46:20+02:00
head: 4c4a75e79f5260970c8221088f5e115f08a0e330
branch: develop
pr: 305
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-declaration-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-declaration-v1.json
proven:
  - Develop head 4c4a75e79f5260970c8221088f5e115f08a0e330 contains the merged three-file declaration from PR 305.
  - The frozen seed-robustness decision remains inconclusive and prior seeds remain immutable.
  - The declaration freezes a per-candle desired-position, do_predict, volume-gate and deterministic pre-trade signal schema.
  - Runtime trade-state capture is not required; current position and transitions are reserved for deterministic post-hoc derivation.
  - The recorder must be disabled by default, project-specific, non-mutating and free of secrets, raw features and model weights.
  - PR 305 changed exactly the three declared files and introduced no executable code, workflow or run request.
  - AI Platform CI 30176180499, Freqtrade CI 30176180469 and zizmor 30176180458 passed on the final declaration head.
  - PR 305 was squash-merged to develop as 4c4a75e79f5260970c8221088f5e115f08a0e330.
derived:
  - A bounded project-specific implementation can now add deterministic serialization and tests without authorizing execution.
  - An instrumented run still requires a second prospective declaration selecting a fresh unconsumed window.
unknown:
  - Whether existing project-specific hooks are sufficient for enabled recording without upstream core changes; implementation must prove this.
  - Which fresh unconsumed research window a later execution declaration will select.
conflicts: []
first_failure:
  marker: NONE
  evidence: Declaration scope, CI and merge completed without implementation or execution.
rejected_hypotheses:
  - Execute an instrumented run under this declaration.
  - Reuse consumed historical OOS 20260501-20260630 or protected holdout 20260801-20260930.
  - Modify upstream freqtrade core without a new declaration.
  - Mutate strategy or model behavior while recording telemetry.
  - Rerun, remove or replace prior seeds.
  - Reopen Phase 6 or change selected_model=null.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-declaration-v1.json
validation:
  - command: exact PR 305 file-scope comparison
    result: PASS
    evidence: The declaration PR changed exactly one task record, one documentation file and one machine-readable JSON declaration.
  - command: machine-readable declaration JSON parse
    result: PASS
    evidence: JSON is valid and keeps implementation and execution authorization false.
  - command: AI Platform CI 30176180499 / run 1242
    result: PASS
    evidence: AI platform tests, compile, Ruff, format, codespell and JSON validation passed.
  - command: Freqtrade CI 30176180469 / run 1469
    result: PASS
    evidence: Scope, pre-commit, documentation syntax, documentation build and CI gate passed.
  - command: GitHub Actions Security Analysis 30176180458 / run 1389
    result: PASS
    evidence: Required zizmor workflow-security analysis passed.
  - command: squash merge PR 305
    result: PASS
    evidence: GitHub merged the inert declaration to develop as 4c4a75e79f5260970c8221088f5e115f08a0e330.
blockers: []
next_action: Declare a separate bounded RL-v2 action-observability implementation task limited to project-specific recorder, validator, deterministic serializer and tests, with no model, backtest, market-data or cache operation.
```
