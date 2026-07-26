---
task_id: FTAI-20260725-portal-liquidations-ui
status: done
branch: develop
base_branch: develop
created: 2026-07-25
updated: 2026-07-26
related_pr: "#311"
owned_paths:
  - ai_platform/portal/web/app/api/market/liquidations/
  - ai_platform/portal/web/app/market/liquidations/
  - ai_platform/portal/web/components/liquidations-dashboard.tsx
  - ai_platform/portal/web/components/liquidations-dashboard.module.css
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/e2e/liquidations.spec.ts
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-ui.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
search_first:
  - active portal and Liquid20 pull requests
optional_reads: []
---

# Portal Liquidations API and UI

## Goal

Expose the bounded Liquid20 read-model through server-side portal BFF routes and add a responsive, read-only Likwidacje surface with filters, summaries, rankings, source semantics and truthful acceptance states.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T07:04:00Z
head: 228b5ad3eb12c6adab300ab86461d3fa67acaa47
branch: develop
pr: "#311"
status: done
context_routes:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
owned_paths:
  - ai_platform/portal/web/app/api/market/liquidations/
  - ai_platform/portal/web/app/market/liquidations/
  - ai_platform/portal/web/components/liquidations-dashboard.tsx
  - ai_platform/portal/web/components/liquidations-dashboard.module.css
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/e2e/liquidations.spec.ts
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-ui.md
proven:
  - PR #307 merged the versioned bounded read-model as aa2f193b970588e478b5d57f58d2ddfd7f4aab67.
  - PR #311 merged the same-origin BFF and responsive Likwidacje UI as 228b5ad3eb12c6adab300ab86461d3fa67acaa47.
  - GET /api/market/liquidations exposes bounded source, symbol, side, time, limit and cursor queries.
  - GET /api/market/liquidations/summary exposes exact 5m, 1h and 24h source-labelled aggregates and symbol ranking.
  - GET /api/market/liquidations/health exposes freshness, current and latest completed acceptance, source health and no-trading invariants.
  - The page provides filters, summaries, recent events, rankings, source semantics and explicit loading, empty, stale, unavailable, historical and acceptance-failed states.
  - The browser receives no collector path, Docker socket, exchange credential, trading credential, signal or execution authority.
  - Responsive navigation and the page remain bounded at a 390 px viewport.
  - Portal Web CI, Portal Universal E2E, AI Platform CI, Freqtrade CI and zizmor passed on the final PR head.
derived:
  - The UI is a read-only research-preview product surface and cannot be used as proof of strategy or model validation.
  - Future strategy/model controls must use separate lifecycle and execution contracts rather than adding trade actions to this page.
unknown: []
conflicts: []
first_failure:
  marker: MOBILE_SIDEBAR_MIN_CONTENT
  evidence: Focused Playwright diagnostics identified the responsive sidebar min-content constraint as the overflow source; bounded shell, sidebar and navigation sizing resolved it.
rejected_hypotheses:
  - Direct browser reads from Synology files, Liquid20 collector, exchanges or Freqtrade.
  - Trading actions, recommendations or signal language on the Liquidations page.
  - Cross-source deduplication or unlabeled volume claims.
  - Present fixture evidence as operational live data.
changed_paths:
  - ai_platform/portal/web/app/api/market/liquidations/_shared.ts
  - ai_platform/portal/web/app/api/market/liquidations/route.ts
  - ai_platform/portal/web/app/api/market/liquidations/health/route.ts
  - ai_platform/portal/web/app/api/market/liquidations/summary/route.ts
  - ai_platform/portal/web/app/market/liquidations/page.tsx
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/components/liquidations-dashboard.tsx
  - ai_platform/portal/web/components/liquidations-dashboard.module.css
  - ai_platform/portal/web/e2e/liquidations.spec.ts
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-ui.md
validation:
  - command: Portal Web CI run 30178483845
    result: PASS
    evidence: TypeScript, ESLint, production build and browser tests passed.
  - command: Portal Universal E2E run 30178483846
    result: PASS
    evidence: Universal Chromium portal tests passed.
  - command: AI Platform CI run 30178483852
    result: PASS
    evidence: AI Platform checks passed.
  - command: Freqtrade CI run 30178483863
    result: PASS
    evidence: Repository pre-commit and test gates passed.
  - command: GitHub Actions Security Analysis run 30178483850
    result: PASS
    evidence: Zizmor completed successfully.
blockers: []
next_action: Use docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md before declaring any new Liquid20 portal, replay, strategy, AI-model or execution package.
```