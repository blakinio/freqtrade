---
task_id: FTAI-20260801-wickhunter-wh07-shadow-runtime-v1
project_lane: freqtrade-wickhunter
status: validating
action_scope: implementation_and_validation
branch: feat/wickhunter-wh07-shadow-runtime-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: 974
depends_on:
  - FTAI-20260801-wickhunter-wh02-deterministic-replay-v1
  - FTAI-20260801-wickhunter-wh03-baseline-strategy-v1
  - FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1
  - FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1
owned_paths:
  - ai_platform/wickhunter/shadow_runtime.py
  - ai_platform/wickhunter/shadow_runtime_common.py
  - ai_platform/wickhunter/shadow_runtime_engine.py
  - ai_platform/wickhunter/shadow_runtime_logic.py
  - ai_platform/wickhunter/shadow_runtime_positions.py
  - ai_platform/wickhunter/shadow_runtime_snapshot.py
  - ai_platform/wickhunter/shadow_runtime_snapshot_builder.py
  - ai_platform/wickhunter/shadow_runtime_state.py
  - ai_platform/wickhunter/shadow_runtime_storage.py
  - tests/ai_platform_integration/test_wickhunter_shadow_runtime.py
  - docs/ai_platform/WICKHUNTER_SHADOW_RUNTIME.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh07-shadow-runtime-v1.md
required_reads:
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
---

# WH-07 shadow runtime

## Objective

Deliver a continuous read-only shadow runtime that consumes accepted WickHunter contracts,
refreshes the supplied dynamic universe, applies candidate/scoring/risk decisions, simulates
positions and publishes replay-parity and observability evidence without credentials or order
submission.

## Acceptance

- read-only current-data consumption through injected accepted snapshots;
- dynamic universe binding and refresh;
- pure candidate, scorer and Risk Engine loop;
- simulated positions and PnL only;
- stale, unhealthy or drifting dependencies fail closed;
- restart recovery and atomic bounded persistence;
- replay/shadow identity and TP/SL parity evidence;
- stable read-only `PortalObservabilitySnapshot` contract;
- no exchange credentials, order adapter or live-capital authority.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T23:16:00+02:00
project_lane: freqtrade-wickhunter
phase: validate
session_id: wh07-20260801-002
session_role: implementer
execution_mode: chat
execution_reason: direct GitHub implementation using the existing pure shadow and risk seams
status: validating
branch: feat/wickhunter-wh07-shadow-runtime-v1
head: bd18709c93faa0f3e11b96bbeff3efdf5f8b724e
base_branch: develop
related_pr: 974
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: discovery, runtime, persistence, parity and producer contract form one deliverable
validation_level: focused
heavy_validation_runs: 0
proven:
  - WH-02 through WH-05 and WH-06 are terminal and merged
  - the branch was synchronized normally with develop after terminal WH-05
  - existing shadow.py remains the pure candidate, score, TradeIntent and local RiskDecision seam
  - existing portal_risk.py remains fail-closed and contains no order submission
  - the runtime refuses live mode and contains no exchange, credential or order adapter dependency
  - stale universe, stale or unhealthy sources, drift and maximum drawdown fail closed before new decisions
  - simulated positions use accepted intent risk, leverage and TP/SL values only
  - restart state and the Portal snapshot are atomically persisted with canonical integrity checks
  - replay/shadow parity binds dataset, code, symbol, side, decision timestamp and TP/SL policy
  - every Portal snapshot records read_only true, zero orders and no credentials or live-capital authority
  - local Python syntax validation passes for all WH-07 modules and focused tests
derived:
  - WH-08 may consume portal-observability-snapshot.json without importing runtime internals
unknown:
  - exact-head repository CI result and any formatter or typing corrections
conflicts: []
first_relevant_error: null
changed_paths:
  - ai_platform/wickhunter/shadow_runtime.py
  - ai_platform/wickhunter/shadow_runtime_common.py
  - ai_platform/wickhunter/shadow_runtime_engine.py
  - ai_platform/wickhunter/shadow_runtime_logic.py
  - ai_platform/wickhunter/shadow_runtime_positions.py
  - ai_platform/wickhunter/shadow_runtime_snapshot.py
  - ai_platform/wickhunter/shadow_runtime_snapshot_builder.py
  - ai_platform/wickhunter/shadow_runtime_state.py
  - ai_platform/wickhunter/shadow_runtime_storage.py
  - tests/ai_platform_integration/test_wickhunter_shadow_runtime.py
  - docs/ai_platform/WICKHUNTER_SHADOW_RUNTIME.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh07-shadow-runtime-v1.md
validation:
  - command: python -m py_compile shadow_runtime*.py test_wickhunter_shadow_runtime.py
    result: PASS
blockers: []
next_action: inspect exact-head CI for PR 974, repair the first relevant failure cheaply, then perform fresh validation and merge with expected-head protection
```
