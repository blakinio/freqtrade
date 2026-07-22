---
task_id: FTAI-20260722-tradingview-futures-historical-preflight
status: ready
branch: docs/tradingview-futures-historical-preflight-task
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: ""
owned_paths:
  - ai_platform/research/tradingview/futures-historical-preflight-v1.json
  - ai_platform/configs/tradingview-futures-research.example.json
  - ai_platform/scripts/tradingview_futures_historical_preflight.py
  - tests/ai_platform/test_tradingview_futures_historical_preflight.py
  - .github/workflows/ai-platform-tradingview-futures-preflight.yml
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-preflight.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
search_first:
  - TradingView historical preflight benchmark futures Kraken Futures
  - experimental historical backtest execution preflight
optional_reads:
  - .github/workflows/experimental-model-historical-backtest-execution.yml
---

# TradingView Futures Historical Preflight

## Goal

Add a fail-closed, preflight-only work package that proves an executable historical futures data path for the three merged candle-only TradingView research strategies before any comparative backtest is authorized.

The preflight must resolve and freeze the exact BTC and ETH USD-settled perpetual market symbols supported by the repository runtime, verify required historical 15m coverage, and materialize a common dry-run futures research configuration. It must not execute any of the three strategy backtests.

## Frozen research boundary

- candidates: `TVDonchianBreakoutStrategy`, `TVSupertrendStrategy`, `TVBollingerMeanReversionStrategy` only;
- Wick Hunter liquidation/VWAP remains excluded until a trustworthy historical liquidation feed and deterministic alignment contract exist;
- exchange runtime target: `krakenfutures`;
- trading mode: `futures`;
- margin mode: `isolated`;
- settlement/stake currency: `USD`;
- exact BTC and ETH perpetual symbols: resolved by preflight and then frozen, never guessed;
- strategy timeframe: `15m`;
- historical research semantic window: `20260301-20260630`;
- technical Freqtrade execution stop: exclusive `20260701`;
- historical download ceiling: exclusive `20260701`;
- common fee assumption for later comparison: `0.002`;
- `dry_run: true` required;
- no leverage optimization or parameter tuning;
- no ranking or winner selection in the preflight.

The previously consumed `20260501-20260630` period is historical research evidence only. It must not be described as unseen final evidence and must not be used to tune these strategy implementations after results are observed.

## Safety boundaries

- protected final holdout `20260801-20260930` remains unused and forbidden;
- no final-holdout evaluation before `2026-10-01 UTC`;
- frozen Phase 5 thresholds `0.006/-0.009` remain unchanged and irrelevant to these candle-only strategy signals;
- completed Phase 6 and authoritative `selected_model = null` remain unchanged;
- no backtest, Hyperopt, parameter search, strategy mutation, promotion, live trading, profitability claim, or superiority claim;
- no changes to upstream `freqtrade/` core unless a separately reviewed capability gap is proven.

## Acceptance criteria

The implementation task must fail closed unless it can prove all of the following before any later backtest work package:

1. the runtime exposes exactly one eligible active USD-settled perpetual market for BTC and exactly one for ETH under the declared Kraken Futures mode;
2. the resolved symbols are persisted as evidence and used consistently by the generated research config;
3. the generated config is futures/isolated/USD and `dry_run: true`;
4. 15m history covers the declared historical research window through the final required candle before `2026-07-01T00:00:00Z`;
5. no requested or downloaded range overlaps the protected final holdout;
6. all three strategy classes load from the merged TradingView research implementation;
7. the preflight emits no strategy-performance metric and executes no comparative backtest.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T10:30:00+02:00
head: db38831df4115df35249227dd2db754d7c000793
branch: docs/tradingview-futures-historical-preflight-task
pr: none
status: ready
context_routes:
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - .github/workflows/experimental-model-historical-backtest-execution.yml
owned_paths:
  - ai_platform/research/tradingview/futures-historical-preflight-v1.json
  - ai_platform/configs/tradingview-futures-research.example.json
  - ai_platform/scripts/tradingview_futures_historical_preflight.py
  - tests/ai_platform/test_tradingview_futures_historical_preflight.py
  - .github/workflows/ai-platform-tradingview-futures-preflight.yml
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-preflight.md
proven:
  - develop is verified at db38831df4115df35249227dd2db754d7c000793 at task declaration time.
  - PR #55 merged the isolated TradingView strategy research foundation.
  - The three candle-only TradingView candidates are long/short research strategies intended for futures testing.
  - No separate TradingView historical benchmark or preflight PR exists in the current repository state.
  - Existing one-shot historical research infrastructure establishes fail-closed request, data-coverage, execution-boundary, and evidence patterns.
  - The protected final holdout remains 20260801-20260930 and is outside this task.
derived:
  - A futures-specific data preflight is required before comparing the long/short candidates because the existing historical model execution path used Kraken spot data.
unknown:
  - Exact active Kraken Futures unified symbols for the BTC and ETH USD-settled perpetual markets in the repository runtime.
  - Whether GitHub Actions can obtain complete 15m Kraken Futures history for both resolved markets through the exclusive 20260701 stop.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - Reuse Kraken spot BTC/USDT and ETH/USDT for strategies with short entries.
  - Guess Kraken Futures market symbols without runtime discovery.
  - Run the three strategy backtests before data mode and coverage are proven.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-preflight.md
validation:
  - command: not-run
    result: NOT_RUN
    evidence: Task declaration only; repository CI will validate the declaration PR.
blockers: []
next_action: Implement the fail-closed TradingView futures historical preflight from current develop, including runtime symbol discovery, dry-run futures config materialization, protected-holdout guards, strategy-loading checks, 15m historical coverage verification, targeted tests, and a data-only GitHub Actions preflight that performs no strategy backtest.
```
