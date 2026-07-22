---
task_id: FTAI-20260722-portal-p6-web-shell
status: active
branch: feat/portal-p6-web-shell
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: null
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
- dedicated web CI workflow for install, typecheck, lint/build and Chromium E2E;
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
9. Critical Chromium E2E covers shell navigation and create-bot success in fixture mode.
10. Dedicated web CI, required repository CI and security analysis pass before merge.

## Validation

- Node dependency install from lockfile.
- TypeScript/typecheck and production build.
- Chromium Playwright E2E in explicit fixture mode.
- Repository CI and zizmor before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T21:15:38+02:00
head: b2811eac7d977eb880a80dd10ef094d48dbc2e45
branch: feat/portal-p6-web-shell
pr: null
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
  - P2 PR #116, P3 PR #118, P4 PR #119 and P5 PR #124 are merged to develop.
  - P5 durable closeout PR #134 merged as b2811eac7d977eb880a80dd10ef094d48dbc2e45.
  - No existing package.json, Playwright configuration or ai_platform/portal/web implementation was found in repository search.
  - Canonical P2 API exposes POST/GET /v1/bots, GET /v1/bots/{bot_id}, POST revisions and POST desired-state operations behind a fail-closed identity dependency.
  - Canonical BotSpec requires tenant, strategy/model/risk/exchange references, pair universe, timeframe, capital allocation/currency, runtime version, config revision, environment and execution mode.
  - Portal architecture requires browser -> portal boundary only; browser -> Freqtrade and browser -> data plane are denied.
  - UI architecture requires persistent environment visibility and designed loading/empty/error/denied states.
  - Next.js 16.2 is the active LTS line after the July 2026 security release; React latest stable major is 19.2; Playwright current release line is 1.61.
derived:
  - P6 can use explicit fixture mode for deterministic E2E while keeping production API mode fail-closed and server-side.
  - A same-origin BFF route is required for browser mutations so private portal API origins are not embedded in client bundles.
unknown:
  - Final package-manager lockfile resolution until executable Node install runs in CI or local runtime.
conflicts: []
first_failure:
  marker: none
  evidence: No P6 executable validation has run yet.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-portal-p6-web-shell.md
validation: []
blockers: []
next_action: Scaffold the isolated Next.js web application with server-only API boundary, explicit fixture mode, responsive shell and Dashboard/Bots/Create Bot MVP routes before adding Chromium E2E and web CI.
```
