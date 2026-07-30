---
task_id: FTAI-20260730-closure-ui-strategy-catalog
status: in_progress
branch: agent/closure-ui-strategy-catalog
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 819
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md
  - ai_platform/portal/web/app/bots/strategies/page.tsx
  - ai_platform/portal/web/app/api/strategy-catalog/route.ts
  - ai_platform/portal/web/app/api/strategy-catalog/[strategyVersion]/route.ts
  - ai_platform/portal/web/app/api/strategy-catalog/[strategyVersion]/rollback/route.ts
  - ai_platform/portal/web/components/strategy-catalog-client.tsx
  - ai_platform/portal/web/lib/strategy-catalog-api.ts
  - ai_platform/portal/web/lib/strategy-catalog-contracts.ts
  - ai_platform/portal/web/e2e/strategy-catalog-closure.spec.ts
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - ai_strategy_engine/TASKS.md
---

# Closure Strategy Catalog UI

## Goal

Replace the static summary table with the tenant-scoped, research-only catalog lifecycle defined by the frozen contracts.

## Delivered scope

- same-origin tenant-scoped catalog and detail BFF routes;
- immutable version history, provenance and approval reason codes;
- paper, dry-run and shadow deployment evidence with explicit no-live-capital authority;
- CSRF, session and MFA-gated rollback intent with source, target, audit reference and result evidence;
- loading, empty, stale, denied, failure, conflict and success states;
- responsive browser coverage for the critical lifecycle and authorization boundaries.

## Non-negotiable boundaries

- Browser traffic remains same-origin and cannot reach Freqtrade, exchanges or Vault directly.
- The UI does not redefine shared lifecycle schemas, generated clients, shell navigation or backend authorization.
- Approval does not grant execution authority.
- Deployment and rollback remain simulated, dry-run or shadow only.
- Repository fixture evidence is not external staging acceptance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T21:48:00+02:00
head: 4ee4ad5d5a7e62631185c662cddec77849f5e1eb
branch: agent/closure-ui-strategy-catalog
pr: 819
status: ci_pending
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md
  - ai_platform/portal/web/app/bots/strategies/page.tsx
  - ai_platform/portal/web/app/api/strategy-catalog/route.ts
  - ai_platform/portal/web/app/api/strategy-catalog/[strategyVersion]/route.ts
  - ai_platform/portal/web/app/api/strategy-catalog/[strategyVersion]/rollback/route.ts
  - ai_platform/portal/web/components/strategy-catalog-client.tsx
  - ai_platform/portal/web/lib/strategy-catalog-api.ts
  - ai_platform/portal/web/lib/strategy-catalog-contracts.ts
  - ai_platform/portal/web/e2e/strategy-catalog-closure.spec.ts
proven:
  - Shared contracts PR 781 merged as 6e489f7e10199120424cbcd01b3e125711630243 and freeze 549ba3afddba39ce455fce5eebbd4d67bea813a6 defines canonical history, approval, deployment, rollback and provenance contracts.
  - develop 9bb8edad795e122a2e513b354cd4aafa16d5917b was the branch base and open PRs 816 and 758 had no owned-path overlap.
  - Implementation head 4ee4ad5d5a7e62631185c662cddec77849f5e1eb changes only eight route-local implementation and browser-test paths before this checkpoint update.
  - Browser reads require the portal session; rollback additionally requires CSRF and mutation-capable identity state.
  - Fixture and API modes remain separated, and fixture provenance explicitly labels repository fixture evidence.
  - PR 819 is open against develop and requests Portal Web, browser, repository and security validation.
derived:
  - The owned routes can consume the frozen contracts without changing shared schemas or generated-client inputs.
  - No backend, shell, navigation, CI workflow or live-capital ownership transfer is required.
unknown:
  - Exact workflow run IDs and conclusions until PR 819 CI completes.
  - Exact merge commit until all required checks and review gates pass.
conflicts: []
first_failure:
  marker: NONE
  evidence: No implementation failure is recorded yet; PR CI is pending.
rejected_hypotheses:
  - Add approval or deployment authority to the browser.
  - Send browser requests directly to Freqtrade, an exchange or Vault.
  - Redefine frozen v2 lifecycle contracts in shared files.
  - Treat fixture rollback evidence as external staging acceptance.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md
  - ai_platform/portal/web/app/bots/strategies/page.tsx
  - ai_platform/portal/web/app/api/strategy-catalog/route.ts
  - ai_platform/portal/web/app/api/strategy-catalog/[strategyVersion]/route.ts
  - ai_platform/portal/web/app/api/strategy-catalog/[strategyVersion]/rollback/route.ts
  - ai_platform/portal/web/components/strategy-catalog-client.tsx
  - ai_platform/portal/web/lib/strategy-catalog-api.ts
  - ai_platform/portal/web/lib/strategy-catalog-contracts.ts
  - ai_platform/portal/web/e2e/strategy-catalog-closure.spec.ts
validation:
  - command: develop and open-PR ownership preflight
    result: PASS
    evidence: develop base 9bb8edad795e122a2e513b354cd4aafa16d5917b; PR 816 changes only a WickHunter request and PR 758 changes external preflight paths.
  - command: compare develop...agent/closure-ui-strategy-catalog
    result: PASS
    evidence: Implementation diff is ahead without divergence and remains inside the eight implementation/test owned paths before this checkpoint update.
  - command: PR 819 required CI
    result: PENDING
    evidence: Workflow runs are being created for exact branch head.
blockers: []
next_action: Inspect PR 819 exact-head CI and fix the first failing required check inside owned paths.
```
