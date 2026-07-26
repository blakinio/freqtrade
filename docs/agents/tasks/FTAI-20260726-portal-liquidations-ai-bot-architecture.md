---
task_id: FTAI-20260726-portal-liquidations-ai-bot-architecture
status: reviewing
branch: docs/portal-liquidations-ai-bot-architecture-20260726
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#323"
owned_paths:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/liquidations-ai-bot-architecture-v1.json
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-ui.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-synology.md
  - docs/agents/tasks/FTAI-20260726-portal-liquidations-ai-bot-architecture.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/AI_ML_AND_LEARNING_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
search_first:
  - current develop head and open PR ownership
  - merged Liquid20 collector, portal and Synology packages
  - current Liquid20 runtime and acceptance evidence before any operational claim
optional_reads:
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
---

# Portal Liquidations and AI bot architecture

## Goal

Create one canonical human-readable and machine-readable architecture and continuation contract that separates the Liquid20 collector, the read-only portal module, the Wick Hunter-inspired research strategy and a future AI bot, while repairing stale portal-liquidation checkpoints.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T07:11:00Z
head: c44358a310455c6c6589eac8011d6a02a1856f10
branch: docs/portal-liquidations-ai-bot-architecture-20260726
pr: 323
status: reviewing
context_routes:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/liquidations-ai-bot-architecture-v1.json
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
owned_paths:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/liquidations-ai-bot-architecture-v1.json
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-ui.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-synology.md
  - docs/agents/tasks/FTAI-20260726-portal-liquidations-ai-bot-architecture.md
proven:
  - PR #307 merged the bounded read-model as aa2f193b970588e478b5d57f58d2ddfd7f4aab67.
  - PR #311 merged the same-origin BFF and Likwidacje UI as 228b5ad3eb12c6adab300ab86461d3fa67acaa47.
  - PR #313 merged the Synology read-only integration as 1bf106fb5919706cca4db4f8245e00d2a1932df9.
  - Authoritative develop deployment run 30191687921 passed for the merged Synology integration.
  - The existing portal module is market-data and research preview only and carries trading_authorized false.
  - The Wick Hunter-inspired foundation remains a separate research track without a validated profitability or execution claim.
  - The new architecture document defines data, trust, synchronization, strategy, AI, risk, execution, testing and agent-handoff boundaries.
  - A versioned JSON manifest preserves current component identity, routes, paths, invariants, dependencies and revalidation requirements.
  - Stale read-model and UI checkpoints now record their completed merged state, and the completed Synology checkpoint routes future work through the canonical architecture.
  - PR #323 is open as a documentation-only review package with no overlap with open Bot Operations PR #320.
derived:
  - Future agents can start from one source rather than reconstructing state from prompt, PR and task fragments.
  - The next legal strategy work starts with accepted dataset selection and a prospective deterministic replay contract, not order integration.
unknown:
  - Final CI state for PR #323 current head.
  - Current mutable runtime state after the recorded develop deployment; every operational task must reverify it.
  - Current newest Liquid20 acceptance outcome.
conflicts:
  - Open PR #320 owns bot-operation implementation paths and its own task record; this documentation package has no owned-path overlap.
first_failure:
  marker: none
  evidence: Repository source documents and merged implementation records were consistent after stale task states were identified.
rejected_hypotheses:
  - Treat the portal page, collector availability or a completed data run as a validated trading strategy.
  - Add trading controls or execution authority to the Liquidations page.
  - Combine collection, replay, AI, DCA, leverage and live capital into one work package.
  - Let future agents rely on the historical implementation prompt instead of current repository state.
changed_paths:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/liquidations-ai-bot-architecture-v1.json
  - docs/ai_platform/portal/LIQUIDATIONS_READ_MODEL.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-ui.md
  - docs/agents/tasks/FTAI-20260725-portal-liquidations-synology.md
  - docs/agents/tasks/FTAI-20260726-portal-liquidations-ai-bot-architecture.md
validation:
  - command: live repository and PR preflight
    result: PASS
    evidence: Current merged Liquid20 portal packages, exact merge SHAs, current open PR ownership, source contracts and deployment checkpoint were inspected before writing.
  - command: JSON structure review
    result: PASS
    evidence: The machine-readable manifest was authored as strict JSON with no comments or trailing commas.
blockers: []
next_action: Require current-head repository CI on PR #323 and squash-merge only after all required checks pass.
```