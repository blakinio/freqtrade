---
task_id: FTAI-20260801-wickhunter-wh02-deterministic-replay-v1
project_lane: freqtrade-wickhunter
status: ready
branch: feat/wickhunter-wh02-deterministic-replay-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: null
depends_on:
  - FTAI-20260731-wickhunter-wh01-production-materialization-v1
  - FTAI-20260801-wickhunter-wh02-replay-price-path-v1
owned_paths:
  - ai_platform/wickhunter/deterministic_replay.py
  - tests/ai_platform_integration/test_wickhunter_deterministic_replay.py
  - docs/ai_platform/WICKHUNTER_DETERMINISTIC_REPLAY.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-deterministic-replay-v1.md
required_reads:
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh02-replay-price-path-v1.md
  - docs/ai_platform/WICKHUNTER_REPLAY_PRICE_PATH.md
---

# WH-02 deterministic replay and event labels

## Objective

Bind the immutable WH-01 dataset and verified exact trade path into deterministic replay labels and independently verifiable replay evidence without accessing the protected holdout or authorizing trading.

## Phases

1. `WH02-DESIGN` — freeze entry, delay, fees, slippage, TP/SL ordering, timeout, MFE, MAE, time-to-outcome, purge/embargo and parity contracts.
2. `WH02-IMPLEMENT` — implement replay clock, labels, atomic publication, hashes and verifier.
3. `WH02-VALIDATE` — fresh exact-head validator session.

## Acceptance

- deterministic TP-first, SL-first and timeout outcomes;
- explicit delayed/missing-entry behavior;
- decimal-safe fees and slippage;
- returns, MFE, MAE and time-to-outcome;
- purged/embargoed walk-forward geometry;
- immutable self-hashed output and independent verification;
- replay/shadow parity fixture;
- protected holdout refused;
- no performance, model, execution, order or live-capital authority.

## Invocation

`Uruchom WickHunter WH-02.` resumes the exact current phase. `Zweryfikuj WickHunter WH-02.` is valid only when the checkpoint identifies a coherent candidate head.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T15:23:00+02:00
project_lane: freqtrade-wickhunter
phase: design
session_id: unclaimed
session_role: implementer
execution_mode: codex
execution_reason: multi-file implementation and deterministic test loop required
status: ready
branch: feat/wickhunter-wh02-deterministic-replay-v1
base_branch: develop
related_pr: null
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: contract design, implementation and validation share one immutable replay output
validation_level: not_started
heavy_validation_runs: 0
proven:
  - WH-01 contains 919 verified decisions across 20 symbols
  - exact post-decision aggregate-trade sequence is available in the immutable v4 package
  - the protected holdout was not accessed
  - all authority flags remained false and orders submitted remained zero
derived:
  - WH-02 can now define exact event ordering without candle-order approximation
unknown:
  - final entry, fee, slippage, TP/SL, timeout and parity contracts
conflicts: []
first_relevant_error: null
changed_paths: []
validation: []
blockers: []
next_action: claim the task, verify live ownership and exact immutable inputs, then complete the bounded WH02-DESIGN contract phase before implementation
```
