---
task_id: FTAI-20260722-tradingview-futures-historical-benchmark
status: declared
branch: feat/tradingview-futures-historical-benchmark-v1
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: ""
owned_paths:
  - ai_platform/research/tradingview/futures-historical-benchmark-v1.json
  - ai_platform/scripts/tradingview_futures_historical_benchmark.py
  - tests/ai_platform/test_tradingview_futures_historical_benchmark.py
  - .github/workflows/ai-platform-tradingview-futures-historical-benchmark.yml
  - ai_platform/research/tradingview/run-requests/futures-historical-benchmark-v1.json
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_BENCHMARK.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-benchmark.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_PREFLIGHT.md
search_first:
  - TradingView futures historical benchmark one-shot
  - historical backtest execution request
optional_reads:
  - .github/workflows/experimental-model-historical-backtest-execution.yml
---

# TradingView Futures Historical Benchmark

## Goal

Create a separately declared, one-shot historical benchmark for the three already merged candle-only TradingView research strategies using the exact futures market path proven by the preceding preflight.

This task is evidence-only. It may execute frozen historical backtests and deterministic validation analyses, but it may not tune strategy parameters, mutate strategy logic after observing results, promote a candidate, claim profitability or superiority, or access the protected final holdout.

## Frozen benchmark boundary

- candidates, in canonical order:
  1. `TVDonchianBreakoutStrategy`;
  2. `TVSupertrendStrategy`;
  3. `TVBollingerMeanReversionStrategy`;
- strategy source blob at declaration: `e6deee3f9f8832745c66933dc639e5b7c9cffe53`;
- signal source blob at declaration: `7d9f8360166d8f8fc2ffa238f0ad3385af111a31`;
- exchange: `krakenfutures`;
- trading mode: `futures`;
- margin mode: `isolated`;
- stake/settlement currency: `USD`;
- pairs, in canonical order:
  1. `BTC/USD:USD` (`PF_XBTUSD`);
  2. `ETH/USD:USD` (`PF_ETHUSD`);
- timeframe: `15m`;
- semantic research window: `20260301-20260630`;
- Freqtrade execution timerange: `20260301-20260701`;
- common fee assumption: `0.002`;
- `dry_run: true` required;
- no leverage optimization;
- no Hyperopt;
- no parameter search;
- no candidate mutation from observed benchmark results.

The previously consumed `20260501-20260630` interval is historical research evidence. Results from this task are not unseen final evidence and cannot authorize retuning on the same reported window.

## Required execution contract

The implementation must fail closed unless it can prove before execution that:

1. the benchmark candidate set and order are unchanged;
2. the declared strategy and signal source identities are unchanged from the frozen contract or are rebound prospectively before any result-producing run;
3. the exact two preflight-proven Kraken Futures pairs are used for every candidate;
4. every candidate uses identical timeframe, timerange, fee, wallet/stake assumptions, pair universe and execution semantics;
5. the materialized config remains futures/isolated/USD and `dry_run: true`;
6. requested/downloaded/scored ranges do not overlap protected final holdout `20260801-20260930`;
7. exactly one canonical benchmark request can trigger the result-producing workflow;
8. the result-producing trigger PR is scope-limited to adding the canonical run-request file;
9. each candidate backtest is bound to the exact execution commit and immutable evidence artifacts are retained;
10. no winner promotion, live trading or profitability/superiority claim is emitted automatically.

## Required validation evidence

For each candidate preserve at minimum:

- exact Git commit and source identities;
- exact config and command;
- pair universe and timerange;
- fee assumption;
- Freqtrade backtest archive;
- trade count;
- total/relative profit metrics available from the canonical archive;
- maximum drawdown metrics available from the canonical archive;
- pair-level results;
- exit-reason results;
- long/short breakdown when available;
- lookahead-analysis result;
- recursive-analysis result or explicit bounded incompatibility evidence;
- deterministic extraction into one common comparison schema.

The benchmark may produce an ordering for research review, but it must explicitly label that ordering as historical evidence only. No automatic promotion decision is authorized.

## Safety boundaries

- protected final holdout: `20260801-20260930`, usage forbidden;
- no final-holdout evaluation before `2026-10-01T00:00:00Z`;
- frozen Phase 5 thresholds `0.006/-0.009` remain unchanged and are not candidate parameters here;
- completed Phase 6 and authoritative `selected_model = null` remain unchanged;
- PyTorch/RL evidence remains separate;
- Wick Hunter liquidation/VWAP remains excluded pending trustworthy historical liquidation data and deterministic alignment;
- no live-capital or promotion action;
- no upstream `freqtrade/` core modification unless a separately reviewed capability gap is proven.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T11:30:00+02:00
head: 0dd4a1b79cd5794bddb06f339c526e4b8685c9eb
branch: feat/tradingview-futures-historical-benchmark-v1
pr: none
status: declared
context_routes:
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_PREFLIGHT.md
  - .github/workflows/experimental-model-historical-backtest-execution.yml
owned_paths:
  - ai_platform/research/tradingview/futures-historical-benchmark-v1.json
  - ai_platform/scripts/tradingview_futures_historical_benchmark.py
  - tests/ai_platform/test_tradingview_futures_historical_benchmark.py
  - .github/workflows/ai-platform-tradingview-futures-historical-benchmark.yml
  - ai_platform/research/tradingview/run-requests/futures-historical-benchmark-v1.json
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_BENCHMARK.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-benchmark.md
proven:
  - TradingView futures preflight PR #112 merged to develop as 0dd4a1b79cd5794bddb06f339c526e4b8685c9eb after AI Platform CI, Freqtrade CI, zizmor and the dedicated runtime preflight succeeded.
  - Preflight resolved BTC/USD:USD as PF_XBTUSD and ETH/USD:USD as PF_ETHUSD under krakenfutures futures isolated USD mode.
  - Preflight evidence verified 15m historical coverage sufficient for the declared 20260301-20260630 research window and strategy warmup.
  - The three canonical strategy classes are loadable through Freqtrade and are ready for controlled historical OOS research backtesting.
  - Wick Hunter remains excluded because no trustworthy historical liquidation feed has been bound to the research track.
derived:
  - A one-shot benchmark can now be implemented without changing candidate logic or touching the protected final holdout.
  - Historical benchmark results may support later research prioritization but cannot by themselves authorize promotion.
unknown:
  - Whether each candidate completes backtesting successfully under the common futures execution contract.
  - Whether lookahead-analysis and recursive-analysis are directly compatible with all three futures strategies in the current repository runtime.
  - Comparative historical performance of the three candidates under identical assumptions.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - Add Wick Hunter to the benchmark without historical liquidation observations.
  - Retune candidate parameters after observing this benchmark.
  - Use protected final holdout data for the benchmark.
  - Reuse spot BTC/USDT and ETH/USDT instead of the preflight-proven futures markets.
changed_paths:
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-benchmark.md
validation:
  - command: GitHub Actions on declaration PR
    result: NOT_RUN
    evidence: Declaration branch created from merged preflight commit; no benchmark execution authorized yet.
blockers: []
next_action: Open the declaration pull request against develop, merge it only after required CI succeeds, then implement the frozen benchmark contract and one-shot execution workflow on a fresh branch from updated develop without creating the result-producing run-request yet.
```
