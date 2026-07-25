---
task_id: FTAI-20260725-portal-liquidations-ui
status: reviewing
branch: feat/portal-liquidations-ui-20260725
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
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
updated_at: 2026-07-25T23:00:00Z
head: c54b0659173da24cb269fbd1779b895ea310b95a
branch: feat/portal-liquidations-ui-20260725
pr: 311
status: reviewing
context_routes:
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
  - PR 307 was merged to develop as aa2f193b970588e478b5d57f58d2ddfd7f4aab67 and owns the versioned bounded read-model.
  - Same-origin BFF routes expose only versioned event, summary and health contracts and return safe 422, 503 or 500 errors.
  - The Likwidacje page provides source, symbol, side and time-range filters; 5m, 1h and 24h summaries; recent events; symbol ranking; source semantics; and explicit live, stale, historical and acceptance-failed states.
  - The browser receives no collector path, Docker socket, exchange credential, trading credential or execution authority.
  - Responsive navigation and the liquidation page remain within a 390 px viewport; table overflow is contained locally.
  - The final branch contains no temporary diagnostic workflow.
derived:
  - The Synology deployment package may mount the authoritative Liquid20 root read-only and configure PORTAL_LIQUIDATIONS_DATA_ROOT without changing this UI package.
unknown:
  - Final acceptance result of the active Liquid20 retry liquid20-20260725T212201Z-1.
conflicts: []
first_failure:
  marker: MOBILE_SIDEBAR_MIN_CONTENT
  evidence: Focused Playwright diagnostics identified the responsive aside.sidebar as the unclipped overflow source; min-content constraints on the shell, sidebar and navigation resolved it.
rejected_hypotheses:
  - Direct browser reads from Synology files, Liquid20 collector or Freqtrade.
  - Trading actions, recommendations or signal language on the liquidation page.
  - The liquidation table or acceptance gate token was the root cause of mobile document overflow.
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
  - command: Portal Web CI run 30178394146
    result: PASS
    evidence: TypeScript, ESLint, production Next.js build and Playwright web tests passed.
  - command: Portal Universal E2E run 30178394118
    result: PASS
    evidence: Universal Chromium portal tests passed.
  - command: AI Platform CI run 30178394115
    result: PASS
    evidence: AI Platform checks passed.
  - command: Freqtrade CI run 30178394105
    result: PASS
    evidence: Repository pre-commit and test gates passed.
  - command: zizmor run 30178394117
    result: PASS
    evidence: GitHub Actions security analysis passed.
blockers: []
next_action: Re-run the final documentation-only commit checks, verify review threads are empty and squash-merge PR 311.
```
