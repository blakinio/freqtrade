---
task_id: FTAI-20260727-portal-e2e-architecture
status: validating
branch: test/portal-e2e-architecture-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
owned_paths:
  - ai_platform/portal/web/e2e/**
  - ai_platform/portal/web/playwright.config.ts
  - ai_platform/portal/web/package.json
  - .github/workflows/portal-web.yml
  - .github/workflows/portal-universal-e2e.yml
  - .github/workflows/portal-e2e-scheduled.yml
  - docs/ai_platform/portal/E2E_TEST_ARCHITECTURE.md
  - docs/ai_platform/portal/README.md
  - ai_platform/portal/web/README.md
  - .gitignore
  - docs/agents/tasks/FTAI-20260727-portal-e2e-architecture.md
required_reads:
  - AGENTS.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/QUALITY_AND_AUTONOMOUS_E2E.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
---

# Portal E2E architecture

## Goal

Replace the flat portal Playwright suite with domain-owned tests, shared fixtures, journeys, page objects, deterministic factories, bounded failure evidence and tiered CI execution without weakening identity, tenant, risk, dry-run or private-Freqtrade boundaries.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T23:59:00+02:00
base_develop: 96d229fc9082c24b0c534685efe9ef7d1ed91699
branch: test/portal-e2e-architecture-20260727
status: validating
proven:
  - The portal web package uses Next.js 16.2.11, Playwright 1.61.0 and deterministic fixture identity/data modes.
  - Existing browser coverage was concentrated in four flat specs and duplicated fixture authentication and canonical bot request data.
  - Existing Playwright configuration exposed only one Chromium project and one undifferentiated npm command.
  - Existing Portal Web and Universal E2E workflows both ran the same complete Chromium command.
  - The architecture preserves dry-run creation, fail-closed execution, same-origin BFF, opaque sessions, tenant isolation and read-only Liquid20 behavior.
derived:
  - Domain ownership plus tags removes suite duplication while preserving one source scenario.
  - Accessibility and resilience should use isolated projects so the normal Chromium regression remains stable and independently diagnosable.
  - Scheduled artifacts should upload only on failure with short retention because repository artifact storage is bounded.
unknown:
  - Final exact-head Portal Web, Universal E2E, repository and security workflow results.
conflicts: []
first_failure:
  marker: FLAT_UNDIFFERENTIATED_E2E_SUITE
  evidence: Four root-level specs duplicated helpers and one Chromium-only configuration could not select business gates or scheduled quality classes.
changed_paths: []
validation:
  - command: local TypeScript syntax validation with module stubs
    result: PASS
    evidence: All proposed Playwright configuration, fixtures, helpers and specs parse successfully.
blockers: []
next_action: Commit the bounded architecture, open a PR and require exact-head CI before merge.
```
