---
task_id: FTAI-20260722-tradingview-futures-historical-benchmark
status: ready
branch: develop
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "132"
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
updated_at: 2026-07-22T23:01:59+02:00
head: 73f612557fd2a14d2ab3f8d413a32853b1e7f554
branch: develop
pr: none
status: ready
context_routes:
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_PREFLIGHT.md
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_BENCHMARK.md
  - .github/workflows/ai-platform-tradingview-futures-historical-benchmark.yml
owned_paths:
  - ai_platform/research/tradingview/futures-historical-benchmark-v1.json
  - ai_platform/scripts/tradingview_futures_historical_benchmark.py
  - tests/ai_platform/test_tradingview_futures_historical_benchmark.py
  - .github/workflows/ai-platform-tradingview-futures-historical-benchmark.yml
  - ai_platform/research/tradingview/run-requests/futures-historical-benchmark-v1.json
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_BENCHMARK.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-benchmark.md
proven:
  - PR #122 merged the frozen benchmark contract and one-shot workflow; subsequent resolver and extractor compatibility fixes were merged without changing candidate logic or frozen benchmark geometry.
  - Canonical trigger PR #132 changed exactly ai_platform/research/tradingview/run-requests/futures-historical-benchmark-v1.json, passed all required CI, and was squash-merged as 73f612557fd2a14d2ab3f8d413a32853b1e7f554.
  - Dedicated benchmark run 29947929886 completed contract validation, strategy resolver preflight, market rebinding, data coverage verification, all three backtests, validation analyses, comparison assembly, and artifact upload successfully.
  - Immutable benchmark artifact 8541078835 has digest sha256:9cb7c603d6c1f612a783907aa6ca112c7f946efff80abdd38ad283bed1ad822c and is retained until 2026-10-20.
  - Historical ordering is TVBollingerMeanReversionStrategy, TVSupertrendStrategy, TVDonchianBreakoutStrategy; selected_candidate remains null and no promotion or superiority claim is authorized.
  - Bollinger produced profit_total -0.02944326341, max_drawdown 0.03016401647122 and 912 trades; Supertrend produced -0.031403532914, 0.03162537857 and 603 trades; Donchian produced -0.034981894459, 0.0350744488 and 613 trades.
  - Lookahead analysis returned exit code 0 but no CSV/strategy row for all three candidates, so every lookahead status is incomplete; recursive analysis returned exit code 0 for all three and is marked completed_review_required.
  - Protected final holdout 20260801-20260930 was not used; retuning, automatic validation, promotion, live trading, profitability claims and superiority claims remain forbidden.
derived:
  - None of the three frozen candidates produced positive historical return under the common benchmark assumptions, so the historical ordering is research evidence only and does not justify promotion.
  - The task now needs evidence materialization and manual validation review rather than another benchmark rerun or parameter change.
unknown:
  - Why lookahead-analysis produced no CSV strategy row despite exit code 0, and whether a separate bounded compatibility investigation can produce conclusive bias evidence without changing candidate logic.
  - Whether recursive-analysis indicator variance is operationally negligible for each candidate after manual review of the retained logs.
conflicts: []
first_failure:
  marker: resolved_prior_execution_failures
  evidence: Attempts #125/#127 failed closed before backtesting and #129 failed on drawdown normalization; resolver fixes #126/#128 and extractor fix #130 resolved those issues, and #132 completed successfully.
rejected_hypotheses:
  - Add Wick Hunter without trustworthy historical liquidation observations.
  - Retune or mutate candidate parameters after observing benchmark results.
  - Treat historical ordering as automatic winner selection or promotion authorization.
  - Use protected final holdout data for this benchmark or its follow-up review.
changed_paths:
  - ai_platform/research/tradingview/run-requests/futures-historical-benchmark-v1.json
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-benchmark.md
validation:
  - command: GitHub Actions on PR #132 head 9c03faedea870cea78b46672545fb4a4ba371e6f
    result: PASS
    evidence: AI Platform CI, Freqtrade CI, zizmor and AI Platform TradingView Futures Historical Benchmark all completed success; Pre-commit Types update was skipped.
  - command: Dedicated benchmark workflow run 29947929886
    result: PASS
    evidence: Execute frozen one-shot historical benchmark completed successfully and uploaded artifact 8541078835 with digest sha256:9cb7c603d6c1f612a783907aa6ca112c7f946efff80abdd38ad283bed1ad822c.
blockers: []
next_action: Create a separate evidence-materialization and validation-review branch from current develop, persist the immutable run 29947929886 provenance and benchmark summary, review the incomplete lookahead and recursive-analysis evidence without retuning, and close the task with selected_candidate remaining null unless a separately declared future work package is authorized.
```
