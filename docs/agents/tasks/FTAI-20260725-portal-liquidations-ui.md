---
task_id: FTAI-20260725-portal-liquidations-ui
status: implementing
branch: feat/portal-liquidations-ui-20260725
base_branch: feat/portal-liquidations-read-model-20260725
created: 2026-07-25
updated: 2026-07-25
related_pr: ""
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
updated_at: 2026-07-25T22:15:00Z
head: feba6da71b4e201685ce701b6a1b415b907bc0ff
branch: feat/portal-liquidations-ui-20260725
pr: none
status: implementing
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
  - PR 307 contains the versioned bounded server-side read-model and fixtures.
  - The current Synology portal preview is a standalone Next.js application in fixture mode on private LAN port 3031.
  - Browser clients must access liquidation data only through same-origin portal BFF routes.
derived:
  - This package can be stacked on PR 307 while its required checks are queued, then retargeted to develop after PR 307 merges.
unknown:
  - Final CI outcome for PR 307.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - Direct browser reads from Synology files, Liquid20 collector or Freqtrade.
  - Trading actions, recommendations or signal language on the liquidation page.
changed_paths:
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-ui.md
validation:
  - command: stacked task declaration
    result: PASS
    evidence: UI ownership excludes deployment paths and preserves PR 307 as the read-model dependency.
blockers: []
next_action: Implement same-origin BFF handlers and the responsive Likwidacje page using only the versioned read-model contracts.
```
