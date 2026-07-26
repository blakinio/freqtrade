# Residual PyTorch custom-model research architecture

## Decision

The first new custom model is `ResidualPyTorchRegressor`: a deterministic, single-target, tabular residual MLP that remains compatible with the existing FreqAI regression contract.

The initial package intentionally does not implement multi-target prediction, temporal windows, model stacking, market-data access, training execution or model promotion. Those capabilities require separate contracts because they change data shape, leakage risk and evaluation geometry.

## Why this model is first

The current project-specific PyTorch baseline only adds process-level seeding around the upstream example MLP. The upstream block is feed-forward but does not add its input back to its output. The new candidate adds an explicit residual skip connection while retaining the same one-row feature tensor and one-target prediction interface.

This is the smallest architecture change that can test whether a better neural tabular inductive bias adds value without simultaneously changing targets, temporal sampling, strategy thresholds or execution behavior.

## Runtime boundary

```text
OHLCV and accepted contextual data
        |
        v
Frozen feature engineering
        |
        v
FreqAI normalization and chronological split
        |
        v
ResidualPyTorchRegressor
  - input LayerNorm
  - linear projection
  - GELU
  - N pre-normalized residual feed-forward blocks
  - output LayerNorm
  - one regression head
        |
        v
&-future_return prediction
        |
        v
Frozen deterministic strategy thresholds
        |
        v
Independent deterministic risk and Freqtrade execution
```

The model predicts one continuous target. It does not emit orders, alter thresholds or bypass `do_predict`, strategy or risk gates.

## Frozen M1 architecture

- input: one normalized FreqAI feature vector per candle;
- output: one value for `&-future_return`;
- hidden width: `128`;
- residual blocks: `3`;
- expansion factor: `2`;
- activation: `GELU`;
- dropout: `0.1`;
- optimizer: `AdamW`;
- learning rate: `0.0003`;
- weight decay: `0.0001`;
- loss: `SmoothL1Loss(beta=0.01)`;
- seed: `42`;
- continual learning: disabled;
- data split shuffle: disabled.

These values are implementation defaults, not selected or validated hyperparameters. Changing them requires a separate prospectively declared tuning package.

## File map

| Path | Role |
|---|---|
| `ai_platform/freqaimodels/residual_mlp_components.py` | Residual block and network |
| `ai_platform/freqaimodels/ResidualPyTorchRegressor.py` | FreqAI model adapter and trainer construction |
| `ai_platform/configs/freqai-residual-pytorch-research.example.json` | stopped, dry-run research configuration |
| `ai_platform/experiments/residual-pytorch-research-v1.json` | inert experiment declaration |
| `ai_platform/experimental_model_research/residual-pytorch-research-contract-v1.json` | machine-readable boundaries and roadmap |
| `ai_platform/scripts/residual_pytorch_research_contract.py` | fail-closed validator |
| `tests/ai_platform/test_residual_pytorch_research_contract.py` | static and optional tensor tests |

## Evaluation comparators

M1 must be evaluated against both:

1. `LightGBMRegressor`, as the simple tree baseline;
2. `SeededPyTorchMLPRegressor`, as the current neural baseline.

A comparison is valid only when feature set, target, strategy, pair universe, timeframes, fees, training windows and evaluation windows are identical.

## Required evidence

Model diagnostics:

- MAE;
- Smooth L1 loss;
- directional accuracy;
- Spearman rank information coefficient;
- prediction distribution and saturation;
- train-versus-validation loss behavior.

Trading evidence:

- strict out-of-sample net return after fees;
- maximum drawdown;
- cross-window stability;
- trade count;
- profit factor as a diagnostic;
- fee sensitivity;
- pair-level concentration;
- lookahead-analysis and recursive-analysis results.

A single profitable backtest is insufficient.

## Staged implementation plan

### P0 — Foundation

Delivered by this package:

- architecture and isolation contract;
- residual network and FreqAI adapter;
- safe example config;
- inert experiment manifest;
- fail-closed validator;
- dependency-light tests.

No market data or model execution is authorized.

### P1 — Runtime smoke preflight

Separate task:

- install the dependency-closed Linux profile;
- resolve the model through `freqaimodel_path`;
- instantiate CPU and available CUDA paths;
- run synthetic forward, fit, save, load and predict checks;
- verify deterministic repeatability for the same seed;
- record parameter count, tensor shapes and runtime provenance.

No exchange data, backtest or performance claim.

### P2 — Data and target audit

Separate task:

- freeze a development-only historical window that excludes consumed historical OOS and the protected final holdout;
- verify chronological alignment and target look-forward semantics;
- record feature count after FreqAI expansion;
- check NaN handling, outliers and label distribution;
- confirm no liquidation feature enters until its historical source and candle-alignment contract are accepted.

### P3 — Bounded M1 execution

Separate request-gated task:

- execute fixed seeds declared before outcomes are known;
- run LightGBM, seeded MLP and residual MLP on identical geometry;
- retain raw logs, models, predictions, configs, hashes and backtest archives;
- produce descriptive evidence only;
- do not tune from the evaluation results.

### P4 — Walk-forward robustness

Separate task after P3:

- multiple chronological folds;
- pair-level and fold-level metrics;
- fee and threshold perturbation diagnostics without changing frozen Phase 5 thresholds;
- minimum trade count and drawdown gates;
- explicit `supported`, `not_supported` or `inconclusive` decision for continued research.

This still does not authorize dry-run deployment.

### P5 — Multi-task residual model

Blocked until a dedicated multi-target contract defines:

- exact target columns and horizons;
- per-head losses and weights;
- prediction-column mapping into FreqAI;
- missing-label policy;
- no-leakage alignment;
- strategy consumption of each head.

Suggested heads are expected return, directional probability, realized volatility and return quantiles. They must not be added opportunistically to M1.

### P6 — TCN sequence model

Blocked until a sequence dataset contract defines:

- causal window construction;
- per-pair window boundaries;
- no crossing of train/test or pair boundaries;
- padding and warm-up behavior;
- feature normalization location;
- inference latency and memory limits.

### P7 — OOF ensemble

Blocked until base models have immutable out-of-fold predictions. The meta-model may consume only OOF predictions during training and must have a deterministic fallback when a component prediction is missing or stale.

### P8 — PatchTST or TFT

Deferred. These models are justified only after simpler models fail to capture stable signal and the accepted dataset is large enough to support additional capacity.

## Promotion boundary

The whole track remains:

```text
experiment only
```

Any move to `candidate`, `validated` or `dry-run` requires a separate reviewed package and appropriate evidence. Live-capital operation is outside this architecture.

## Isolation

This work must not:

- reopen or reinterpret completed Phase 6;
- change authoritative `selected_model = null`;
- change frozen entry `0.006` or exit `-0.009` thresholds;
- use consumed historical OOS `20260501-20260630`;
- use protected final holdout `20260801-20260930`;
- rank PyTorch against RL retrospectively;
- add liquidation features before accepted historical-source and synchronization contracts;
- claim profitability, superiority or production readiness.
