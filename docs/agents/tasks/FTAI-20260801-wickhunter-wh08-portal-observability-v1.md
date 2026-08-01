---
task_id: FTAI-20260801-wickhunter-wh08-portal-observability-v1
project_lane: freqtrade-wickhunter
status: waiting
action_scope: discovery_only_after_portal_ownership_release
branch: feat/wickhunter-wh08-portal-observability-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: null
depends_on:
  - FTAI-20260801-wickhunter-wh07-shadow-runtime-v1
owned_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh08-portal-observability-v1.md
required_reads:
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh07-shadow-runtime-v1.md
---

# WH-08 portal observability

## Objective

Expose the frozen WH-07 observability snapshot through read-only Portal state and views without adding trade controls, runtime mutation or execution authority.

## Phases

1. `WH08-DISCOVERY` — inspect current Portal ownership, read models, API and E2E seams. No implementation and no claimed shared paths while another Portal PR owns them.
2. `WH08-IMPLEMENT` — after the WH-07 snapshot contract is frozen and Portal ownership is delegated, implement the read-only consumer and fixture-based tests.
3. `WH08-VALIDATE` — fresh exact-head validator plus bounded WH-07/WH-08 integration E2E.

## Required displayed state

- bot mode and health;
- dynamic universe;
- source freshness;
- model and parameter identities;
- candidates and risk rejections;
- simulated positions, PnL and drawdown;
- retraining, validation and drift state;
- circuit-breaker state.

No trade buttons may be added to the liquidation page.

## Ownership rule

This task intentionally claims only its own task record until discovery proves exact non-conflicting Portal paths and the active Portal owner delegates them. The checkpoint must be updated before any code mutation.

## Invocation

`Uruchom WickHunter WH-08.` performs discovery only when live Portal ownership permits it. Otherwise it reports `waiting` with one next action and exits.

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
execution_reason: Portal ownership and integration seams must be resolved before code authorization
status: waiting
branch: feat/wickhunter-wh08-portal-observability-v1
base_branch: develop
related_pr: null
context_pressure: medium
context_growth: stable
decomposition_decision: discovery_first
decomposition_reason: active Portal ownership and final WH-07 snapshot paths are not yet frozen
validation_level: not_started
heavy_validation_runs: 0
proven:
  - WH-08 depends on WH-07
  - Portal paths may be owned by active non-WickHunter work
  - observability must remain read-only and add no trade controls
derived:
  - WH-08 can use a fixture after the WH-07 producer contract freezes, while WH-07 runtime hardening continues on separate paths
unknown:
  - final Portal-owned paths and current owner delegation
  - final WH-07 PortalObservabilitySnapshot contract
conflicts:
  - active Portal PR ownership must be released or explicitly delegated before code mutation
first_relevant_error: null
changed_paths: []
validation: []
blockers:
  - Portal ownership and WH-07 producer contract are not yet available
next_action: after active Portal ownership is released, perform read-only WH08-DISCOVERY and claim only exact delegated paths before implementation
```
