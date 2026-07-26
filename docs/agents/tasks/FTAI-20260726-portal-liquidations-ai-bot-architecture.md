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
updated_at: 2026-07-26T09:22:00+02:00
head: 8003de22b600a7c8f1a93f37bfbec367184ee59f
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
  - PR #320 Bot Operations merged as 7fc2dde2f40b31b23ef719109af6e54898b09102 and its closure PR #324 merged as fa4158db5073bcdab34d3a41eb0b9af196821513.
  - The existing Liquidations module is market-data and research preview only and carries trading_authorized false.
  - The Wick Hunter-inspired foundation remains a separate research track without a validated profitability or execution claim.
  - The new architecture document defines data, trust, synchronization, strategy, AI, risk, execution, testing and agent-handoff boundaries.
  - A versioned JSON manifest preserves current component identity, routes, paths, invariants, dependencies and revalidation requirements.
  - Stale read-model and UI checkpoints now record their completed merged state, and the completed Synology checkpoint routes future work through the canonical architecture.
  - PR #323 is current with develop and has no owned-path conflict with completed Bot Operations work.
derived:
  - Future agents can start from one source rather than reconstructing state from prompt, PR and task fragments.
  - The next legal strategy work starts with accepted dataset selection and a prospective deterministic replay contract, not order integration.
unknown:
  - Final current-head CI state for PR #323 after newline normalization.
  - Current mutable runtime state after the recorded develop deployment; every operational task must reverify it.
  - Current newest Liquid20 acceptance outcome.
conflicts: []
first_failure:
  marker: MISSING_FINAL_NEWLINES
  evidence: Freqtrade CI run 30192552953 failed only the pre-commit job because end-of-file-fixer identified five Markdown files without a final newline; documentation build, AI Platform CI and zizmor passed on the same head.
rejected_hypotheses:
  - Treat the portal page, collector availability or a completed data run as a validated trading strategy.
  - Add trading controls or execution authority to the Liquidations page.
  - Combine collection, replay, AI, DCA, leverage and live capital into one work package.
  - Let future agents rely on the historical implementation prompt instead of current repository state.
  - Change codespell or repository-wide pre-commit policy for a file-format defect.
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
    evidence: The machine-readable manifest is strict JSON with no comments or trailing commas.
  - command: AI Platform CI run 30192552967 on head 0d81ece6e7900e381392e6a561c61a213c68d82d
    result: PASS
    evidence: AI Platform validation completed successfully.
  - command: GitHub Actions Security Analysis run 30192552965 on head 0d81ece6e7900e381392e6a561c61a213c68d82d
    result: PASS
    evidence: Zizmor completed successfully.
  - command: Freqtrade CI run 30192552953 on head 0d81ece6e7900e381392e6a561c61a213c68d82d
    result: FAIL
    evidence: Documentation build passed; pre-commit failed only because five Markdown files lacked a final newline.
blockers: []
next_action: Normalize the remaining architecture file newline, run all required checks on the exact current head and squash-merge PR #323 only after success.
```
