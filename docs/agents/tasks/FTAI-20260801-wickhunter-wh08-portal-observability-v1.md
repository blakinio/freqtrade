---
task_id: FTAI-20260801-wickhunter-wh08-portal-observability-v1
project_lane: freqtrade-wickhunter
status: implementing
action_scope: implementation_and_validation
branch: feat/wickhunter-wh08-portal-observability-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: null
depends_on:
  - FTAI-20260801-wickhunter-wh07-shadow-runtime-v1
owned_paths:
  - ai_platform/portal/web/lib/wickhunter-observability/contracts.ts
  - ai_platform/portal/web/lib/wickhunter-observability/reader.ts
  - ai_platform/portal/web/lib/wickhunter-observability/index.ts
  - ai_platform/portal/web/app/api/market/wickhunter/route.ts
  - ai_platform/portal/web/app/market/wickhunter/page.tsx
  - ai_platform/portal/web/components/wickhunter-observability-dashboard.tsx
  - ai_platform/portal/web/components/wickhunter-observability-dashboard.module.css
  - ai_platform/portal/web/fixtures/wickhunter/portal-observability-snapshot.json
  - ai_platform/portal/web/e2e/specs/wickhunter-observability.spec.ts
  - docs/ai_platform/portal/WICKHUNTER_OBSERVABILITY.md
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

1. `WH08-DISCOVERY` — inspect current Portal ownership, read models, API and E2E seams.
2. `WH08-IMPLEMENT` — implement the read-only consumer and fixture-based tests after the WH-07 snapshot contract is frozen.
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

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T23:40:00+02:00
project_lane: freqtrade-wickhunter
phase: implement
session_id: wh08-20260801-002
session_role: implementer
execution_mode: chat
execution_reason: bounded read-only Portal consumer uses new non-conflicting paths and direct GitHub validation
status: implementing
branch: feat/wickhunter-wh08-portal-observability-v1
head: 3c2a6f909f2c25350ff26152ba25adabd041e65b
base_branch: develop
related_pr: null
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: reader, authenticated API, read-only dashboard, fixture and E2E share one frozen snapshot contract
validation_level: ownership_preflight
heavy_validation_runs: 0
proven:
  - WH-07 PortalObservabilitySnapshot v1 is frozen on exact candidate head 6cee3b0f1c2b3e294d7bdd45fa93494e53ad1a7f
  - WH-07 exact-head AI Platform CI and security analysis pass
  - the WH-08 branch is synchronized normally with develop at 3900ac6043a5f5f4a9abd4e349ab4693e4ec78ed
  - open Portal PR 976 changes only an OIDC diagnostic workflow, deployment script and deployment test
  - all claimed WH-08 application, fixture, E2E, documentation and task paths are new and do not overlap PR 976
  - the consumer will remain authenticated, no-store, read-only and reject every credential, order or live-capital authority flag
derived:
  - the fixture can validate the frozen producer contract while WH-07 full repository CI finishes on separate paths
unknown:
  - exact-head Portal typecheck, lint, build and E2E results after implementation
conflicts: []
first_relevant_error: null
changed_paths:
  - docs/agents/tasks/FTAI-20260801-wickhunter-wh08-portal-observability-v1.md
validation:
  - command: live open-PR and changed-path ownership preflight
    result: PASS
    evidence: PR 976 has no overlap with the eleven claimed WH-08 paths
blockers: []
next_action: implement the validated snapshot reader, authenticated no-store API, read-only dashboard, fixture and bounded E2E, then run exact-head Portal validation
```
