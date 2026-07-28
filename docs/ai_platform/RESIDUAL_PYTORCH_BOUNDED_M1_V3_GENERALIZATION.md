# Residual PyTorch bounded M1 v3 pair generalization

## Decision

V3 is a separate, development-only generalization cohort for the three frozen bounded-M1
regressors. It changes only the two-pair market cohort from `BTC/USDT` + `ETH/USDT` to
`SOL/USDT` + `XRP/USDT`.

This package does not select a winner, promote a model, retune a parameter, modify a
feature formula, consume historical OOS, access the protected final holdout or authorize
live trading.

## Why a two-pair cohort

The v2 FreqAI geometry contains one primary pair and one correlated pair. Adding all
markets to one correlation list would increase the feature count and confound pair
generalization with feature expansion.

V3 therefore uses another fixed two-pair cohort. The mandatory pre-fit audit requires:

- exactly `272` expanded and transformed features per pair;
- the same primary/correlated-role normalized feature-name SHA-256 as terminal v2:
  `c65ec5f29963f1bb541f1c5416b52a4be8bfe2a1328a04577c17eea197d2945c`;
- finite raw and transformed matrices;
- exactly 12 trailing target-null rows;
- at least 1,000 eligible training rows per pair;
- no liquidation-derived feature.

A mismatch fails closed before any comparator is fitted.

## Frozen inputs

| Boundary | Value |
|---|---|
| Source evidence | guarded run `30340242201` |
| Training window | `2025-12-01T00:00:00Z` through `2026-03-01T00:00:00Z` exclusive |
| Development window | `2026-03-01T00:00:00Z` through `2026-05-01T00:00:00Z` exclusive |
| Pairs | `SOL/USDT`, `XRP/USDT` |
| Timeframes | `15m`, `1h`, `4h` |
| Features | same finite v2 strategy, exactly 272 after expansion |
| Target | `&-future_return`, offsets `t+1` through `t+12` |
| Thresholds | entry `0.006`, exit `-0.009` |
| Fee | `0.002` per side |
| Executions | exactly one per track |

Model architectures, seeds, training parameters, split geometry and strategy remain
unchanged. New FreqAI identifiers isolate the v3 model directories from v2 evidence.

## Execution protocol

Infrastructure is merged first. A later trigger PR must add exactly:

```text
ai_platform/experimental_model_research/run-requests/residual-pytorch-bounded-m1-generalization-v3.json
```

The request is canonical and SHA-256 binds the contract, configs, manifests, strategy,
instrumentation and model wrappers. The workflow verifies scope before dependency
installation or market-data access.

The trigger PR is evidence plumbing and must be closed without merge after terminal
artifact collection.

## Interpretation boundary

V3 measures whether the frozen research procedure behaves coherently on a new pair
cohort. Results are descriptive only. They cannot be used to reopen Phase 6, claim
profitability or superiority, select a production model, authorize OOS/holdout access or
start dry-run/live execution.
