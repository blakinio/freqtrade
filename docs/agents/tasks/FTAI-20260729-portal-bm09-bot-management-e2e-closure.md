---
task_id: FTAI-20260729-portal-bm09-bot-management-e2e-closure
status: implementing
branch: test/portal-bm09-bot-management-e2e-closure
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: null
depends_on:
  - FTAI-20260729-portal-bm07-command-activation
  - FTAI-20260728-portal-bm08-dashboard-read-model-completion
owned_paths:
  - ai_platform/portal/e2e/**
  - tests/ai_platform/portal/e2e/**
  - ai_platform/portal/web/e2e/specs/bots/full-product-closure.spec.ts
  - .github/workflows/portal-universal-e2e.yml
  - docs/ai_platform/portal/BM09_BOT_MANAGEMENT_E2E_CLOSURE.md
  - docs/ai_platform/portal/E2E_TEST_ARCHITECTURE.md
  - docs/agents/tasks/FTAI-20260729-portal-bm09-bot-management-e2e-closure.md
---

# BM-09 bot-management E2E closure

## Goal

Close the repository-side bot-management product sequence with deterministic API/private-service evidence, a critical browser journey and exact-head CI while preserving all external-target and live-capital gates.

## Acceptance criteria

1. Every architecture-required BM-09 scenario family has one explicit repository evidence route.
2. Scenario references are validated and cannot silently point to missing tests.
3. Critical Chromium traverses the integrated bot-management surfaces through browser and same-origin BFF only.
4. The browser never addresses private Freqtrade mutation endpoints or receives credential references.
5. Accepted command intent, runtime acknowledgement and authoritative execution proof remain distinct.
6. Unavailable identity, signal, grid, runtime or evidence providers remain explicit and fail closed.
7. Portal Universal E2E runs the deterministic backend closure and critical browser closure.
8. AI Platform, Portal Web, Portal Universal E2E, Freqtrade and workflow-security gates pass on one exact head.
9. Fixture evidence is not labeled real Authentik, Vault, Freqtrade, Synology or Cloudflare acceptance.
10. P11 and P14 remain separately governed and no live-capital authority is added.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T10:50:00+02:00
head: 43a69e571faeee84a61b15e487f47a30413a87d7
branch: test/portal-bm09-bot-management-e2e-closure
pr: null
status: implementing
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/E2E_TEST_ARCHITECTURE.md
  - docs/ai_platform/portal/BM09_BOT_MANAGEMENT_E2E_CLOSURE.md
owned_paths:
  - ai_platform/portal/e2e/**
  - tests/ai_platform/portal/e2e/**
  - ai_platform/portal/web/e2e/specs/bots/full-product-closure.spec.ts
  - .github/workflows/portal-universal-e2e.yml
  - docs/ai_platform/portal/BM09_BOT_MANAGEMENT_E2E_CLOSURE.md
  - docs/agents/tasks/FTAI-20260729-portal-bm09-bot-management-e2e-closure.md
proven:
  - BM-07 exact-head repository CI passed and PR 672 merged as ef0550744104f4c82ef3f106181f14442f9b82af.
  - Existing domain E2E covers browser, BFF, risk, identity and fail-closed product surfaces.
  - Private PI-08 and BM-07 services keep credentials and Freqtrade endpoints outside the browser.
derived:
  - One versioned scenario matrix can make full repository coverage explicit without duplicating every narrow test.
unknown:
  - Real owner-managed Authentik, Vault, Synology, Freqtrade and Cloudflare target acceptance remains external evidence.
conflicts: []
first_failure:
  marker: none_observed
  evidence: implementation started from merged BM-07 with no BM-09 validation run yet
rejected_hypotheses: []
changed_paths:
  - ai_platform/portal/e2e/scenarios/bot_management_closure.json
  - tests/ai_platform/portal/e2e/test_bm09_closure_manifest.py
  - ai_platform/portal/web/e2e/specs/bots/full-product-closure.spec.ts
  - .github/workflows/portal-universal-e2e.yml
  - docs/ai_platform/portal/BM09_BOT_MANAGEMENT_E2E_CLOSURE.md
  - docs/agents/tasks/FTAI-20260729-portal-bm09-bot-management-e2e-closure.md
validation:
  - command: BM-09 manifest tests
    result: NOT_RUN
    evidence: pending first pull-request validation
  - command: Portal Universal E2E
    result: NOT_RUN
    evidence: pending first pull-request validation
blockers: []
next_action: Open the BM-09 pull request, fix every exact-head validation failure, then squash merge and record the final repository closure checkpoint.
```
