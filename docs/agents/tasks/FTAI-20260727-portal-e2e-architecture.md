---
task_id: FTAI-20260727-portal-e2e-architecture
status: done
branch: test/portal-e2e-architecture-20260727
base_branch: develop
created: 2026-07-27
updated: 2026-07-28
related_prs:
  - "#548"
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
updated_at: 2026-07-28T00:22:00+02:00
base_develop: 7ce6f1ff20a59eff9d6ac904e20a15655f27d200
head: da114a27228e590e8cd348cba60beda4a1331f12
branch: test/portal-e2e-architecture-20260727
pr: "#548"
status: done
proven:
  - The portal web package uses Next.js 16.2.11, Playwright 1.61.0 and deterministic fixture identity/data modes.
  - The four flat browser specs were migrated into domain-owned scenarios with shared config, factories, fixtures, journeys, page objects and support helpers, then removed.
  - Playwright now exposes isolated Chromium, accessibility, resilience, Firefox, WebKit, mobile, stability and soak projects selected through a central tag vocabulary.
  - Portal Web CI runs typecheck, ESLint, a production fixture build and the complete Chromium regression.
  - Portal Universal E2E runs the deterministic backend simulator scenario and the critical Chromium browser journey.
  - Scheduled CI provides nightly cross-browser, mobile, accessibility and resilience coverage, weekly stability and a manually selected bounded soak.
  - Failure evidence includes trace, screenshot, video, HTML/JSON reports and redacted console/request summaries; CI uploads artifacts only on failure with seven-day retention.
  - The architecture preserves dry-run creation, fail-closed execution, same-origin BFF, opaque sessions, CSRF, MFA, step-up, tenant isolation, private Freqtrade and read-only Liquid20 behavior.
  - PR 548 merged as da114a27228e590e8cd348cba60beda4a1331f12.
derived:
  - Domain ownership plus tags removes suite duplication while preserving one source scenario.
  - Isolated quality projects keep normal regression deterministic and make accessibility, resilience, stability and soak failures independently attributable.
  - A single CI worker is required while fixture-backed mutable portal state is shared within one test server lifecycle.
  - Structured lint output in the failure artifact prevents diagnostic loss when GitHub job logs are truncated.
unknown:
  - Terminal result of the first scheduled nightly cross-browser matrix after merge.
conflicts: []
first_failure:
  marker: REACT_HOOK_LINT_COLLISION
  evidence: Portal Web CI run 30309736611 passed typecheck but ESLint interpreted the Playwright fixture callback parameter named use as a React hook. The parameter was renamed to provide without changing fixture behavior.
rejected_hypotheses:
  - Disable the React Hooks rule for all portal tests.
  - Skip lint or weaken the Portal Web merge gate.
  - Preserve copied root-level specs alongside the domain suite.
  - Run live exchange, production identity or production-capital acceptance from fixture-mode browser tests.
changed_paths:
  - .github/workflows/portal-e2e-scheduled.yml
  - .github/workflows/portal-universal-e2e.yml
  - .github/workflows/portal-web.yml
  - .gitignore
  - ai_platform/portal/web/README.md
  - ai_platform/portal/web/e2e/**
  - ai_platform/portal/web/package.json
  - ai_platform/portal/web/playwright.config.ts
  - docs/ai_platform/portal/E2E_TEST_ARCHITECTURE.md
  - docs/ai_platform/portal/README.md
  - docs/agents/tasks/FTAI-20260727-portal-e2e-architecture.md
validation:
  - command: Portal Web CI 30310009901 on ff954336f5ac2b406fcd39aabf4c0802a5e8d37b
    result: PASS
    evidence: Typecheck, ESLint, production fixture build, Chromium install and complete chromium-desktop regression succeeded.
  - command: Portal Universal E2E 30310009820 on ff954336f5ac2b406fcd39aabf4c0802a5e8d37b
    result: PASS
    evidence: Deterministic backend scenario and critical Chromium browser journey succeeded.
  - command: AI Platform CI 30310009817
    result: PASS
    evidence: Python compilation, AI platform tests, Ruff, format, codespell and JSON validations succeeded.
  - command: Freqtrade CI 30310009791
    result: PASS
    evidence: Pre-commit, documentation build and CI Gate succeeded; unrelated core and online suites were correctly skipped by path classification.
  - command: GitHub Actions Security Analysis 30310009816
    result: PASS
    evidence: zizmor completed successfully for the final workflow definitions.
blockers: []
next_action: Observe the first scheduled nightly run and create a separate bounded repair task only if it exposes a reproducible cross-browser, accessibility, resilience or mobile defect.
```
