---
task_id: FTAI-20260724-liquidation-symbol-universe-v1
status: active
branch: feat/liquidation-symbol-universe-v1
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: pending
owned_paths:
  - ai_platform/research/liquidations/symbol-universes-v1.json
  - ai_platform/research/liquidations/symbol_universe.py
  - ai_platform/scripts/liquidation_multi_source_runner.py
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-symbol-universe-v1.md
required_reads:
  - AGENTS.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
---

# Liquidation Symbol Universe v1

## Goal

Expand multi-source liquidation collection from BTCUSDT and ETHUSDT to a frozen, auditable 20-symbol universe shared by Bybit linear and Binance USD-M, without changing source semantics, enabling execution, or claiming operational acceptance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T13:10:00Z
head: bb8dc9189db954a1c8da8f45448e7e875a3af690
branch: feat/liquidation-symbol-universe-v1
pr: pending
status: active
context_routes:
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
owned_paths:
  - ai_platform/research/liquidations/symbol-universes-v1.json
  - ai_platform/research/liquidations/symbol_universe.py
  - ai_platform/scripts/liquidation_multi_source_runner.py
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-symbol-universe-v1.md
proven:
  - Bybit futures public subscriptions permit multiple symbols and are bounded by a 21000-character args limit.
  - The existing collectors already accept arbitrary repeated symbols and preserve per-source files and summaries.
  - PR #250 and checkpoint PR #253 are merged on develop.
derived:
  - Twenty symbols are operationally small for both public connections.
  - A frozen profile is more reproducible than a changing market-cap or 24-hour-volume ranking.
unknown:
  - Whether every proposed symbol is currently accepted by both production WebSocket endpoints.
  - Final repository CI result.
conflicts: []
first_failure:
  marker: none
  evidence: No implementation failure observed before branch creation.
rejected_hypotheses:
  - Call an unstable market-cap ranking top 20 without freezing its identity.
  - Start with 100 symbols before measuring event volume, symbol churn, storage, and parser health on 20.
  - Merge cross-exchange events or remove source labels.
changed_paths:
  - docs/agents/tasks/FTAI-20260724-liquidation-symbol-universe-v1.md
validation: []
blockers: []
next_action: Add a frozen liquid20-v1 profile, loader, multi-source runner, tests, and documentation; then validate both exchange subscriptions and repository CI.
```
