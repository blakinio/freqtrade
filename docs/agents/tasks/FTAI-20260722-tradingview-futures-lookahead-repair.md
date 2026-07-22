---
task_id: FTAI-20260722-tradingview-futures-lookahead-repair
status: implementing
branch: fix/tradingview-futures-lookahead-config-v1
base_branch: develop
created: 2026-07-22
updated: 2026-07-22
related_pr: ""
owned_paths:
  - ai_platform/research/tradingview/futures-historical-lookahead-repair-v1.json
  - ai_platform/research/tradingview/run-requests/futures-historical-lookahead-repair-v1.json
  - .github/workflows/ai-platform-tradingview-futures-lookahead-repair.yml
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-lookahead-repair.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_BENCHMARK.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-benchmark.md
search_first:
  - TradingView futures historical benchmark lookahead repair
  - PR 132 benchmark evidence
---

# TradingView Futures Historical Lookahead Repair

## Goal

Repair only the missing lookahead-analysis evidence from the completed TradingView futures historical benchmark execution associated with PR #132, without rerunning backtests, changing the historical ordering, mutating strategy logic, retuning parameters, promoting any candidate, or touching the protected final holdout.

## Proven source evidence

The successful benchmark workflow run `29947929886` executed all three frozen candidates and uploaded artifact `8541078835` with digest `sha256:9cb7c603d6c1f612a783907aa6ca112c7f946efff80abdd38ad283bed1ad822c`.

The source benchmark execution head is `9c03faedea870cea78b46672545fb4a4ba371e6f`.

All three backtests completed under the frozen benchmark geometry. However, every lookahead-analysis invocation produced no CSV row because Freqtrade internally forced market order types while the frozen benchmark config retained `entry_pricing.price_side = same`; Freqtrade requires `entry_pricing.price_side = other` for market entry orders.

This repair is analysis-only. The original benchmark config and backtest evidence remain immutable.

## Frozen repair boundary

- source benchmark: `tradingview-futures-historical-benchmark-v1`;
- candidates unchanged:
  1. `TVDonchianBreakoutStrategy`;
  2. `TVSupertrendStrategy`;
  3. `TVBollingerMeanReversionStrategy`;
- exchange: `krakenfutures`;
- futures / isolated / USD;
- pairs: `BTC/USD:USD`, `ETH/USD:USD`;
- timeframe: `15m`;
- analysis timerange: `20260301-20260701`;
- fee: `0.002`;
- protected final holdout `20260801-20260930` remains forbidden;
- no backtest rerun;
- no ranking change;
- no strategy mutation or retuning;
- no automatic validation or promotion claim.

The only permitted compatibility delta is a derived lookahead-only config changing `entry_pricing.price_side` from `same` to `other`, because `lookahead-analysis` itself forces market entry orders. The workflow must prove that this is the only config delta before executing analysis.

## Required outcome

For every candidate preserve a lookahead log, CSV when produced, parsed strategy row, explicit bias result, exact repair execution commit, source benchmark identifiers, frozen market/data geometry, and the exact compatibility delta.

Incomplete output must fail the repair workflow. A complete row reporting bias is valid evidence but is not an automatic validation or promotion authorization.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-22T23:10:00+02:00
head: 73f612557fd2a14d2ab3f8d413a32853b1e7f554
branch: fix/tradingview-futures-lookahead-config-v1
pr: none
status: implementing
context_routes:
  - docs/ai_platform/TRADINGVIEW_FUTURES_HISTORICAL_BENCHMARK.md
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-historical-benchmark.md
owned_paths:
  - ai_platform/research/tradingview/futures-historical-lookahead-repair-v1.json
  - ai_platform/research/tradingview/run-requests/futures-historical-lookahead-repair-v1.json
  - .github/workflows/ai-platform-tradingview-futures-lookahead-repair.yml
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-lookahead-repair.md
proven:
  - PR #132 merged to develop as 73f612557fd2a14d2ab3f8d413a32853b1e7f554 after all required CI succeeded.
  - Workflow run 29947929886 completed the three frozen backtests and immutable artifact upload.
  - Source artifact 8541078835 has digest sha256:9cb7c603d6c1f612a783907aa6ca112c7f946efff80abdd38ad283bed1ad822c.
  - All three lookahead logs terminate at the same Freqtrade configuration incompatibility caused by forced market entry orders with entry_pricing.price_side=same.
  - Recursive analysis completed for all three candidates and requires review; the repair scope does not rerun or reinterpret it.
derived:
  - A separate analysis-only repair preserves benchmark provenance better than modifying or rerunning the frozen backtest execution.
  - The compatibility config must be derived from the validated frozen config and prove a single allowed field delta.
unknown:
  - Whether lookahead-analysis produces a complete CSV row for all three candidates after the compatibility override.
  - Whether any candidate is reported with lookahead bias.
conflicts: []
first_failure:
  marker: lookahead-config-incompatibility
  evidence: Freqtrade reports that market entry orders require entry_pricing.price_side=other; no lookahead CSV is produced.
rejected_hypotheses:
  - Change the frozen benchmark config and reinterpret the already-produced backtests.
  - Rerun the historical backtests merely to repair lookahead evidence.
  - Retune or mutate candidates after observing the benchmark ordering.
changed_paths:
  - ai_platform/research/tradingview/futures-historical-lookahead-repair-v1.json
  - docs/agents/tasks/FTAI-20260722-tradingview-futures-lookahead-repair.md
validation:
  - command: GitHub Actions on repair implementation PR
    result: NOT_RUN
    evidence: Repair workflow not yet added.
blockers: []
next_action: Add the isolated lookahead-repair workflow, open an implementation PR with no run-request, merge only after CI is green, then create a separate one-file repair run-request PR and inspect immutable lookahead evidence.
```
