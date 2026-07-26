---
task_id: FTAI-20260726-liquidations-ai-bot-agent-package
status: reviewing
branch: docs/liquidations-ai-bot-agent-package-20260726
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: null
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
updated_at: 2026-07-26T10:05:00+02:00
head: c937633fad9b766702be272cee04e8f7eaa31aa8
branch: docs/liquidations-ai-bot-agent-package-20260726
pr: null
status: reviewing
context_routes:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/agents/prompts/FTAI_LIQUIDATIONS_AI_BOT_NEXT_AGENT.md
owned_paths:
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/ai_platform/portal/examples/liquidations-dataset-selection-v1.example.json
  - docs/ai_platform/portal/examples/liquidations-replay-request-v1.example.json
  - docs/ai_platform/portal/examples/liquidations-decision-snapshot-v1.example.json
  - docs/agents/prompts/FTAI_LIQUIDATIONS_AI_BOT_NEXT_AGENT.md
  - docs/agents/tasks/FTAI-20260726-liquidations-ai-bot-agent-package.md
proven:
  - develop HEAD at declaration was bff49117b6572a065527ba75127c9aa938bf3119.
  - Open PR #334 owns only docs/agents/tasks/FTAI-20260726-portal-pi06-identity-decision.md and does not overlap this package.
  - The canonical architecture and machine-readable v1 architecture manifest already exist on develop.
  - Existing code provides canonical LiquidationEvent, deterministic source event identity, conservative candle alignment and a pure counter-trade signal-policy foundation.
  - Existing collection packages provide Bybit, Binance, data-only staging, liquid20-v1 universe, multi-source acceptance and Synology collector deployment.
  - The new blueprint maps LQ-02 through LQ-07 into bounded paths and explicitly prevents one-PR implementation of the entire future tree.
  - The artifact manifest defines DatasetSelectionManifest, ReplayRequest, ReplayEvidenceReport, DecisionSnapshot, SignalObservationReport, ModelCandidateEvidence and ApprovedDryRunIntent.
  - Three valid JSON examples provide dataset-selection, replay-request and decision-snapshot starting structures.
  - The next-agent prompt starts with LQ-02 and contains explicit stop conditions when accepted data or versioned candles are absent.
derived:
  - Future agents no longer need to infer file placement, artifact identities or the first legal package from dispersed documents.
  - The next legal implementation remains dataset selection; replay, strategy, AI and execution stay gated.
unknown:
  - Current mutable Synology collector image, newest run and newest completed acceptance result.
  - Whether valid versioned candle evidence currently exists for an accepted interval.
  - Exact CI outcome for this documentation package.
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
  - command: live repository and path-ownership preflight
    result: PASS
    evidence: develop head, AGENTS.md, CONTEXT_HANDOFF.md, canonical architecture, current manifest, existing liquidation contracts and open PR ownership were inspected before writing.
  - command: manual strict-JSON structure review
    result: PASS
    evidence: Artifact manifest and all examples contain no comments or trailing commas.
blockers: []
next_action: Open a documentation PR against develop, require exact-head pre-commit, documentation, AI Platform CI, Freqtrade CI and zizmor, then close this task with the merge SHA.
```
