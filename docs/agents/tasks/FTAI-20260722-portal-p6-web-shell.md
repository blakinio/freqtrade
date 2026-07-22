---
task_id: FTAI-20260722-portal-p6-web-shell
status: active
branch: feat/portal-p6-web-shell
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#135"
owned_paths:
  - ai_platform/portal/web/
  - .github/workflows/portal-web.yml
  - docs/ai_platform/portal/WEB_SHELL_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p6-web-shell.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - ai_platform/portal/control_plane/api.py
  - ai_platform/portal/contracts/bots.py
  - ai_platform/portal/contracts/environment.py
search_first:
  - current develop and open PRs or active tasks overlapping portal web ownership
  - existing frontend package/toolchain and Playwright configuration
  - canonical P1/P2 bot/environment API shapes
optional_reads:
  - only web-shell implementation-adjacent architecture files when a concrete blocker requires them
---

# AI Trading Portal P6 — Web Shell

## Goal

Implement the first production-oriented Next.js/React portal shell and core dry-run operations UX on top of canonical portal APIs without exposing Freqtrade or private control-plane origins to browser code.

## Deliverables

- isolated Next.js/React/TypeScript application under `ai_platform/portal/web/`;
- responsive application shell with primary navigation, topbar and explicit environment badge;
- Dashboard, Bots and Create Bot MVP routes;
- typed portal API/BFF client boundary aligned to canonical P1/P2 bot contracts;
- fail-closed API mode plus deterministic fixture mode for UI/E2E only;
- designed loading, empty, error and authorization-denied states;
- no browser-visible direct Freqtrade URL or API path;
- critical Chromium Playwright E2E for shell navigation and dry-run create-bot flow;
- dedicated web CI workflow for locked install, typecheck, lint/build and Chromium E2E;
- implementation documentation.

## Non-negotiable boundaries

- Browser code must never call Freqtrade REST/WebSocket or exchanges directly.
- Private control-plane origin stays server-side; browser calls only same-origin portal/BFF routes.
- Fixture mode is test/development evidence only and must not silently become the production default.
- Do not invent authentication headers that bypass the fail-closed P2 identity provider.
- Do not return or render exchange secrets.
- All initial bot creation remains `dry_run`/non-live; no live-capital authorization is added.
- Do not alter P1/P2/P3/P4/P5 contracts or implementation paths in P6.
- Do not copy third-party proprietary assets or private UI captures.
- Preserve frozen thresholds, completed Phase 6, protected final holdout and PyTorch/RL evidence boundaries.

## Acceptance criteria

1. Responsive shell exposes current environment clearly on every MVP route.
2. Dashboard renders health/attention summary with freshness semantics and deterministic state handling.
3. Bots view shows desired vs observed state and immutable strategy/model/config context.
4. Create Bot flow produces a canonical P2-compatible request and defaults to `dry_run`.
5. Browser source contains no Freqtrade endpoint or exchange-direct call path.
6. API mode fails closed when server-side portal API configuration is absent or unavailable.
7. Fixture mode is explicit and isolated to deterministic development/E2E use.
8. Loading, empty, error and denied states are intentional and testable.
9. Critical Chromium E2E covers shell navigation, create-bot success and rejection of non-dry-run creation.
10. Dedicated web CI, required repository CI and security analysis pass before merge.

## Validation

- Node dependency install from committed lockfile.
- TypeScript/typecheck and production build.
- Chromium Playwright E2E in explicit fixture mode.
- Repository CI and zizmor before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T21:40:00+02:00
head: c1e7070c51dcaf0309c717eb3ce1ddbd08796c8d
branch: feat/portal-p6-web-shell
pr: "#135"
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
owned_paths:
  - ai_platform/portal/web/
  - .github/workflows/portal-web.yml
  - docs/ai_platform/portal/WEB_SHELL_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p6-web-shell.md
proven:
  - P2 PR #116, P3 PR #118, P4 PR #119 and P5 PR #124 are merged to develop; P5 closeout PR #134 merged as b2811eac7d977eb880a80dd10ef094d48dbc2e45.
  - No prior package.json, Playwright configuration or ai_platform/portal/web implementation existed before P6.
  - P6 implements a responsive Next.js/React shell, Dashboard, Bots, Create Bot, explicit loading/error/denied/empty states and persistent environment visibility.
  - Browser mutations use same-origin /api/bots; private PORTAL_CONTROL_PLANE_URL is consumed only by server-side code.
  - API mode is the default and fails closed when private portal API configuration is missing; fixture mode requires explicit PORTAL_WEB_DATA_MODE=fixture.
  - Create-bot runtime validation accepts only a canonical non-empty P2-shaped request with execution_mode=dry_run and positive config/capital values.
  - Chromium E2E covers shell navigation, environment visibility, deterministic create-bot success, denied state and rejection of non-dry-run creation.
  - Initial Portal Web CI 29951461671 passed dependency resolution, generated package-lock v3, npm ci, typecheck, lint, Next production build, Chromium installation and all Playwright E2E.
  - Generated package-lock.json was committed by a bounded one-time bootstrap after checking out the exact PR head; the final workflow removed bootstrap writes and now uses permissions contents: read with npm ci only.
  - Local sandbox npm validation was unavailable because the internal npm mirror returned HTTP 503 and direct public registry DNS returned EAI_AGAIN; GitHub hosted runner validation is therefore the executable source of truth.
derived:
  - The server-side BFF preserves the private execution boundary while allowing later application session propagation without coupling browser bundles to private origins.
  - Fixture mode can support deterministic P6/P10 E2E without becoming an authentication or production-data fallback.
unknown: []
conflicts: []
first_failure:
  marker: lock-bootstrap-merge-ref
  evidence: Portal Web CI run 29951609305 generated the lockfile successfully but the temporary auto-commit step failed because the default pull_request checkout used the synthetic merge ref; targeting github.event.pull_request.head.sha resolved the bootstrap commit.
changed_paths:
  - .github/workflows/portal-web.yml
  - ai_platform/portal/web/
  - docs/ai_platform/portal/WEB_SHELL_FOUNDATION.md
  - docs/agents/tasks/FTAI-20260722-portal-p6-web-shell.md
validation:
  - command: Portal Web CI 29951461671
    result: PASS
    evidence: lock generation, npm ci, typecheck, lint, production build, Chromium install and Playwright E2E all passed.
  - command: Lockfile bootstrap
    result: PASS
    evidence: package-lock.json v3 is committed on PR #135 and final workflow is read-only npm ci.
blockers: []
next_action: Verify final read-only Portal Web CI, AI Platform CI, Freqtrade CI, zizmor and review state on PR #135; fix only concrete failures, then synchronize current develop and squash-merge P6 when all gates are green.
```
