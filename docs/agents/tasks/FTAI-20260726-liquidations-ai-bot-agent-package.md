---
task_id: FTAI-20260726-liquidations-ai-bot-agent-package
status: done
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#335"
owned_paths:
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/ai_platform/portal/examples/liquidations-dataset-selection-v1.example.json
  - docs/ai_platform/portal/examples/liquidations-replay-request-v1.example.json
  - docs/ai_platform/portal/examples/liquidations-decision-snapshot-v1.example.json
  - docs/agents/prompts/FTAI_LIQUIDATIONS_AI_BOT_NEXT_AGENT.md
  - docs/agents/tasks/FTAI-20260726-liquidations-ai-bot-agent-package.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/liquidations-ai-bot-architecture-v1.json
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
search_first:
  - current develop head and open PR path ownership
  - current Liquid20 collector, latest completed acceptance report and candle evidence before starting LQ-02
optional_reads:
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
---

# Liquidations AI bot agent package

## Goal

Create a practical continuation package for future agents: target repository layout, artifact contracts, valid JSON examples, package ownership boundaries, validation gates and a ready-to-paste LQ-02 prompt.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T10:25:00+02:00
head: d1e728690fb74b346f1ffe61265281feab810e6b
branch: develop
pr: 335
status: done
context_routes:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/agents/prompts/FTAI_LIQUIDATIONS_AI_BOT_NEXT_AGENT.md
proven:
  - PR #335 squash-merged to develop as d1e728690fb74b346f1ffe61265281feab810e6b.
  - The package adds a dependency-ordered implementation blueprint for LQ-02 through LQ-07 without creating the future code tree prematurely.
  - The machine-readable artifact manifest defines DatasetSelectionManifest, ReplayRequest, ReplayEvidenceReport, DecisionSnapshot, SignalObservationReport, ModelCandidateEvidence and ApprovedDryRunIntent.
  - Valid JSON examples exist for dataset selection, replay request and decision snapshot.
  - The ready-to-paste next-agent prompt starts only LQ-02 accepted dataset selection and contains explicit stop conditions for missing accepted evidence or versioned candles.
  - Existing canonical LiquidationEvent, deterministic event identity, conservative alignment, pure counter-trade policy, source adapters, acceptance contracts and read-only portal boundaries remain unchanged.
  - Exact PR head 4a2fe259bee5af91cc3639d54758798642db6d50 passed AI Platform CI 30193517992, Freqtrade CI 30193517927, pre-commit, documentation build, CI Gate and zizmor 30193518002.
derived:
  - Future agents have one practical file map and artifact vocabulary instead of reconstructing them from dispersed documents.
  - Replay, strategy, AI and execution remain gated behind accepted immutable data and versioned candle evidence.
unknown:
  - Current mutable Synology collector image, newest run and newest completed acceptance result.
  - Whether valid versioned candle evidence currently exists for an accepted interval.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Create the entire target directory tree before each package is declared.
  - Start replay or model work before accepted data and candle evidence are frozen.
  - Add trading controls to the read-only Liquidations portal page.
  - Treat AI output as execution authority.
  - Enable DCA, leverage or live capital in the continuation package.
changed_paths:
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/ai_platform/portal/examples/liquidations-dataset-selection-v1.example.json
  - docs/ai_platform/portal/examples/liquidations-replay-request-v1.example.json
  - docs/ai_platform/portal/examples/liquidations-decision-snapshot-v1.example.json
  - docs/agents/prompts/FTAI_LIQUIDATIONS_AI_BOT_NEXT_AGENT.md
  - docs/agents/tasks/FTAI-20260726-liquidations-ai-bot-agent-package.md
validation:
  - command: AI Platform CI run 30193517992 on head 4a2fe259bee5af91cc3639d54758798642db6d50
    result: PASS
    evidence: AI Platform tests, lint, format, codespell and JSON validation completed successfully.
  - command: Freqtrade CI run 30193517927 on head 4a2fe259bee5af91cc3639d54758798642db6d50
    result: PASS
    evidence: Scope classification, pre-commit, documentation build and CI Gate passed; unrelated core jobs were correctly skipped for documentation-only scope.
  - command: GitHub Actions Security Analysis run 30193518002 on head 4a2fe259bee5af91cc3639d54758798642db6d50
    result: PASS
    evidence: Zizmor completed successfully.
  - command: PR #335 review state
    result: PASS
    evidence: No inline review threads remained before squash merge.
blockers: []
next_action: Start LQ-02 only after a fresh develop/open-PR/runtime preflight; require a completed Liquid20 report with explicit passed true and valid versioned candle evidence, otherwise record the exact blocker and do not start replay.
```
