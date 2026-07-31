---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: active
dispatch_state: READY
project_lane: freqtrade-portal
branch: agent/closure-ui-signal-wizard-implementation-20260731
base_branch: develop
created: 2026-07-30
updated: 2026-07-31
related_pr: 818
terminal_pr: 820
unblock_pr: 830
correlation_blocker_pr: 832
correlation_repair_pr: 846
backend_task: FTAI-20260730-closure-signal-wizard-backend
backend_pr: 825
backend_merge: 0bc35521debd33312820dfad9f010e22aa651610
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - FTAI-20260730-closure-signal-wizard-backend merged as 0bc35521debd33312820dfad9f010e22aa651610
  - FTAI-20260731-signal-wizard-context-repair merged through PR 846 as 367a51b610d2a34ee5841bc0b86622bd64fc6858
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - ai_platform/portal/web/app/ai/signal-wizard/page.tsx
  - ai_platform/portal/web/app/ai/signal-wizard/signal-wizard-client.tsx
  - ai_platform/portal/web/app/api/ai/signal-wizard/preview/route.ts
  - ai_platform/portal/web/app/api/ai/signal-wizard/submit/route.ts
  - ai_platform/portal/web/lib/signal-wizard-api.ts
  - ai_platform/portal/web/lib/signal-wizard-contracts.ts
  - ai_platform/portal/web/e2e/signal-wizard-closure.spec.ts
  - ai_platform/portal/web/e2e/specs/ai/signal-wizard-closure.spec.ts
required_reads:
  - AGENTS.md
  - docs/agents/AGENTS.md
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - ai_strategy_engine/TASKS.md
---

# Closure Signal Wizard UI

## Goal

Build the complete research-only Signal Wizard against the frozen typed DSL and the canonical Signal Wizard backend/API.

## Resolved dependency chain

- PR #825 merged durable tenant-scoped `/v1/signal-wizard/preview` and `/submit` services.
- PR #832 correctly proved that the identity-enabled boundary could not expose fresh upstream HTTP correlation identifiers before BFF command construction.
- PR #846 merged the canonical repair: authenticated server-side command correlation is derived deterministically from trusted tenant, actor, operation and normalized idempotency key.
- PR #846 covers real identity-enabled login/CSRF, preview retry, submit retry and actor mismatch rejection, so browser/BFF code no longer predicts or supplies authoritative correlation.
- Duplicate PR #844 and stale coordinator PR #851 were closed without merge after PR #846 became canonical.
- Current Playwright configuration discovers tests only under `e2e/specs`; the route-local discoverable test path is therefore added to ownership after live no-overlap verification. The original reserved root test path remains untouched.

## Context checkpoint

```yaml
checkpoint_version: 1
project_lane: freqtrade-portal
phase: implement
session_id: chat-github-20260731-signal-wizard-frontend
execution_mode: chat-github
execution_reason: The sandbox cannot resolve github.com for a checkout; route-local implementation is performed through the GitHub connector and validated by exact-head Portal/browser CI.
updated_at: 2026-07-31T09:38:00+02:00
lease_expires_at: 2026-07-31T10:23:00+02:00
head: 367a51b610d2a34ee5841bc0b86622bd64fc6858
branch: agent/closure-ui-signal-wizard-implementation-20260731
pr: pending
status: active
proven:
  - Shared contracts PR 781 and canonical backend PR 825 are merged.
  - Context repair PR 846 is merged as 367a51b610d2a34ee5841bc0b86622bd64fc6858.
  - The canonical backend accepts only approved Feature Registry entries, validates parameters and typed condition AST, emits leakage warnings, persists previews and creates research experiment intents without execution or promotion authority.
  - PR 846 provides stable authenticated command correlation and durable retry semantics through the identity-enabled control plane.
  - No open PR owns any Signal Wizard frontend implementation path.
  - Playwright testDir is e2e/specs, so the prior reserved root spec path is not browser-discoverable.
derived:
  - The route-local BFF can construct tenant and actor context from the authenticated session while the backend binds authoritative command correlation.
  - Browser traffic can remain same-origin and never address Freqtrade, exchanges or Vault.
  - A discoverable route-local spec under e2e/specs/ai is required for real Portal Web CI coverage.
unknown:
  - Exact-head frontend typecheck, build and Chromium conclusions.
conflicts: []
first_failure:
  marker: NONE
  evidence: All production dependencies required for route-local implementation are merged and no ownership overlap exists.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
validation:
  - command: Live backend and identity-enabled repair inventory
    result: PASS
    evidence: PRs 825 and 846 are merged and cover durable preview/submit plus stable authenticated correlation/retries.
  - command: Open PR ownership comparison
    result: PASS
    evidence: No open PR touches any route-local Signal Wizard frontend path after stale PR 851 was closed unmerged.
  - command: Playwright discovery review
    result: PASS
    evidence: playwright.config.ts sets testDir to e2e/specs; the discoverable AI spec path is now explicitly owned.
blockers: []
next_action: Implement the same-origin approved-feature selection, constrained preview and experiment submission flow with route-local browser coverage.
```
