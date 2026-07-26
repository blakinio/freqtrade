---
task_id: FTAI-20260726-liquid20-h1-provider-neutral-contracts
status: in_progress
branch: feat/liquid20-h1-provider-neutral-contracts
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: pending
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
updated_at: 2026-07-26T11:30:00Z
head: pending
branch: feat/liquid20-h1-provider-neutral-contracts
pr: pending
status: in_progress
context_routes:
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
  - docs/ai_platform/LIQUID20_HISTORICAL_AI_TRAINING_ARCHITECTURE.md
owned_paths:
  - ai_platform/research/liquidations/historical/
  - tests/ai_platform_integration/test_liquidation_history_contracts.py
  - docs/ai_platform/LIQUID20_HISTORICAL_CONTRACTS.md
  - docs/agents/tasks/FTAI-20260726-liquid20-h1-provider-neutral-contracts.md
proven:
  - H0 and the CoinAPI authenticated trial are merged and leave H1/H2 as the autonomous next action.
derived:
  - H1 can be completed without network access or provider credentials.
unknown: []
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
  - command: targeted H1 tests and repository CI
    result: PENDING
    evidence: Run after the implementation commit.
blockers: []
next_action: Validate the H1 implementation, open a PR, merge it when CI and review are clean, then begin H2 on a fresh branch.
```
