# Residual PyTorch runtime smoke

## Decision boundary

P1 answers one technical question only: whether `ResidualPyTorchRegressor` can complete its supported FreqAI lifecycle on deterministic synthetic data.

The only allowed outcomes are:

- `runtime_supported`;
- `runtime_not_supported`;
- `runtime_inconclusive`.

No outcome is evidence of trading quality, profitability, superiority, promotion readiness or production readiness.

## Data boundary

The smoke creates deterministic synthetic tabular rows beginning on `2025-01-01T00:00:00Z`. It performs no exchange request and uses no market record.

It explicitly records that it does not use:

- consumed historical OOS `20260501-20260630`;
- protected final holdout `20260801-20260930`.

## Lifecycle checks

The dedicated script resolves the model through `FreqaiModelResolver.load_freqaimodel` and executes on CPU:

1. model construction and standalone forward;
2. `fit` on one synthetic target;
3. inherited FreqAI `predict`;
4. trainer checkpoint `save`;
5. checkpoint `load` through the trainer lifecycle;
6. fresh wrapper reconstruction and repeated `predict`;
7. exact prediction equality before and after restore.

When `torch.cuda.is_available()` is true, the same lifecycle runs on CUDA without forcing or emulating a GPU. Otherwise CUDA is reported as skipped.

## Reproducibility and integrity

For each executed device, two independent runs use the frozen seed and runtime. The smoke requires identical state dictionaries and predictions.

It also verifies:

- input and output tensor shapes;
- positive parameter count;
- finite weights and predictions;
- checkpoint metadata;
- exactly one target;
- checkpoint file creation and size.

## Fail-closed checks

The package requires explicit failure for:

- multiple targets;
- zero feature columns;
- mismatched feature and label row counts;
- missing checkpoint files;
- invalid model configuration;
- continual learning.

The model hardening in this package changes no frozen model parameter. It only makes unsupported input and lifecycle modes fail explicitly and records the parameter count in checkpoint metadata.

## Execution

```bash
python -m ai_platform.scripts.residual_pytorch_runtime_smoke \
  --output residual-pytorch-runtime-smoke-report.json
```

The dedicated GitHub Actions workflow installs the `freqai` dependency profile, validates the package, runs the smoke and uploads the machine-readable report even when the smoke fails.

## Forbidden interpretation

P1 does not authorize market-data training, backtesting, Hyperopt, feature search, OOS scoring, protected-holdout access, dry-run deployment, live trading or model promotion.
