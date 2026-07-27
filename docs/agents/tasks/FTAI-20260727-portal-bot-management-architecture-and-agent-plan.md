---
task_id: FTAI-20260727-portal-bot-management-architecture-and-agent-plan
status: active
branch: docs/portal-bot-management-architecture-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
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

## Deliverables

- dedicated bot-management product architecture;
- target additive file and directory structure;
- canonical policy, command, execution and reconciliation boundaries;
- package sequence from BM-00 through BM-09 while preserving PI-07 and PI-08 gates;
- multi-agent ownership matrix;
- serial shared-contract, migration and integration rules;
- portal README documentation map update.

## Non-negotiable boundaries

- documentation and planning only;
- no runtime, API, migration, deployment or browser behavior changes;
- no activation of PI-05, PI-07, PI-08, P11 or P14;
- no live-capital authorization;
- no proprietary third-party code or assets;
- no weakening of identity, tenant, risk, audit, credential or reconciliation boundaries;
- do not overlap active PI-06 Synology target-preflight paths in PR #431.

## Acceptance criteria

1. The architecture defines complete dry-run bot creation and management capabilities without claiming current implementation.
2. The target repository structure gives feature agents disjoint primary ownership.
3. Shared hot paths have one integration owner.
4. One contract agent is required before parallel implementation.
5. PI-07 precedes PI-08 activation.
6. Command success requires authoritative reconciliation.
7. The plan states an explicit recommended concurrency and stop conditions.
8. README links the new canonical documents.

## Validation

- inspect current open PR ownership;
- verify all references and package dependencies are internally consistent;
- confirm documentation-only changed paths;
- review diff for accidental completion or authorization claims.

## Context checkpoint

- Current portal software foundation and Bot Operations are complete for their bounded scopes.
- Real bot product completeness still requires richer configuration policies, exchange connection workflows, PI-07 credential brokering, PI-08 private dry-run submission, position/order commands and full E2E closure.
- PR #431 owns only PI-06 Synology target-preflight workflow, script, tests and documentation; this task uses disjoint documentation paths.
- The recommended model is one BM-00 contract lead, then five to six parallel feature agents plus one shared integration owner and one E2E owner.
- The new architecture does not activate implementation packages automatically.

next_action: Open the documentation PR, record its number here, and verify the changed-file set contains only the four declared documentation paths.
