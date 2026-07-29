---
task_id: FTAI-20260729-portal-bm09-bot-management-e2e-closure
status: ready
branch: test/portal-bm09-bot-management-e2e-closure
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: 675
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
updated_at: 2026-07-29T11:11:00+02:00
head: e0a90ccdcfb3dc0e1ac03acede92f0f8c9da70e3
merged_commit: d7ae949cb91d44e260ca7c32e193d69238fad120
branch: test/portal-bm09-bot-management-e2e-closure
pr: 675
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/E2E_TEST_ARCHITECTURE.md
  - docs/ai_platform/portal/BM09_BOT_MANAGEMENT_E2E_CLOSURE.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
owned_paths:
  - ai_platform/portal/e2e/**
  - tests/ai_platform/portal/e2e/**
  - ai_platform/portal/web/e2e/specs/bots/full-product-closure.spec.ts
  - .github/workflows/portal-universal-e2e.yml
  - docs/ai_platform/portal/BM09_BOT_MANAGEMENT_E2E_CLOSURE.md
  - docs/ai_platform/portal/E2E_TEST_ARCHITECTURE.md
  - docs/agents/tasks/FTAI-20260729-portal-bm09-bot-management-e2e-closure.md
proven:
  - BM-07 exact-head repository CI passed and PR 672 merged as ef0550744104f4c82ef3f106181f14442f9b82af.
  - The BM-09 manifest covers every required scenario family exactly once and every referenced repository evidence path exists.
  - Critical Chromium traverses dashboard, fleet, bot detail, exchanges, signals and grid without direct private Freqtrade mutation traffic or credential references.
  - Lifecycle replay keeps accepted persisted command intent distinct from execution submission and authoritative execution proof.
  - AI Platform CI 30437195010 passed on exact head e0a90ccdcfb3dc0e1ac03acede92f0f8c9da70e3.
  - Portal Universal E2E 30437195047 passed both deterministic backend and critical Chromium closure jobs on the exact head.
  - Portal Web CI 30437194948 passed typecheck, lint, production build and Chromium regression on the exact head.
  - Freqtrade CI 30437194987 passed pre-commit, documentation, Python 3.11 through 3.14, coverage, distribution build and CI gate on the exact head.
  - Workflow security analysis 30437194958 passed on the exact head.
  - PR 675 squash merged as d7ae949cb91d44e260ca7c32e193d69238fad120.
derived:
  - Repository-side BM-00 through BM-09 and BMW delivery is closed without granting external-target or live-capital authority.
  - Future repository work must be declared as a separate package rather than extending the completed BM sequence implicitly.
unknown:
  - Real owner-managed Authentik, Vault, Synology, Freqtrade and Cloudflare target acceptance remains external evidence.
  - PI-05 still requires an owner-selected channel/provider and destination/privacy policy.
conflicts: []
first_failure:
  marker: resolved_bm09_manifest_ruff_format
  evidence: the first PR validation found only Ruff formatting in the BM-09 manifest test; exact formatter output was applied before all final exact-head gates passed
rejected_hypotheses:
  - Fixture and deterministic evidence do not prove real target acceptance.
  - A runtime acknowledgement does not prove authoritative execution.
  - Repository closure does not authorize P11, P14, production credentials, withdrawals or live capital.
changed_paths:
  - ai_platform/portal/e2e/scenarios/bot_management_closure.json
  - tests/ai_platform/portal/e2e/test_bm09_closure_manifest.py
  - ai_platform/portal/web/e2e/specs/bots/full-product-closure.spec.ts
  - .github/workflows/portal-universal-e2e.yml
  - docs/ai_platform/portal/BM09_BOT_MANAGEMENT_E2E_CLOSURE.md
  - docs/agents/tasks/FTAI-20260729-portal-bm07-command-activation.md
  - docs/agents/tasks/FTAI-20260729-portal-bm09-bot-management-e2e-closure.md
validation:
  - command: AI Platform CI 30437195010
    result: PASS
    evidence: exact head e0a90ccdcfb3dc0e1ac03acede92f0f8c9da70e3 completed successfully
  - command: Portal Universal E2E 30437195047
    result: PASS
    evidence: deterministic backend scenario and critical Chromium journey completed successfully
  - command: Portal Web CI 30437194948
    result: PASS
    evidence: typecheck, lint, production build and full Chromium regression completed successfully
  - command: Freqtrade CI 30437194987
    result: PASS
    evidence: all required jobs and final CI gate completed successfully
  - command: GitHub Actions security analysis 30437194958
    result: PASS
    evidence: exact-head workflow security analysis completed successfully
blockers: []
next_action: Keep BM-09 closed; start no further repository package unless a separately governed owner decision supplies PI-05, PI-06 target-acceptance or P11 prerequisites, and keep P14 blocked.
```
