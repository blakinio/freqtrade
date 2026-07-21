# Experimental Model Historical Backtest Execution v1

This work package defines the guarded execution infrastructure for the two canonical research-only tracks created by the Experimental Model Research Foundation:

- `pytorch-research-v1` using `SeededPyTorchMLPRegressor` and `AiFrozenCandidateStrategy`;
- `rl-research-v1` using `LongOnlyReinforcementLearner` and `AiLongOnlyRLResearchStrategy`.

The infrastructure merge does **not** execute either backtest. Real execution is triggered only by a later pull request that adds exactly one canonical run-request file at:

`ai_platform/experimental_model_research/run-requests/historical-backtest-execution-v1.json`

The dedicated workflow listens only for the `opened` event on that path. A trigger pull request must target `develop`, originate from this repository, and contain exactly that one added file. This mirrors the one-shot Phase 6 execution boundary while keeping PyTorch and RL outside Phase 6.

## Frozen execution contract

The immutable infrastructure contract is:

`ai_platform/experimental_model_research/historical-backtest-execution-contract-v1.json`

It pins:

- exactly two tracks: `pytorch-research-v1` and `rl-research-v1`;
- semantic prediction window `20260301-20260630`;
- Freqtrade execution timerange `20260301-20260701`;
- Freqtrade download timerange `20250801-20260701`;
- strict historical-OOS scoring window `20260501-20260630`;
- Kraken spot data for `BTC/USDT` and `ETH/USDT` at `15m`, `1h`, and `4h`;
- fee ratio `0.002`;
- frozen thresholds `0.006/-0.009`;
- protected final holdout isolation;
- no Phase 6 membership or result consumption;
- no parameter, feature, reward, or threshold changes;
- no cross-track selection, promotion, live trading, profitability claim, or superiority claim.

The validator `ai_platform/scripts/experimental_model_historical_backtest_run_request.py` derives the only accepted request payload from the tracked contract and canonical repository inputs. The request binds SHA-256 hashes for each track's manifest, config, strategy implementation, and FreqAI model implementation, plus the execution contract itself.

A future trigger request can be generated only after this infrastructure is merged:

```bash
python -m ai_platform.scripts.experimental_model_historical_backtest_run_request \
  --print-canonical
```

The generated payload must be added unchanged as the sole file in the trigger pull request.

## Fail-closed workflow sequence

`.github/workflows/experimental-model-historical-backtest-execution.yml` performs three guarded stages.

### 1. Request validation

Before dependency installation, market-data access, or model execution, the workflow:

- checks out the exact trigger pull-request head SHA;
- proves the pull request adds exactly the canonical request path and no other file;
- validates the active bounded task checkpoint;
- validates the request byte-for-value against the canonical payload and frozen contract;
- uploads the request and contract as evidence.

The workflow has no `workflow_dispatch` trigger. Merging the infrastructure itself therefore cannot execute a real backtest.

### 2. Boundary-correct market data

Two independent jobs prepare `BTC/USDT` and `ETH/USDT` history. Each job:

- restores the exact boundary-correct v2 cache when available;
- otherwise restores only an allowed historical seed and completes the declared download through the exclusive July 1 stop;
- runs the merged historical-execution preflight verification for its pair;
- saves a pair-specific v2 cache only after successful verification.

No model backtest job starts until both pair jobs succeed.

Each model-execution job then restores both exact pair-specific v2 caches with cache-miss failure enabled and re-verifies combined pair/timeframe coverage immediately before execution.

## Exactly one independent backtest per track

After data verification, a two-entry matrix contains exactly one PyTorch job and one RL job. Each job calls the canonical runner once with `--stage backtest` and its frozen manifest.

The workflow validates that the resulting run summary contains:

- the expected track identity;
- the exact trigger head SHA as Git provenance;
- execution timerange `20260301-20260701`;
- download timerange `20250801-20260701`;
- exactly one executed Freqtrade command;
- that command is `backtesting`.

The workflow does not evaluate a cross-track winner and contains no model-selection policy.

## Strict historical-OOS evidence

For each successful backtest archive, the workflow invokes:

`ai_platform.scripts.experimental_model_oos_result_extractor`

The extractor applies the already-merged immutable scoring semantics:

- include only fully contained closed trades with `open_date >= 2026-05-01T00:00:00Z`;
- require `close_date < 2026-07-01T00:00:00Z`;
- exclude and count trades crossing either boundary;
- report profit, drawdown, trade count, and May/June stability from included trades only.

The workflow validates extraction authorization remains evidence-only, outside Phase 6, with final-holdout use, retuning, promotion, and profitability claims all disabled.

PyTorch and RL evidence is uploaded as two independent 90-day artifacts. No result assembler or cross-track selection stage is present. A zero-trade strict extraction, if schema-valid, remains an evidence result rather than being silently converted into a winner or profitability conclusion.

## Artifact boundary

Each successful track artifact contains at least:

- canonical run request;
- execution contract;
- canonical manifest;
- runner-copied manifest;
- run provenance;
- run summary;
- backtest log;
- Freqtrade backtest ZIP;
- strict historical-OOS extraction;
- immediately pre-execution market-data coverage evidence.

The trigger request itself should not be merged after execution. After artifacts are collected and independently reviewed, durable evidence must be persisted in a separate repository work package. This keeps the one-shot request from becoming a reusable execution switch in `develop`.

## Safety boundary

This infrastructure authorizes only the later explicitly requested historical backtest and strict evidence extraction for the two frozen tracks. It does not authorize:

- any access to the protected final holdout;
- threshold, model-parameter, feature, reward, or hyperparameter search;
- changing the completed Phase 6 comparison, candidates, policy, evidence, or outcome;
- selecting a winner between PyTorch and RL;
- promotion, live trading, or capital deployment;
- a profitability or superiority claim.

Any later evidence interpretation, follow-up research, promotion decision, or final-holdout evaluation requires a separate prospectively declared work package.
