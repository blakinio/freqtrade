# RL-v2 Historical Training Execution

## Status

`rl-v2-historical-training-execution-v1` defines guarded infrastructure for exactly one later historical RL-v2 FreqAI training/backtest execution.

The infrastructure merge is intentionally inert. It does not add the canonical run-request file and therefore cannot trigger model training, backtesting, market-data download, or result production.

Execution contract:

`ai_platform/experimental_model_research/rl-v2-historical-training-execution-contract-v1.json`

Canonical request validator/generator:

`ai_platform.scripts.rl_v2_historical_training_execution_run_request`

Request-triggered workflow:

`.github/workflows/ai-platform-rl-v2-historical-training-execution.yml`

Future one-shot request path:

`ai_platform/experimental_model_research/run-requests/rl-v2-historical-training-execution-v1.json`

## Frozen RL-v2 binding

The execution path is bound to the already frozen research surface:

- training configuration: `rl-v2-training-configuration-v1`;
- model: `DesiredPositionReinforcementLearner`;
- strategy: `AiDesiredPositionRLResearchStrategy`;
- Stable-Baselines3 through FreqAI;
- PPO with `MlpPolicy`;
- long-only spot semantics;
- `0=target_flat`, `1=target_long`;
- transition and reward semantics owned by `ai_platform.scripts.rl_v2_synthetic_reference`.

The canonical request contains SHA-256 bindings for the execution contract, training-configuration descriptor, base config, model, strategy, validator, and workflow. A later trigger request fails closed if any bound input changes.

## Prospectively frozen historical geometry

The execution geometry was declared before any RL-v2 result-producing run:

```text
download timerange:   20250801-20260501
execution timerange:  20260301-20260501
semantic evidence:    20260301-20260430
train_period_days:    90
backtest_period_days: 61
exchange:             Kraken spot
pairs:                BTC/USDT, ETH/USDT
timeframes:           15m, 1h, 4h
fee:                   0.002
```

Freqtrade timerange stops are treated as exclusive. Both market-data and execution ranges stop at `2026-05-01T00:00:00Z`, before the consumed May-June OOS window begins.

The base committed training configuration remains immutable and contains no execution geometry. Immediately before a later authorized execution, the validator may materialize a temporary runtime copy that adds only:

```text
freqai.train_period_days = 90
freqai.backtest_period_days = 61
```

No `timerange` or `live_retrain_hours` key is added to the committed or temporary config; the historical execution timerange remains an explicit CLI argument controlled by the frozen execution contract.

## Evidence classification

March-April 2026 output is classified only as:

`historical_development_evidence`

It is not a fresh project-wide strict-OOS window and is not protected final validation. The workflow intentionally does not call `experimental_model_oos_result_extractor` and does not produce an automatic ranking, promotion, profitability, or superiority conclusion.

A negative result, zero-trade result, or execution failure remains valid evidence and must not be silently converted into a positive candidate decision.

## Consumed OOS and final-holdout isolation

The following remain forbidden:

- consumed historical OOS `20260501-20260630`;
- protected final holdout `20260801-20260930`.

The data workflow uses a dedicated cache namespace with no fallback restore keys. It may restore only caches created from the exact pre-May contract/config/model/strategy identity. On cache miss it downloads only `20250801-20260501`, verifies the exclusive May 1 stop, and saves the cache only after coverage validation.

This prevents reuse of the older experimental caches that contain data through July 2026.

Frozen Phase 5 thresholds remain `0.006/-0.009` and are not RL-v2 tuning inputs. Completed Phase 6 remains authoritative with `selected_model = null`; RL-v2 is not a Phase 6 member.

## One-shot request separation

The workflow listens only for a pull request **opened** against `develop` that touches the canonical request path.

Before installing runtime dependencies or accessing market data, it:

1. checks out the exact trigger PR head;
2. proves the diff adds exactly one file: the canonical request path;
3. validates the bounded task checkpoint;
4. validates the request byte-for-value against the generated canonical payload and frozen hashes.

The infrastructure implementation PR does not contain that request path, so merging infrastructure cannot execute the model.

After infrastructure is merged and frozen, the canonical request can be generated with:

```bash
python -m ai_platform.scripts.rl_v2_historical_training_execution_run_request \
  --print-canonical
```

A later separate trigger PR must add that generated JSON unchanged as its only changed file.

## Guarded execution sequence

After a valid future trigger:

1. two independent data jobs prepare BTC and ETH history using only the dedicated pre-OOS cache namespace;
2. each pair is verified across `15m`, `1h`, and `4h` before caching;
3. the execution job restores both exact verified caches and re-verifies combined coverage;
4. the canonical request is revalidated immediately before execution;
5. a temporary config is materialized from the frozen base config;
6. exactly one `freqtrade backtesting` command runs for `20260301-20260501`;
7. the raw backtest archive, logs, effective temporary config, data coverage, and non-OOS provenance metadata are uploaded as evidence.

No strict-OOS extractor, cross-track assembler, ranking stage, promotion stage, or live-trading step exists in this workflow.

## Validation

Infrastructure validation is dependency-light and non-result-producing:

```bash
pytest -q tests/ai_platform/test_rl_v2_historical_training_execution.py
python -m ai_platform.scripts.rl_v2_historical_training_execution_run_request \
  --print-canonical
```

These checks validate contracts, hashes, one-shot request semantics, temporary config materialization, pre-OOS boundaries, workflow guards, and evidence labeling without training a model or accessing market data.

A successful infrastructure validation is authorization evidence for the later canonical one-file trigger only. It is not model-performance evidence and does not itself execute RL-v2.
