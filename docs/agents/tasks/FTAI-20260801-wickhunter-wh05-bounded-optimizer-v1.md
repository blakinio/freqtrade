---
task_id: FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1
project_lane: freqtrade-wickhunter
status: waiting
branch: feat/wickhunter-wh05-bounded-optimizer-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: null
depends_on:
  - FTAI-20260801-wickhunter-wh03-baseline-strategy-v1
  - FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1
owned_paths:
  - ai_platform/wickhunter/bounded_optimizer.py
  - tests/ai_platform_integration/test_wickhunter_bounded_optimizer.py
  - docs/ai_platform/WICKHUNTER_BOUNDED_OPTIMIZER.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1.md
required_reads:
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh03-baseline-strategy-v1.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1.md
---

# WH-05 bounded walk-forward optimizer

## Objective

Produce reproducible candidate-only parameter packages inside immutable hard bounds, first for the deterministic baseline and later for the frozen WH-04 model contract.

## Phases

1. `WH05-BASELINE` — hard-bound spaces, rolling walk-forward baseline search, seeds, perturbation checks and global/regime/cluster candidates. This phase may run in parallel with WH-04 after WH-03.
2. `WH05-MODEL-AWARE` — resume only after WH-04 merges and add model-aware tuning through the frozen WH-04 interface.
3. `WH05-VALIDATE` — fresh exact-head validator session.

After phase 1 the task checkpoints `waiting` and the worker exits. It does not remain active waiting for WH-04.

## Acceptance

- immutable hard bounds and deterministic seeds;
- rolling walk-forward geometry with purge/embargo;
- reproducibility and local perturbation checks;
- global, regime and symbol-cluster candidates;
- sparse-symbol inheritance;
- protected holdout refusal;
- candidate-only output with no automatic model or parameter promotion.

## Invocation

`Uruchom WickHunter WH-05.` resolves whether baseline-only or model-aware work is currently ready from the checkpoint.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T15:23:00+02:00
project_lane: freqtrade-wickhunter
phase: implement
session_id: unclaimed
session_role: implementer
execution_mode: codex
execution_reason: iterative bounded search implementation and reproducibility tests require a checkout
status: waiting
branch: feat/wickhunter-wh05-bounded-optimizer-v1
base_branch: develop
related_pr: null
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: baseline-only and model-aware phases produce one coherent optimizer package
validation_level: not_started
heavy_validation_runs: 0
proven:
  - baseline-only optimization may start after WH-03 without waiting for WH-04
  - model-aware optimization must consume the terminal WH-04 contract
derived:
  - WH-05 can overlap WH-04 only during the baseline-only phase
unknown:
  - final WH-03 bounds and WH-04 model interface
conflicts: []
first_relevant_error: null
changed_paths: []
validation: []
blockers:
  - WH-03 is not yet terminal
next_action: after WH-03 merges, claim WH-05 paths and complete only the WH05-BASELINE phase before checkpointing waiting for WH-04
```
