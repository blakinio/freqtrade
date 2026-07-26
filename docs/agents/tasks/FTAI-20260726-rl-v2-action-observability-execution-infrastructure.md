---
task_id: FTAI-20260726-rl-v2-action-observability-execution-infrastructure
status: active
branch: docs/rl-v2-action-observability-execution-infrastructure-task
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "319"
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-infrastructure.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-contract-v1.json
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy.py
  - ai_platform/scripts/rl_v2_action_observability_execution_run_request.py
  - ai_platform/scripts/rl_v2_action_observability_execution_evidence.py
  - tests/ai_platform/test_rl_v2_action_observability_execution.py
  - .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-declaration-v1.json
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md
  - ai_platform/scripts/rl_v2_action_observability.py
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-execution.md
search_first:
  - current develop and open PRs overlapping RL-v2 action observability, lifecycle strategies, run requests, workflows, data windows, seeds or evidence ownership
---

# RL-v2 Action Observability Execution Infrastructure

## Goal

Implement the merged prospective execution declaration as inert, request-gated infrastructure. Add only the declared project-specific observable subclass, immutable execution contract, canonical request generator/validator, bounded workflow, deterministic action-versus-trade evidence tooling, tests and documentation.

The canonical request file must remain absent. Infrastructure review must perform no market-data access, model training, backtest, cache restore or prior-seed operation.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T09:00:00+02:00
head: 9c5f34e0cf9fa72a3104cc85ff59e5cd87712b65
branch: docs/rl-v2-action-observability-execution-infrastructure-task
pr: 319
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-declaration-v1.json
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-infrastructure.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_INFRASTRUCTURE.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-contract-v1.json
  - ai_platform/strategies/AiDesiredPositionRLLifecycleAlignedObservableResearchStrategy.py
  - ai_platform/scripts/rl_v2_action_observability_execution_run_request.py
  - ai_platform/scripts/rl_v2_action_observability_execution_evidence.py
  - tests/ai_platform/test_rl_v2_action_observability_execution.py
  - .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
proven:
  - Develop contains the merged and closed prospective execution declaration at c04725708fbc229a71cb0bd4217a131959181d01.
  - The declaration freezes the fresh window, four new seeds, runtime inputs, project-specific hook and evidence contract.
  - The reusable recorder and validator are already merged and validated.
  - No open PR overlaps the declared RL-v2 paths.
  - PR 319 changes exactly this task record.
derived:
  - The infrastructure can remain inert by triggering only on an exact canonical request path that is absent from develop.
unknown:
  - Whether full-runtime strategy invocation captures each pair exactly once.
  - Whether the fresh data download and four-seed jobs will complete after a later canonical request.
conflicts: []
first_failure:
  marker: NONE
  evidence: The task is prospectively bounded before implementation.
rejected_hypotheses:
  - Add or merge the canonical request in this task.
  - Execute any data, model or backtest operation during infrastructure review.
  - Modify the lifecycle-aligned parent, model, reward, features or upstream core.
  - Restore old caches or touch consumed OOS or protected holdout.
  - Rerun or replace any previous seed.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-infrastructure.md
validation:
  - command: live develop and overlapping open-PR preflight
    result: PASS
    evidence: No conflicting RL-v2 ownership exists.
  - command: exact PR 319 scope comparison
    result: PASS
    evidence: The PR contains only the bounded task declaration.
blockers: []
next_action: Merge this one-file task declaration, then implement and validate exactly the eight owned paths with the canonical request absent and zero execution.
```
