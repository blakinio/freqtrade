---
task_id: FTAI-20260724-liquidation-binance-source-v1
status: validating
branch: feat/liquidation-binance-source-v1
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: pending
owned_paths:
  - ai_platform/research/liquidations/binance.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/scripts/liquidation_binance_collector.py
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-binance-source-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
---

# Binance Liquidation Source v1

## Goal

Add Binance USD-M Futures as a second public liquidation source without changing the frozen Bybit staging policy,
enabling execution, merging unlike feed semantics, or making a profitability claim.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T12:30:00Z
head: pending
branch: feat/liquidation-binance-source-v1
pr: pending
status: validating
context_routes:
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
owned_paths:
  - ai_platform/research/liquidations/binance.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/scripts/liquidation_binance_collector.py
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-binance-source-v1.md
proven:
  - Bybit Stage 1 collection and its frozen policy are already merged and remain unchanged.
  - Binance documents the public USD-M forceOrder stream and live subscription protocol.
  - Binance documents that only the latest liquidation order per symbol within each 1000 ms window is pushed.
  - The canonical event contract already includes a source field and source-scoped deterministic event IDs.
  - The branch adds a Binance parser, bounded public collector, clock probe, source catalog, tests, and a multi-source runbook.
derived:
  - Binance can provide a second venue observation but cannot be treated as a complete liquidation-volume feed.
  - Cross-exchange events must not be deduplicated because they are venue-specific observations.
  - The two collectors should write separate immutable files and summaries to avoid concurrent append races.
unknown:
  - Repository CI result for the branch.
  - Public endpoint smoke result from a non-restricted host.
  - Multi-source 24-hour operational evidence.
conflicts: []
first_failure:
  marker: none
  evidence: No implementation failure is known before repository CI.
rejected_hypotheses:
  - Treat Binance forceOrder as a complete all-liquidation stream.
  - Sum Bybit and Binance notional values without source labels or declared normalization.
  - Modify the already frozen Bybit data-only-staging-policy-v1 after observing evidence.
  - Enable strategy execution, DCA, leverage, or live capital in this source-adapter package.
changed_paths:
  - ai_platform/research/liquidations/binance.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/scripts/liquidation_binance_collector.py
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-binance-source-v1.md
validation:
  - command: python -m py_compile new Python files
    result: PASS
    evidence: The new parser, collector, and tests compile locally.
  - command: focused parser assertions
    result: PASS
    evidence: SELL maps to liquidated long and executed quantity plus average fill price produce canonical notional.
blockers:
  - Repository CI and a public endpoint smoke have not completed.
next_action: Open a PR, repair only branch-local CI failures, then run a bounded Binance public-endpoint smoke without credentials.
```
