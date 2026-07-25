---
task_id: FTAI-20260725-rl-v2-action-observability-declaration
status: active
branch: docs/rl-v2-action-observability-declaration
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

The future recorder is limited to immutable observation of per-pair inference rows after FreqAI prediction columns and deterministic pre-trade signal predicates exist. It may not mutate actions, dataframes, signals, rewards, features, trade state or lifecycle behavior.

Current position and transition classes will be derived later from immutable completed-trade intervals plus the desired-position timeline rather than coupled into runtime trade-state handling. No implementation, model execution, backtest, data access, cache restore, seed rerun, retuning, ranking or promotion is authorized by this task.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-25T23:42:00+02:00
head: d5548fd37265c4ac83b5216058f3e94cf9886a2b
branch: docs/rl-v2-action-observability-declaration
pr: 305
status: active
context_routes:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md
  - docs/ai_platform/RL_V2_SEED_VALIDITY_DIAGNOSIS.md
  - ai_platform/freqaimodels/DesiredPositionReinforcementLearner.py
  - ai_platform/strategies/AiDesiredPositionRLResearchStrategy.py
  - ai_platform/scripts/rl_v2_synthetic_reference.py
owned_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-declaration-v1.json
proven:
  - Develop head fb8001f38385a1b1a69c2869ee93968d014702b1 terminally closes the RL-v2 seed-validity diagnosis with decision=inconclusive.
  - Seeds 1710810709 and 1950377252 remain invalid at 14 and 13 completed trades and may not be rerun or replaced.
  - Immutable completed artifacts contain no retained per-candle inference action, do_predict or pre-trade signal timeline.
  - Current strategy code exposes desired-position action and do_predict columns and deterministic entry/exit predicates.
  - Current synthetic reference exposes count-level observability and deterministic desired-position transition semantics.
  - Open PR 288 is portal-only and open PR 109 is a UI reference; neither overlaps RL-v2 ownership.
  - This declaration changes exactly one task record, one AI-platform document and one machine-readable declaration.
  - PR 305 targets develop from the dedicated declaration branch with exactly the three owned paths.
derived:
  - A per-candle desired-position and gating timeline is sufficient for a later post-hoc join with immutable completed-trade intervals.
  - Capturing runtime trade state is unnecessary for this bounded observability contract and would create avoidable coupling.
  - A disabled-by-default project-specific recorder can be implemented without changing strategy or model behavior.
unknown:
  - Whether an enabled recorder can be integrated through existing project-specific hooks without any upstream core change; the future implementation task must prove this.
  - Which fresh unconsumed research window a later execution declaration will select.
conflicts: []
first_failure:
  marker: NONE
  evidence: Live repository state and source inspection support an inert declaration; no implementation or execution has occurred.
rejected_hypotheses:
  - Instrument or execute before a prospective declaration is merged.
  - Reuse consumed historical OOS 20260501-20260630 or protected holdout 20260801-20260930.
  - Capture secrets, raw feature vectors, model weights or private endpoints.
  - Mutate strategy signals, action values, rewards, features, trade state or lifecycle behavior.
  - Modify upstream freqtrade core under this declaration.
  - Rerun, remove or replace prior seeds.
  - Reopen Phase 6 or change selected_model=null.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-declaration-v1.json
validation:
  - command: live develop and overlapping open-PR preflight
    result: PASS
    evidence: Develop is fb8001f38385a1b1a69c2869ee93968d014702b1; no open PR overlaps RL-v2 action observability or model-selection ownership.
  - command: declaration boundary and source-code review
    result: PASS
    evidence: Frozen fields map to existing desired-position action, do_predict and deterministic signal semantics without authorizing runtime mutation.
  - command: exact branch scope comparison
    result: PASS
    evidence: The branch is three commits ahead of develop and changes exactly the three declared files.
  - command: machine-readable declaration JSON parse
    result: PASS
    evidence: The declaration renders as valid JSON with implementation and execution authorization both false.
blockers: []
next_action: Obtain required CI and exact checkpoint validation for PR 305, merge the inert three-file declaration, close this task on develop, then create a separate bounded implementation task that runs no model, backtest, data or cache operation.
```
