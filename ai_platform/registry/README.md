# Experiment Registry

The registry is the durable local memory for AI-platform research.

It separates:

1. **experiment definitions** — semantic combinations of strategy/config/model/features/target/data windows;
2. **experiment runs** — concrete executions of a definition with Git SHA, Freqtrade version, metrics, and optional validation evidence.

The default SQLite database is:

```text
ai_platform/artifacts/registry/registry.sqlite3
```

`ai_platform/artifacts/` is ignored by Git. The database is an operational research artifact, not source code.

## Definition contract

Registry definitions use `schema-v1.json`.

The baseline definition is:

```text
ai_platform/registry/baseline-v1.json
```

A definition adds explicit research dimensions that are not safely inferred from strategy source code:

- `strategy_version`;
- `feature_set_id`;
- `target_id`;
- human-readable feature and target descriptions.

The semantic fingerprint also includes hashes of the strategy, config, and experiment manifest; the FreqAI identifier; model type; training/evaluation windows; pairs; timeframes; model parameters; and fee assumption.

Changing any of those values produces a different fingerprint.

## Initialize

```bash
python ai_platform/scripts/registry.py init
```

## Detect a duplicate definition

Run this before launching an expensive experiment:

```bash
python ai_platform/scripts/registry.py check-definition \
  ai_platform/registry/baseline-v1.json
```

Exit codes:

- `0` — definition is new;
- `2` — the same semantic definition already exists in the registry;
- `1` — invalid input or registry error.

## Register a backtest run

```bash
python ai_platform/scripts/registry.py register \
  ai_platform/registry/baseline-v1.json \
  --run-summary ai_platform/artifacts/<experiment>/<run>/run-summary.json
```

The registry verifies that the run-summary manifest/config/strategy hashes still match the current definition before accepting the run.

## Register a validated run

```bash
python ai_platform/scripts/registry.py register \
  ai_platform/registry/baseline-v1.json \
  --run-summary ai_platform/artifacts/<experiment>/<run>/run-summary.json \
  --validation-report ai_platform/artifacts/validation/<validation>/<run>/validation-report.json
```

A run with `promotion_allowed: true` is recorded as `validated` only when it also has:

- a full 40-character Git commit SHA;
- a non-empty FreqAI identifier from the exact hashed config;
- a resolved Freqtrade version.

This enforces the repository requirement that validated candidates map back to code and model identity.

## Compare runs

All registered runs:

```bash
python ai_platform/scripts/registry.py compare
```

Filter examples:

```bash
python ai_platform/scripts/registry.py compare --model LightGBMRegressor
python ai_platform/scripts/registry.py compare --feature-set baseline-price-trend-momentum-volume-v1
python ai_platform/scripts/registry.py compare --target future-average-return-v1
python ai_platform/scripts/registry.py compare --timeframe 1h
python ai_platform/scripts/registry.py compare --promotion-status validated
```

Results are returned as structured JSON ordered by holdout profit when available, then backtest profit.

## Lifecycle

The registry records the current evidence-based state:

```text
experiment -> candidate -> validated
```

Dry-run and any later live states remain separate future work packages. Registry storage does not itself promote or execute a strategy.
