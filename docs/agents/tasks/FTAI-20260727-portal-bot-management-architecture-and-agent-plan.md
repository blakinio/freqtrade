---
task_id: FTAI-20260727-portal-bot-management-architecture-and-agent-plan
status: done
branch: develop
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#438"
owned_paths:
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/README.md
  - docs/agents/tasks/FTAI-20260727-portal-bot-management-architecture-and-agent-plan.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
search_first:
  - current develop and open PRs
  - overlapping portal documentation and architecture ownership
---

# Bot management architecture and agent plan

## Goal

Define the product architecture, target repository structure, bounded package dependencies and safe multi-agent ownership model required to complete dry-run bot creation and bot management beyond the current portal foundation.

## Delivered

- dedicated bot-management product architecture;
- target additive file and directory structure;
- canonical policy, command, execution and reconciliation boundaries;
- package sequence from BM-00 through BM-09 while preserving PI-07 and PI-08 gates;
- multi-agent ownership matrix;
- serial shared-contract, migration and integration rules;
- portal README documentation map update.

## Non-negotiable boundaries preserved

- documentation and planning only;
- no runtime, API, migration, deployment or browser behavior changes;
- no activation of PI-05, PI-07, PI-08, P11 or P14;
- no live-capital authorization;
- no proprietary third-party code or assets;
- no weakening of identity, tenant, risk, audit, credential or reconciliation boundaries;
- no overlap with PI-06 Synology target-preflight paths.

## Acceptance result

1. Complete dry-run bot creation and management capabilities are defined without claiming current implementation.
2. Target repository paths provide disjoint feature ownership.
3. Shared hot paths have one integration owner.
4. BM-00 is the required serial contract package before parallel implementation.
5. PI-07 precedes PI-08.
6. Command success requires authoritative reconciliation.
7. Recommended concurrency and stop conditions are explicit.
8. The portal README links both canonical documents.

## Validation evidence

- PR #438 contained exactly four declared documentation paths.
- AI Platform CI run 1829: success.
- GitHub Actions Security Analysis run 2098: success.
- Freqtrade CI run 2235: Documentation build and final CI Gate succeeded; code/test matrix jobs were correctly skipped for documentation-only scope.
- Squash merge: `3076b9aee049bc1b293af57e12bca1b18e717ad1`.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T10:40:00+02:00
head: 3076b9aee049bc1b293af57e12bca1b18e717ad1
branch: develop
pr: "#438"
status: done
proven:
  - The bot-management product architecture and agent ownership plan are merged.
  - BM-00 is the mandatory first serial implementation package.
  - Five to six feature agents may run in parallel only after BM-00 contracts merge.
  - PI-07, PI-08, P11 and P14 retain separate gates.
derived:
  - Downstream feature agents must consume merged BM-00 contracts rather than define local competing schemas.
unknown: []
conflicts: []
first_failure:
  marker: null
  evidence: null
rejected_hypotheses:
  - Start all feature agents before shared contracts are frozen.
  - Combine credential brokering, order submission and live-capital work.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-portal-bot-management-architecture-and-agent-plan.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_PRODUCT_ARCHITECTURE.md
  - docs/ai_platform/portal/BOT_MANAGEMENT_AGENT_PLAN.md
  - docs/ai_platform/portal/README.md
validation:
  - command: PR #438 required CI
    result: PASS
    evidence: AI Platform CI, security analysis, Documentation build and final CI Gate succeeded.
  - command: squash merge
    result: PASS
    evidence: develop commit 3076b9aee049bc1b293af57e12bca1b18e717ad1.
blockers: []
next_action: Execute BM-00 shared bot-management contracts on `feat/portal-bm00-shared-contracts` without starting downstream feature implementation.
```

next_action: Execute BM-00 shared bot-management contracts on `feat/portal-bm00-shared-contracts` without starting downstream feature implementation.
