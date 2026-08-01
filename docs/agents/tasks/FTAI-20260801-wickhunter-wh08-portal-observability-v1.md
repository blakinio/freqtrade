---
task_id: FTAI-20260801-wickhunter-wh08-portal-observability-v1
project_lane: freqtrade-wickhunter
status: validating
action_scope: implementation_and_validation
branch: feat/wickhunter-wh08-portal-observability-v1
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: 979
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
updated_at: 2026-08-01T23:44:00+02:00
project_lane: freqtrade-wickhunter
phase: validate
session_id: wh08-20260801-002
session_role: implementer
execution_mode: chat
execution_reason: bounded read-only Portal consumer uses new non-conflicting paths and exact-head GitHub validation
status: validating
branch: feat/wickhunter-wh08-portal-observability-v1
head: 4474639982efa00a2f02cd0488fa1ea6bcc3d97a
base_branch: develop
related_pr: 979
context_pressure: high
context_growth: stable
decomposition_decision: phased
decomposition_reason: reader, authenticated API, read-only dashboard, fixture and E2E share one frozen snapshot contract
validation_level: focused
heavy_validation_runs: 0
proven:
  - WH-07 PortalObservabilitySnapshot v1 is frozen on exact candidate head 6cee3b0f1c2b3e294d7bdd45fa93494e53ad1a7f
  - WH-07 exact-head AI Platform CI and security analysis pass
  - the WH-08 branch was synchronized normally with develop at 3900ac6043a5f5f4a9abd4e349ab4693e4ec78ed
  - open Portal PR 976 changes only an OIDC diagnostic workflow, deployment script and deployment test
  - PR 979 changes exactly the eleven declared WH-08 paths
  - the snapshot reader rejects symlinks, oversized or malformed content, unsupported mode, incomplete identities and every execution-authority flag
  - the API reuses the authenticated tenant boundary and returns no-store sanitized responses
  - the dashboard displays all required runtime, universe, source, identity, decision, risk, simulated-position, PnL, drift and circuit-breaker state
  - the only dashboard action is refresh and no trade, buy, sell, submit or execute control exists
  - the fixture and E2E scenario bind the exact frozen producer schema and zero-authority fields
derived:
  - WH-09 can use the accepted WH-07 snapshot and WH-08 read model as immutable evidence inputs
unknown:
  - exact-head Portal typecheck, lint, build and Playwright results
conflicts: []
first_relevant_error: null
changed_paths:
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
validation:
  - command: live open-PR and changed-path ownership preflight
    result: PASS
    evidence: PR 976 has no overlap with the eleven WH-08 paths
  - command: fixture schema and zero-authority contract review
    result: PASS
blockers: []
next_action: inspect exact-head CI for PR 979, repair the first relevant failure cheaply, then validate and merge with expected-head protection
```
