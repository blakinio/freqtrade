---
task_id: FTAI-20260726-rl-v2-action-observability-execution-declaration
status: active
branch: docs/rl-v2-action-observability-execution-declaration
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

Prospectively freeze a fresh historical-development action-observability study before any strategy wiring, market-data access, training or backtest. The declaration must preserve the terminal seed-validity result and select only new seeds and a previously unconsumed evidence window.

## Result

The declaration selects September-October 2025 as a fresh semantic evidence window, with bounded June-October data coverage and exactly four new seeds. It freezes the lifecycle-aligned model, strategy parent, configuration, pairs, timeframes, fee, PPO policy, data split, project-specific capture hook, artifact set and post-hoc trade-state derivation.

The declaration itself executes nothing.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T08:35:00+02:00
head: 45394c566d4ddd704c4ec40f6a91ecfd8068115a
branch: docs/rl-v2-action-observability-execution-declaration
pr: 317
status: validating
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
  - Develop head b10ebefaace1e15d070dd2f4662775df5d974db8 contains the terminal action-observability implementation closure.
  - No open PR overlaps RL-v2 action observability, lifecycle seeds, PPO configuration or run-request ownership.
  - Prior RL-v2 execution used March-April 2026 development evidence, consumed OOS is May-June 2026 and protected holdout is August-September 2026.
  - The selected September-October 2025 semantic evidence window is absent from prior RL-v2 execution declarations and does not overlap the forbidden windows.
  - Exactly four new seeds are frozen and no previous seed may be rerun or replaced.
  - The only authorized future strategy delta is disabled-by-default project-specific telemetry after inherited exit-signal evaluation.
  - PR 317 changes exactly the three declared paths.
derived:
  - A complete historical window before prior executed evidence can test action persistence without outcome-aware reuse of old seeds.
  - Four fresh seeds provide descriptive cross-seed mechanism evidence while preserving the old inconclusive aggregate unchanged.
unknown:
  - Whether the recorder can be wired through the declared subclass hook without duplicate pair capture in the full Freqtrade backtest lifecycle.
  - What action-versus-position patterns the four fresh seeds will produce.
conflicts: []
first_failure:
  marker: NONE
  evidence: Live preflight found no overlapping RL-v2 work or forbidden-window conflict.
rejected_hypotheses:
  - Rerun either invalid seed with telemetry.
  - Reuse March-April 2026 development evidence.
  - Access consumed OOS 20260501-20260630 or protected holdout 20260801-20260930.
  - Add telemetry directly to the parent strategy or upstream Freqtrade core.
  - Change PPO, reward, features, lifecycle, thresholds, pairs, timeframes or fee.
  - Use profitability, ranking, promotion, dry-run or live outcomes.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution-declaration.md
  - docs/ai_platform/RL_V2_ACTION_OBSERVABILITY_EXECUTION_DECLARATION.md
  - ai_platform/experimental_model_research/rl-v2-action-observability-execution-declaration-v1.json
validation:
  - command: live develop and overlapping open-PR preflight
    result: PASS
    evidence: Develop and open PR state do not conflict with the declared three-file scope.
  - command: declaration cross-check against prior timeranges and frozen identities
    result: PASS
    evidence: The selected window and four new seeds preserve consumed-OOS, holdout, prior-seed and Phase 6 boundaries.
  - command: exact PR 317 scope comparison
    result: PASS
    evidence: The PR contains only the task, documentation and machine-readable declaration.
blockers: []
next_action: Validate and merge this three-file prospective declaration, close its task record on develop, then create a separate inert implementation/infrastructure task before any data or model operation.
```
