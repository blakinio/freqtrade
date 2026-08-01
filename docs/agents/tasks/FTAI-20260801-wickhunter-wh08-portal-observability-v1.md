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
updated_at: 2026-08-01T19:18:00+02:00
project_lane: freqtrade-wickhunter
phase: investigate
session_id: wh08-ownership-20260801-001
session_role: discovery
execution_mode: chat
execution_reason: live Portal ownership barrier inspection before any shared-path discovery
status: waiting
branch: feat/wickhunter-wh08-portal-observability-v1
base_branch: develop
related_pr: null
context_pressure: low
context_growth: stable
decomposition_decision: discovery_first
decomposition_reason: active Portal ownership and final WH-07 snapshot paths are not yet frozen
validation_level: ownership_preflight
heavy_validation_runs: 0
proven:
  - WH-08 depends on the frozen WH-07 PortalObservabilitySnapshot producer contract
  - open Portal repair PR 956 is active and owns deploy/synology/portal-oidc/diagnose_discovery.py plus tests/ai_platform/portal/deployment/test_portal_oidc_public_probe_user_agent.py
  - PR 956 is a bounded public-login probe repair and does not delegate broader Portal ownership to WH-08
  - WH-08 currently claims only this task record and has not mutated any Portal code, API, view, deployment or test path
  - observability must remain read-only and add no trade controls, credentials, order adapter or live-capital authority
derived:
  - exact Portal consumer paths must be selected only after PR 956 reaches a terminal state and WH-07 freezes the snapshot schema
  - fixture-first contract work can begin after WH-07 contract freeze without requiring the continuous runtime implementation to be complete
unknown:
  - final WH-07 PortalObservabilitySnapshot fields and serialized location
  - exact Portal read-model, API, view and E2E paths available after current ownership is released
conflicts:
  - active Portal PR 956 retains Portal ownership; no WH-08 implementation or shared-path claim is authorized
first_relevant_error: null
changed_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh08-portal-observability-v1.md
validation:
  - command: live open-PR and changed-path ownership preflight
    result: WAITING
    evidence: PR 956 is open and owns two Portal deployment/test paths
blockers:
  - WH-07 producer contract is not frozen
  - Portal repair PR 956 is not terminal and ownership has not been delegated
next_action: remain waiting; after PR 956 is terminal and WH-07 freezes PortalObservabilitySnapshot, rebase from live develop and perform exact read-only Portal seam discovery before claiming any shared path
```
