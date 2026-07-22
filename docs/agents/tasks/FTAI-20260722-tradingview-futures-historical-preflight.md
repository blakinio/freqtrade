---
task_id: FTAI-20260722-tradingview-futures-historical-preflight
status: implementing
branch: feat/tradingview-futures-historical-preflight-v1
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
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_PREFLIGHT.md
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
updated_at: 2026-07-22T10:48:00+02:00
head: 3084d25032bc4526648ba331beacb8a91ef94c18
branch: feat/tradingview-futures-historical-preflight-v1
pr: none
status: implementing
context_routes:
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_PREFLIGHT.md
  - .github/workflows/experimental-model-historical-backtest-execution.yml
owned_paths:
  - ai_platform/research/tradingview/futures-historical-preflight-v1.json
  - ai_platform/configs/tradingview-futures-research.example.json
  - ai_platform/scripts/tradingview_futures_historical_preflight.py
  - tests/ai_platform/test_tradingview_futures_historical_preflight.py
  - .github/workflows/ai-platform-tradingview-futures-preflight.yml
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-preflight.md
proven:
  - Task declaration PR #111 merged to develop as 60715d85739800bcae20b0c3c30cf395acb48cda after Freqtrade CI and zizmor succeeded.
  - The implementation contract fixes exactly three candle-only TradingView candidates and keeps Wick Hunter excluded pending historical liquidation data.
  - The tracked config template is krakenfutures futures isolated USD and dry_run=true with an intentionally empty pair whitelist before discovery.
  - The validator discovers exactly one active contract swap with quote USD and settle USD for each BTC and ETH base and fails closed on missing or ambiguous matches.
  - The validator materializes the runtime config only from discovered symbols and checks the protected final holdout does not overlap execution or download ranges.
  - The data verifier uses CandleType.FUTURES and requires 15m warmup coverage plus the final 2026-06-30 23:45 UTC candle.
  - The dedicated workflow performs strategy loading, public market discovery, config materialization, bounded historical download and coverage verification only; it contains no strategy backtest step.
derived:
  - Successful workflow evidence will be sufficient to declare the futures data path ready for a separately authorized benchmark, but not to rank or promote any strategy.
unknown:
  - Exact active Kraken Futures unified symbols for BTC and ETH in the GitHub Actions runtime.
  - Whether Kraken Futures historical 15m download reaches the complete declared window in GitHub Actions.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - Reuse Kraken spot BTC/USDT and ETH/USDT for strategies with short entries.
  - Guess Kraken Futures market symbols without runtime discovery.
  - Run the three strategy backtests before data mode and coverage are proven.
changed_paths:
  - ai_platform/research/tradingview/futures-historical-preflight-v1.json
  - ai_platform/configs/tradingview-futures-research.example.json
  - ai_platform/scripts/tradingview_futures_historical_preflight.py
  - tests/ai_platform/test_tradingview_futures_historical_preflight.py
  - .github/workflows/ai-platform-tradingview-futures-preflight.yml
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-preflight.md
validation:
  - command: GitHub Actions on implementation PR
    result: NOT_RUN
    evidence: Implementation branch is ready to open for CI and data-only preflight validation.
blockers: []
next_action: Open the implementation pull request against develop and use AI Platform CI, Freqtrade CI, zizmor, checkpoint validation, and the dedicated TradingView Futures Preflight workflow to fix any contract, lint, strategy-loading, market-discovery, or historical-data coverage failure before merge.
```
