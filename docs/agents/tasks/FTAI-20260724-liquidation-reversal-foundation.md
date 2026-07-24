---
task_id: FTAI-20260724-liquidation-reversal-foundation
status: done
branch: feat/liquidation-reversal-foundation-v1
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "#236"
owned_paths:
  - ai_platform/research/liquidations/**
  - ai_platform/scripts/liquidation_collector.py
  - ai_platform/research/tradingview/catalog-v1.json
  - tests/ai_platform_integration/test_liquidation_research_foundation.py
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
---

# Liquidation Reversal Foundation

## Goal

Prepare the minimum safe data, signal, validation, and deployment foundation for a Wick Hunter-inspired
liquidation reversal strategy without enabling execution, DCA, live capital, profitability claims, or use of
the protected final holdout.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T11:10:00Z
head: 8ab033dd771b3f4695328b22f61c3f6d05a6e1d4
branch: develop
pr: "#236"
status: done
context_routes:
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
owned_paths:
  - ai_platform/research/liquidations/**
  - ai_platform/scripts/liquidation_collector.py
  - ai_platform/research/tradingview/catalog-v1.json
  - tests/ai_platform_integration/test_liquidation_research_foundation.py
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
proven:
  - PR #236 merged to develop as squash commit 8ab033dd771b3f4695328b22f61c3f6d05a6e1d4.
  - The merged foundation contains the canonical event contract, Bybit parser, append-only collector, closed-candle alignment, counter-trade policy, disabled profile, tests, and staged deployment process.
  - The profile remains research-only, execution-disabled, dry-run, position-size zero, with DCA and exits disabled.
  - Final AI Platform CI, full Freqtrade CI, pre-commit, documentation, mypy, Ruff, and zizmor checks passed.
derived:
  - The next safe work package is data-only staging with no exchange credentials or Freqtrade strategy.
  - Historical replay remains invalid until an operationally collected interval is accepted and frozen with hashes.
unknown:
  - Operational availability, parse-failure, reconnect, duplicate, event-volume, and latency evidence.
  - Exact future volume filter, exit policy, DCA policy, and execution adapter.
conflicts: []
first_failure:
  marker: none
  evidence: The final merged head had no unresolved validation failure.
rejected_hypotheses:
  - Treat a VWAP band breach without a real liquidation observation as a valid entry.
  - Use unfinished-candle final OHLCV in historical replay.
  - Enable DCA, execution, or real capital before frozen replay and dry-run evidence.
changed_paths:
  - ai_platform/research/liquidations/__init__.py
  - ai_platform/research/liquidations/contracts.py
  - ai_platform/research/liquidations/bybit.py
  - ai_platform/research/liquidations/alignment.py
  - ai_platform/research/liquidations/signals.py
  - ai_platform/research/liquidations/profile-example-v1.json
  - ai_platform/scripts/liquidation_collector.py
  - ai_platform/research/tradingview/catalog-v1.json
  - tests/ai_platform_integration/test_liquidation_research_foundation.py
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
validation:
  - command: AI Platform CI run 30078739837
    result: PASS
    evidence: Compile, tests, Ruff, Ruff format, codespell, and JSON validation passed.
  - command: Freqtrade CI run 30078739780
    result: PASS
    evidence: Pre-commit, documentation, cross-platform core tests, coverage, smoke tests, Ruff, and mypy passed.
  - command: GitHub Actions Security Analysis run 30078739728
    result: PASS
    evidence: Zizmor completed successfully.
blockers: []
next_action: Continue docs/agents/tasks/FTAI-20260724-liquidation-data-only-staging.md on its dedicated branch.
```
