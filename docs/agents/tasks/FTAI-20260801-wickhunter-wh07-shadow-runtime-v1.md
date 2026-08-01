---
task_id: FTAI-20260801-wickhunter-wh07-shadow-runtime-v1
project_lane: freqtrade-wickhunter
status: ready
action_scope: discovery_only
branch: feat/wickhunter-wh07-shadow-runtime-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: null
depends_on:
  - FTAI-20260801-wickhunter-wh02-deterministic-replay-v1
  - FTAI-20260801-wickhunter-wh03-baseline-strategy-v1
  - FTAI-20260801-wickhunter-wh04-lightgbm-scorer-v1
  - FTAI-20260801-wickhunter-wh05-bounded-optimizer-v1
owned_paths:
  - ai_platform/wickhunter/shadow_runtime.py
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

Deliver a continuous read-only shadow runtime that consumes accepted WickHunter contracts, refreshes the dynamic universe, applies candidate/scoring/risk decisions, simulates positions and produces replay-parity and observability evidence without credentials or order submission.

## Phases

1. `WH07-DISCOVERY` — read-only seam, lifecycle, storage, source, restart, deployment and ownership discovery. It may run before dependencies are complete and must checkpoint `waiting` on completion.
2. `WH07-CONTRACT` — after WH-02 through WH-05 and completed WH-06, freeze the producer and `PortalObservabilitySnapshot` contracts.
3. `WH07-IMPLEMENT` — runtime lifecycle, persistence, recovery, source freshness, simulated PnL, drift and circuit-breaker state.
4. `WH07-VALIDATE` — fresh exact-head validator and replay/shadow parity session.

## Acceptance

- read-only current-data consumption;
- dynamic universe refresh;
- pure candidate, scorer and Risk Engine loop;
- simulated positions and PnL only;
- stale/unhealthy dependencies fail closed;
- restart recovery and bounded persistence;
- replay/shadow deterministic parity;
- stable read-only observability snapshot;
- no exchange credentials, order adapter or live-capital authority.

## Invocation

`Uruchom WickHunter WH-07.` currently starts only bounded discovery. The checkpoint must not authorize implementation until all declared package dependencies are terminal.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T15:23:00+02:00
project_lane: freqtrade-wickhunter
phase: investigate
session_id: unclaimed
session_role: discovery
execution_mode: chat
execution_reason: initial seam and ownership discovery does not require implementation
status: ready
branch: feat/wickhunter-wh07-shadow-runtime-v1
base_branch: develop
related_pr: null
context_pressure: medium
context_growth: stable
decomposition_decision: phased
decomposition_reason: discovery, contract, implementation and validation share one shadow-runtime deliverable
validation_level: not_started
heavy_validation_runs: 0
proven:
  - WH-06 Risk Engine and TradeIntent integration is completed
  - WH-07 implementation depends on terminal WH-02 through WH-05
  - bounded discovery can proceed without changing runtime code
derived:
  - WH-07 must freeze the producer contract before WH-08 implementation starts
unknown:
  - exact current runtime seam, storage and deployment ownership
conflicts: []
first_relevant_error: null
changed_paths: []
validation: []
blockers: []
next_action: perform read-only WH07-DISCOVERY, record the exact seams and proposed ownership, then checkpoint waiting and exit without implementation
```
