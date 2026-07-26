---
task_id: FTAI-20260726-rl-v2-action-observability-execution-declaration
status: done
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "317"
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-declaration-v1.json
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_DECLARATION.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_IMPLEMENTATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-implementation-v1.json
  - docs/agents/tasks/FTAI-20260725-rl-v2-lifecycle-seed-robustness-execution.md
search_first:
  - current develop and open PRs overlapping RL-v2 action observability, lifecycle strategy, seeds, workflows, run requests, data windows or model-selection ownership
---

# RL-v2 Action Observability Execution Declaration

## Goal

Prospectively freeze a fresh historical-development action-observability study before any strategy wiring, market-data access, training or backtest.

## Result

PR 317 merged the three-file declaration as `b8e3fa1b946a5fb6e14a8ccccb1d96a8cbbd2787`. It selects September-October 2025, exactly four new seeds and a disabled-by-default project-specific capture hook while preserving all forbidden-window, prior-seed, Phase 6 and no-promotion boundaries.

No model, data or backtest operation occurred.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T08:45:00+02:00
head: b8e3fa1b946a5fb6e14a8ccccb1d96a8cbbd2787
branch: develop
pr: 317
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260725-rl-v2-seed-validity-diagnosis.md
  - docs/agents/tasks/FTAI-20260725-rl-v2-action-observability-implementation.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-declaration-v1.json
owned_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-declaration-v1.json
proven:
  - PR 317 changed exactly the three prospectively owned declaration paths.
  - The fresh execution range is 20250901-20251101 with bounded download range 20250601-20251101 and no cache restore.
  - Exactly seeds 271828182, 628318530, 1414213562 and 1618033988 are frozen; no prior or outcome-aware replacement seed is allowed.
  - The future observable strategy may only add disabled-by-default telemetry after inherited exit-signal evaluation.
  - AI Platform CI 30191265050, Freqtrade CI 30191265036 and zizmor 30191265031 passed on the final declaration head.
  - GitHub squash-merged PR 317 as b8e3fa1b946a5fb6e14a8ccccb1d96a8cbbd2787.
  - No market data, model, training, backtest, cache, consumed OOS or protected holdout was accessed.
derived:
  - The declaration is sufficient to begin a separate inert implementation/infrastructure package.
unknown:
  - Whether the full runtime invokes the declared capture hook exactly once per pair.
  - What action-versus-position patterns the four fresh seeds will produce.
conflicts: []
first_failure:
  marker: NONE
  evidence: All declaration validation and review gates passed.
rejected_hypotheses:
  - Rerun or replace prior seeds.
  - Reuse March-April 2026 evidence or access forbidden windows.
  - Add telemetry to the parent strategy or upstream core.
  - Change PPO, reward, features, lifecycle or execution geometry.
  - Rank, promote, dry-run or deploy from this evidence.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-declaration.md
validation:
  - command: AI Platform CI 30191265050
    result: PASS
    evidence: Compile, tests, Ruff, format, codespell and JSON validation passed.
  - command: Freqtrade CI 30191265036
    result: PASS
    evidence: Pre-commit, scope, documentation and final CI gate passed.
  - command: GitHub Actions Security Analysis 30191265031
    result: PASS
    evidence: zizmor passed on the final declaration head.
  - command: squash merge PR 317
    result: PASS
    evidence: Declaration merged to develop as b8e3fa1b946a5fb6e14a8ccccb1d96a8cbbd2787.
blockers: []
next_action: Create a separate inert RL-v2 action-observability execution infrastructure task implementing only the declared subclass hook, canonical request validation, workflow and deterministic evidence tooling; keep the canonical request absent and execute nothing.
```
