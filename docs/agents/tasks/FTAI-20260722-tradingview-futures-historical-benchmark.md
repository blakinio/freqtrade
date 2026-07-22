---
task_id: FTAI-20260722-tradingview-futures-historical-benchmark
status: done
branch: docs/tradingview-futures-benchmark-final-closure
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: "#132, #140, #141, #146, #152"
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
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_BENCHMARK.md
search_first:
  - TradingView futures historical benchmark one-shot
  - PR 132 benchmark evidence
---

# TradingView Futures Historical Benchmark

## Goal

Run one frozen, evidence-only historical comparison of the three existing candle-only TradingView research strategies on the same Kraken Futures data path, then preserve the result without retuning, promotion, or protected-final-holdout access.

## Frozen benchmark

- candidates: `TVDonchianBreakoutStrategy`, `TVSupertrendStrategy`, `TVBollingerMeanReversionStrategy`;
- pairs: `BTC/USD:USD` / `PF_XBTUSD` and `ETH/USD:USD` / `PF_ETHUSD`;
- timeframe: `15m`;
- execution timerange: `20260301-20260701`;
- semantic research window: `20260301-20260630`;
- fee: `0.002`;
- futures / isolated / USD / `dry_run: true`;
- no Hyperopt, parameter search, strategy mutation, promotion, or live trading.

## Completed historical result

The canonical one-shot execution ran in workflow `29947929886` from exact execution head `9c03faedea870cea78b46672545fb4a4ba371e6f`. Immutable benchmark artifact `8541078835` has digest `sha256:9cb7c603d6c1f612a783907aa6ca112c7f946efff80abdd38ad283bed1ad822c`.

Historical ordering by the frozen ranking rule was:

1. `TVBollingerMeanReversionStrategy`: profit `-2.944326341%`, max drawdown `3.016401647122%`, `912` trades;
2. `TVSupertrendStrategy`: profit `-3.1403532914%`, max drawdown `3.162537856999988%`, `603` trades;
3. `TVDonchianBreakoutStrategy`: profit `-3.4981894459%`, max drawdown `3.5074448800000026%`, `613` trades.

All three candidates were historically negative. The benchmark kept `selected_candidate = null`; no profitability, superiority, validation, retuning, or promotion claim is authorized.

## Validation evidence

The original lookahead invocation was incomplete because Freqtrade forced market entry orders while the frozen benchmark config used `entry_pricing.price_side = same`. The isolated analysis-only repair completed in workflow `29958028584` without rerunning backtests or changing ranking. All three candidates produced `has_bias=False` over twenty checked signals with zero biased entry and exit signals.

Recursive-analysis review remains research evidence rather than an automatic pass:

- Bollinger: effectively zero variance across tested startup-candle counts;
- Donchian: EMA variance at the strategy startup count `120` was `0.078%` and converged toward zero with larger warm-up;
- Supertrend: at the strategy startup count `50`, `tv_supertrend` differed by `-1.016%` and `tv_supertrend_direction` by `-200%`, so this v1 runtime geometry is not treated as recursively stable for promotion purposes.

No candidate is promoted. Any changed Supertrend startup geometry or other strategy variant must be a separately declared prospective experiment and cannot reinterpret this frozen benchmark.

## Archived one-shot workflow

PR #152 converted the consumed result-producing workflow into a maintenance-only archive guard and was squash-merged as `f989f778d8dfeb623fd09dba3dd5fe42e90505c6` after Freqtrade CI, zizmor, and the dedicated archive guard succeeded.

Maintenance PRs now validate the checkpoint and frozen contract, prove the consumed request is unchanged, and cannot execute another benchmark. Deleting or modifying the consumed request fails closed. No result-producing job remains in the archived workflow.

## Safety boundaries

