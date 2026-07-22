---
task_id: FTAI-20260722-tradingview-futures-historical-preflight
status: implementing
branch: feat/tradingview-futures-historical-preflight-v1
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#112"
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
- historical download request: `20260201-20260701`;
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
updated_at: 2026-07-22T11:10:00+02:00
head: fd7065fe8d3780f36269c813a6ddf8d73c68abc5
branch: feat/tradingview-futures-historical-preflight-v1
pr: "#112"
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
  - The validator resolves runtime markets fail-closed and materializes the config only from validated discovered symbols.
  - Dedicated preflight workflow run 29906078000 succeeded through strategy loading, market discovery, config materialization, bounded 15m futures download, coverage verification, and evidence upload without running a strategy backtest.
  - Runtime discovery resolved BTC/USD:USD with Kraken Futures market id PF_XBTUSD and ETH/USD:USD with market id PF_ETHUSD; both were active USD-quoted USD-settled swap contracts.
  - Evidence artifact 8523923560 has digest sha256:1b4ce3ea3e68d9f74de9908f88798a94209766215c33c8c0f146074805d633fa and records 14401 15m rows for each resolved pair from 2026-02-01T00:00:00Z through 2026-07-01T00:00:00Z with maximum observed gap 900 seconds.
  - The semantic research window remains 20260301-20260630 and the later benchmark execution timerange remains 20260301-20260701 with the stop treated as the evaluation boundary; the downloaded source file may contain the boundary candle and therefore must not define scoring membership by itself.
  - The generated runtime config remained futures/isolated/USD, dry_run=true, and used only BTC/USD:USD and ETH/USD:USD.
  - Protected final holdout 20260801-20260930 was not accessed; no strategy backtest, ranking, promotion, profitability claim, or superiority claim was produced.
  - AI Platform CI run 29906606278 and zizmor run 29906606163 succeeded on implementation head fd7065fe8d3780f36269c813a6ddf8d73c68abc5.
derived:
  - The Kraken Futures 15m data path is proven ready for a separately authorized historical benchmark of the three fixed candle-only candidates under common execution assumptions.
  - Later benchmark scoring must filter by the declared execution timerange rather than assume the downloaded file excludes a candle exactly at the request stop boundary.
unknown:
  - Final-head CI outcome after this durable checkpoint update.
conflicts: []
first_failure:
  marker: strategy-loader-project-path
  evidence: Dedicated preflight run 29905329735 initially failed while loading ai_platform strategy dependencies through the Freqtrade console entry point; setting PYTHONPATH to the checked-out repository root fixed the loader and later run 29906078000 passed the full data-only preflight.
rejected_hypotheses:
  - Reuse Kraken spot BTC/USDT and ETH/USDT for strategies with short entries.
  - Guess Kraken Futures market symbols without runtime discovery.
  - Run the three strategy backtests before data mode and coverage are proven.
  - Treat the downloaded file boundary as the benchmark scoring boundary without applying the declared execution timerange.
changed_paths:
  - ai_platform/research/tradingview/futures-historical-preflight-v1.json
  - ai_platform/configs/tradingview-futures-research.example.json
  - ai_platform/scripts/tradingview_futures_historical_preflight.py
  - tests/ai_platform/test_tradingview_futures_historical_preflight.py
  - .github/workflows/ai-platform-tradingview-futures-preflight.yml
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-preflight.md
validation:
  - command: AI Platform TradingView Futures Preflight run 29906078000
    result: PASS
    evidence: Contract, checkpoint, strategy loading, Kraken Futures market discovery, config materialization, 15m download, coverage verification, and artifact upload all succeeded; no backtest step exists.
  - command: AI Platform CI run 29906606278
    result: PASS
    evidence: Compile, AI-platform tests, Ruff, Ruff format, codespell, and JSON validation succeeded on head fd7065fe8d3780f36269c813a6ddf8d73c68abc5.
  - command: GitHub Actions Security Analysis with zizmor run 29906606163
    result: PASS
    evidence: Workflow completed successfully on head fd7065fe8d3780f36269c813a6ddf8d73c68abc5.
blockers: []
next_action: Merge PR #112 only after the required workflows on the final checkpoint head complete successfully.
```
