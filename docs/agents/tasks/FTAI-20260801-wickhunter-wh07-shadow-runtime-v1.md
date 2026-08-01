---
task_id: FTAI-20260801-wickhunter-wh07-shadow-runtime-v1
project_lane: freqtrade-wickhunter
status: waiting
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
updated_at: 2026-08-01T19:05:56+02:00
project_lane: freqtrade-wickhunter
phase: contract
session_id: wh07-discovery-20260801-001
session_role: discovery
execution_mode: chat
execution_reason: bounded read-only seam and ownership discovery
status: waiting
branch: feat/wickhunter-wh07-shadow-runtime-v1
base_branch: develop
related_pr: null
context_pressure: medium
context_growth: stable
decomposition_decision: phased
decomposition_reason: discovery, contract, implementation and validation share one shadow-runtime deliverable
validation_level: discovery
heavy_validation_runs: 0
proven:
  - evaluate_shadow_decision in ai_platform/wickhunter/shadow.py is the pure candidate, scorer, trade-intent and local-risk decision seam and rejects LIVE_BLOCKED mode
  - select_dynamic_universe in ai_platform/wickhunter/universe.py is the immutable freshness-aware dynamic-universe seam
  - ai_platform/wickhunter/portal_risk.py is the fail-closed WH-06 Portal Risk bridge and atomic risk-evidence persistence seam
  - production_market_evidence_daemon.py publishes an atomic collector-health.json beside the durable active-pointer state and carries all authority flags false
  - readiness remediation PR 950 defines explicit live, ready, healthy, freshness and authority checks for collector-health.json
  - WH-02 replay_event_label is the intended exact replay/shadow event-ordering parity seam
  - restart-safe persistence should follow existing temporary-directory or temporary-file plus atomic-rename patterns
  - WH-07 owned runtime, tests, documentation and task paths do not overlap PR 950
derived:
  - the runtime should consume collector health and immutable active evidence read-only instead of modifying collector or deployment ownership
  - one bounded state root should persist the last accepted input identities, simulated positions, closed-position ledger, circuit-breaker state and latest observability snapshot
  - every loop must fail closed before candidate evaluation when readiness, source freshness, universe quality, replay-policy identity or risk-policy identity is invalid
  - PortalObservabilitySnapshot must expose stable hashes and simulated state only, with no order adapter or credentials field
unknown:
  - final WH-03 baseline result contract
  - final WH-04 scorer contract
  - final WH-05 optimizer parameter artifact contract
  - merged final shape of PR 950 readiness payload
conflicts:
  - PR 950 currently owns market-evidence readiness, daemon, workflow and deployment paths; WH-07 must consume the merged contract and must not edit those paths
first_relevant_error: null
changed_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh07-shadow-runtime-v1.md
validation:
  - command: read-only source and ownership discovery
    result: PASS
    evidence: exact pure decision, universe, risk bridge, collector health, atomic persistence and parity seams recorded
blockers:
  - WH-02, WH-03, WH-04 and WH-05 are not all terminal
  - readiness remediation PR 950 is not merged
next_action: remain waiting; after all dependencies are terminal and PR 950 settles the readiness payload, rebase from live develop and execute WH07-CONTRACT before any runtime implementation
```
