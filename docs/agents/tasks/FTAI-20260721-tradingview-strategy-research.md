---
task_id: FTAI-20260721-tradingview-strategy-research
status: implementing
branch: feat/tradingview-strategy-research-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
owned_paths:
  - ai_platform/research/tradingview/**
  - ai_platform/strategies/TradingViewResearchStrategies.py
  - tests/ai_platform/test_tradingview_research_*.py
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-tradingview-strategy-research.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
search_first: []
optional_reads:
  - ai_platform/research/tradingview/catalog-v1.json
---

# TradingView Strategy Research v1

## Goal

Create a separate research-only foundation for testing independently written adaptations of selected
public TradingView strategy ideas without changing Phase 6, frozen Phase 5.2 thresholds, promotion
state, or protected final-holdout policy.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-20T22:10:00Z
head: fb9547ade32ba29163f4830a11b1db288d8a6511
branch: feat/tradingview-strategy-research-v1
pr: none
status: implementing
context_routes:
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - ai_platform/research/tradingview/catalog-v1.json
owned_paths:
  - ai_platform/research/tradingview/**
  - ai_platform/strategies/TradingViewResearchStrategies.py
  - tests/ai_platform/test_tradingview_research_*.py
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-tradingview-strategy-research.md
proven:
  - develop was verified at 0e82e4db72b7e84555b2873a69f78a03e721a195 before branch creation.
  - Phase 6 final result assembler and its checkpoint closure are merged on develop.
  - PR #52 is a separate open PyTorch/RL research foundation and is not modified by this task.
  - Public TradingView research sources were identified for Wick Hunter Multi-VWAP, Donchian breakout, Supertrend, and Bollinger mean reversion.
  - Local implementations are independent adaptations; Pine source code is not copied or republished.
  - Donchian breakout, Supertrend, and Bollinger adaptations have Freqtrade research strategy classes under ai_platform/strategies.
  - Wick Hunter is implemented only as a VWAP distance gate because a trustworthy time-aligned historical liquidation feed is not yet bound.
  - Protected final holdout 20260801-20260930 is forbidden and Phase 6 membership/promotion/profitability claims remain false.
derived:
  - The first useful comparison can evaluate three candle-only candidates under one pinned historical OOS protocol while liquidation research proceeds independently.
unknown:
  - GitHub Actions CI outcome for the implementation branch.
  - Concrete historical OOS pair universe, timerange, futures dry-run config, fee assumption, and persisted result location for the first comparison run.
  - Historical liquidation data source and deterministic alignment contract for the Wick Hunter candidate.
conflicts: []
first_failure:
  marker: local-clone-dns
  evidence: Sandbox git clone could not resolve github.com; executable validation must use GitHub Actions CI.
rejected_hypotheses:
  - Reuse the protected final holdout for rapid strategy ranking.
  - Treat VWAP distance alone as a complete Wick Hunter liquidation strategy.
  - Copy public Pine source code into the repository.
changed_paths:
  - ai_platform/research/tradingview/__init__.py
  - ai_platform/research/tradingview/signals.py
  - ai_platform/research/tradingview/catalog-v1.json
  - ai_platform/strategies/TradingViewResearchStrategies.py
  - tests/ai_platform/test_tradingview_research_signals.py
  - tests/ai_platform/test_tradingview_research_strategies.py
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-tradingview-strategy-research.md
validation:
  - command: local clone/test
    result: BLOCKED
    evidence: Sandbox DNS could not resolve github.com; GitHub Actions will be used for executable validation.
blockers: []
next_action: Open a pull request against develop and use GitHub Actions to validate compile, targeted AI-platform tests, Ruff, formatting, codespell, JSON validation, and repository CI; fix any failures before considering the foundation complete.
```
