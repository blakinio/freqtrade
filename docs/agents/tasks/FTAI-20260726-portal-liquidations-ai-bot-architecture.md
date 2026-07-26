---
task_id: FTAI-20260726-portal-liquidations-ai-bot-architecture
status: done
branch: develop
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
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/liquidations-ai-bot-architecture-v1.json
search_first:
  - current develop head and open PR ownership
  - current Liquid20 collector, portal image, newest run and completed acceptance report
optional_reads:
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
---

# Portal Liquidations and AI bot architecture

## Goal

Create one canonical human-readable and machine-readable continuation contract that separates the Liquid20 collector, the read-only portal module, the Wick Hunter-inspired research track and a future AI bot, while repairing stale Liquidations checkpoints.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T09:35:00+02:00
head: a86c955a1138e7fad1393a38f6a4406e6701f868
branch: develop
pr: 323
status: done
context_routes:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/liquidations-ai-bot-architecture-v1.json
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
proven:
  - PR #307 merged the bounded Liquid20 read-model as aa2f193b970588e478b5d57f58d2ddfd7f4aab67.
  - PR #311 merged the same-origin BFF and responsive Likwidacje UI as 228b5ad3eb12c6adab300ab86461d3fa67acaa47.
  - PR #313 merged the Synology read-only integration as 1bf106fb5919706cca4db4f8245e00d2a1932df9.
  - Real-data deployment runs 30191045808 and 30191687921 passed their declared Synology checks.
  - PR #320 Bot Operations and closure PR #324 were already merged and their current documentation state was preserved.
  - PR #323 squash-merged to develop as a86c955a1138e7fad1393a38f6a4406e6701f868.
  - The canonical document covers current data flow, source semantics, evidence layout, read-model, BFF/UI, Synology, authority, synchronization, features, deterministic strategy, optional AI, risk, execution, observability, tests and LQ-02 through LQ-09 expansion order.
  - The versioned JSON manifest preserves machine-readable routes, paths, limits, invariants, lifecycle, dependencies and mandatory runtime revalidation.
  - ADR-017 records that the Liquidations portal surface is read-only research preview and cannot create signals, intents, orders, model promotion or capital authority.
  - Read-model and UI task records now show their completed merged state; the Synology task routes future work through the canonical architecture.
  - The first legal strategy package is accepted dataset selection followed by a prospectively frozen deterministic replay contract.
derived:
  - A working portal page or collector does not validate a strategy, model or acceptance result.
  - AI remains optional and must beat or materially improve a deterministic baseline under identical frozen evidence and execution assumptions.
  - DCA, TP, SL, leverage, order submission and live capital remain separate owner-gated packages.
unknown:
  - Current running portal image after later deployments.
  - Current collector image, newest run ID and newest completed acceptance result.
  - Whether a replay dataset has since been frozen.
conflicts: []
first_failure:
  marker: MISSING_FINAL_NEWLINES
  evidence: Freqtrade CI run 30192552953 failed only end-of-file-fixer on five Markdown files; no semantic, documentation-build, codespell or security defect was present.
rejected_hypotheses:
  - Treat portal availability or a completed collection run as a validated trading strategy.
  - Add trading controls or execution authority to the Liquidations page.
  - Combine collection, replay, AI, DCA, leverage and live capital into one package.
  - Change repository-wide pre-commit policy for a local file-format defect.
  - Rely on the historical implementation prompt instead of current repository state.
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
  - command: AI Platform CI run 30192963570 on PR #323 head 01f689820747e8085821cc36f5d2c103a964415a
    result: PASS
    evidence: AI Platform validation completed successfully.
  - command: Freqtrade CI run 30192963562 on PR #323 head 01f689820747e8085821cc36f5d2c103a964415a
    result: PASS
    evidence: Scope classification, pre-commit, documentation build and CI Gate passed; unrelated core and compatibility jobs were correctly skipped for documentation-only scope.
  - command: GitHub Actions Security Analysis run 30192963563 on PR #323 head 01f689820747e8085821cc36f5d2c103a964415a
    result: PASS
    evidence: Zizmor completed successfully.
  - command: PR #323 review state
    result: PASS
    evidence: No inline review threads or submitted reviews remained before squash merge.
blockers: []
next_action: Before LQ-02, perform a fresh runtime preflight and require a completed acceptance report with explicit passed true for performance research; otherwise keep failed evidence diagnostic-only.
```