- consumed historical evidence is not unseen final evidence and must not be reused for retuning these v1 candidates;
- protected final holdout `20260801-20260930` remains unused;
- final holdout evaluation remains forbidden before `2026-10-01T00:00:00Z`;
- frozen Phase 5 thresholds `0.006/-0.009` remain unchanged;
- completed Phase 6 and authoritative `selected_model = null` remain unchanged;
- PyTorch/RL evidence remains isolated from this benchmark.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T23:55:00+02:00
head: f989f778d8dfeb623fd09dba3dd5fe42e90505c6
branch: docs/tradingview-futures-benchmark-final-closure
pr: pending
status: ready
context_routes:
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_BENCHMARK.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-lookahead-repair.md
owned_paths:
  - ai_platform/research/tradingview/futures-historical-benchmark-v1.json
  - ai_platform/scripts/tradingview_futures_historical_benchmark.py
  - tests/ai_platform/test_tradingview_futures_historical_benchmark.py
  - .github/workflows/ai-platform-tradingview-futures-historical-benchmark.yml
  - ai_platform/research/tradingview/run-requests/futures-historical-benchmark-v1.json
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_BENCHMARK.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-benchmark.md
proven:
  - PR #132 merged the canonical one-shot request and workflow run 29947929886 completed all three frozen backtests.
  - Benchmark artifact 8541078835 has digest sha256:9cb7c603d6c1f612a783907aa6ca112c7f946efff80abdd38ad283bed1ad822c.
  - Historical ordering is Bollinger, Supertrend, Donchian; all three total-profit results are negative.
  - Bollinger produced -2.944326341% total profit, 3.016401647122% max drawdown and 912 trades.
  - Supertrend produced -3.1403532914% total profit, 3.162537856999988% max drawdown and 603 trades.
  - Donchian produced -3.4981894459% total profit, 3.5074448800000026% max drawdown and 613 trades.
  - Lookahead repair workflow 29958028584 completed without backtest reruns or ranking changes.
  - All three candidates produced has_bias=False over 20 checked signals with zero biased entry and exit signals.
  - Recursive evidence is effectively stable for Bollinger, convergent with small EMA variance for Donchian, and materially unstable at startup 50 for Supertrend direction.
  - selected_candidate remains null and promotion, retuning, profitability and superiority claims remain forbidden.
  - Protected final holdout 20260801-20260930 remains unused and Phase 5 thresholds 0.006/-0.009 remain frozen.
  - PR #152 merged the maintenance-only archive guard as f989f778d8dfeb623fd09dba3dd5fe42e90505c6 after all required gates succeeded.
derived:
  - No v1 TradingView candidate qualifies for promotion from this historical evidence.
  - A changed Supertrend startup geometry would be a new prospective variant, not a correction to this frozen result.
  - The completed benchmark is durably archived and cannot be retriggered by maintenance changes.
unknown: []
conflicts: []
first_failure:
  marker: resolved
  evidence: Original lookahead evidence was incomplete due to analysis-only market-order pricing semantics; isolated repair completed successfully without changing benchmark results.
rejected_hypotheses:
  - Retune any v1 candidate on the consumed historical window.
  - Promote Bollinger merely because it ranked first among three losing strategies.
  - Reinterpret the lookahead repair as a new benchmark execution.
  - Use protected final holdout data before 2026-10-01T00:00:00Z.
changed_paths:
  - .github/workflows/ai-platform-tradingview-futures-historical-benchmark.yml
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-benchmark.md
validation:
  - command: immutable benchmark and repaired lookahead evidence review
    result: PASS
    evidence: workflows 29947929886 and 29958028584 preserve frozen metrics and complete has_bias=False evidence without rerunning backtests.
  - command: PR #152 repository gates and archive guard
    result: PASS
    evidence: Freqtrade CI 29959922194, zizmor 29959922230, and archive guard 29959922331 completed successfully before squash merge f989f778d8dfeb623fd09dba3dd5fe42e90505c6.
blockers: []
next_action: Keep this benchmark archived; do not retune or promote these v1 candidates, and require a separately declared prospective task for any changed strategy variant or future research execution.
```
