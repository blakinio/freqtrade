---
task_id: FTAI-20260726-liquid20-h1-provider-neutral-contracts
status: completed
branch: feat/liquid20-h1-provider-neutral-contracts
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#360"
owned_paths:
  - ai_platform/research/liquidations/historical/
  - tests/ai_platform_integration/test_liquidation_history_contracts.py
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
  - docs/agents/tasks/FTAI-20260726-liquid20-h1-provider-neutral-contracts.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
search_first:
  - current develop HEAD and open Liquid20 historical PRs
optional_reads: []
---

# Liquid20 H1 provider-neutral contracts

## Goal

Implement the provider-neutral historical event, manifest, semantic-era, acceptance and adapter contracts with deterministic identities and synthetic tests. No network, provider purchase, credential, bulk data, Synology mutation, feature generation, model training, protected-holdout access or execution.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T12:05:00Z
head: e2def4e06822b2f933fdeaadb66df96afcef0e24
merge_commit: cc30499eb843de7f611c7e81e6484c054881f417
branch: feat/liquid20-h1-provider-neutral-contracts
pr: "#360"
status: completed
context_routes:
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
owned_paths:
  - ai_platform/research/liquidations/historical/
  - tests/ai_platform_integration/test_liquidation_history_contracts.py
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
  - docs/agents/tasks/FTAI-20260726-liquid20-h1-provider-neutral-contracts.md
proven:
  - H0 and the CoinAPI authenticated trial are merged.
  - Historical events preserve provider occurrence and availability provenance without populating first-party received_at_ms.
  - Deterministic event, manifest and acceptance identities are implemented with Draft 2020-12 schemas.
  - Explicit Tardis and first-party semantic eras are frozen while the 2025-02-20 through 2025-02-25 Bybit interval remains unresolved.
  - Protected final holdout overlap, negative provider latency, semantic-era mismatch and duplicate fingerprints fail closed.
  - PR 360 merged as cc30499eb843de7f611c7e81e6484c054881f417.
derived:
  - H2 can implement a local Tardis normalized-CSV adapter and deterministic importer without credentials or paid bulk data.
unknown:
  - Paid full-history availability and license approval remain deferred to H3.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Reuse historical provider timestamps as first-party received_at_ms.
  - Resolve the excluded 2025-02-20 through 2025-02-25 Bybit interval implicitly.
  - Mix provider parsing into feature or model code.
changed_paths:
  - ai_platform/research/liquidations/historical/
  - tests/ai_platform_integration/test_liquidation_history_contracts.py
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
  - docs/agents/tasks/FTAI-20260726-liquid20-h1-provider-neutral-contracts.md
validation:
  - command: AI Platform CI
    result: PASS
    evidence: Run 30200707575 completed successfully with tests, compile, Ruff, formatting, codespell and JSON validation.
  - command: Freqtrade CI
    result: PASS
    evidence: Run 30200707560 completed successfully through Python 3.11-3.14, pre-commit, docs, package build and CI Gate.
  - command: GitHub Actions Security Analysis with zizmor
    result: PASS
    evidence: Run 30200707605 completed successfully.
blockers: []
next_action: Implement H2 as a fresh local-only Tardis normalized-CSV adapter and deterministic importer using synthetic fixtures and public free samples, without paid access or bulk download.
```
