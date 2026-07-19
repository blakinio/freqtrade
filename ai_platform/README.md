# AI Platform

This directory contains project-specific research and strategy code layered on top of upstream
Freqtrade.

It is intentionally separated from `freqtrade/` core to keep upstream synchronization manageable.

## Current scope

The current baseline is research-only:

- spot trading;
- BTC/USDT and ETH/USDT;
- 15m base timeframe;
- 1h and 4h context;
- FreqAI with `LightGBMRegressor`;
- long-only strategy;
- dry-run configuration;
- reproducible experiment manifests and provenance;
- no live-capital automation.

Files:

```text
ai_platform/
├── README.md
├── configs/
│   └── freqai-baseline.example.json
├── experiments/
│   ├── README.md
│   ├── baseline-v1.json
│   └── schema-v1.json
├── scripts/
│   └── run_experiment.py
└── strategies/
    └── AiBaselineStrategy.py
```

## Environment

Install Freqtrade with FreqAI dependencies using the repository-supported installation method.

For a local editable Python environment, the relevant optional dependency group is `freqai`.

## Preferred reproducible workflow

The pinned baseline experiment is `ai_platform/experiments/baseline-v1.json`.

Download the declared historical data and run the backtest:

```bash
python ai_platform/scripts/run_experiment.py \
  ai_platform/experiments/baseline-v1.json \
  --stage all
```

Run only the backtest when the required data already exists:

```bash
python ai_platform/scripts/run_experiment.py \
  ai_platform/experiments/baseline-v1.json \
  --stage backtest
```

The runner records the Git commit, hashes of the manifest/config/strategy, exact commands, logs,
backtest archive, and a machine-readable scalar metric summary below `ai_platform/artifacts/`.
Generated artifacts are ignored by Git.

The baseline manifest uses a fixed `0.002` fee ratio, which Freqtrade applies on entry and exit.
This is a research assumption, not a statement of the current fee schedule of any exchange.

See `ai_platform/experiments/README.md` for the manifest and artifact contract.

## Prepare a local dry-run configuration

For interactive dry-run trading, copy the tracked example into an ignored local config path:

```bash
cp ai_platform/configs/freqai-baseline.example.json user_data/config_ai_baseline.json
```

Do not commit real API credentials.

The example is configured with:

```json
"dry_run": true
```

Keep it that way for the baseline phases.

## Manual data download and backtest

Manual commands are useful for debugging, but a promoted experiment should use a pinned manifest.

Example data download:

```bash
freqtrade download-data \
  --config user_data/config_ai_baseline.json \
  --pairs BTC/USDT ETH/USDT \
  --timeframes 15m 1h 4h \
  --timerange 20250801-20260630
```

Example backtest:

```bash
freqtrade backtesting \
  --config user_data/config_ai_baseline.json \
  --strategy AiBaselineStrategy \
  --strategy-path ai_platform/strategies \
  --freqaimodel LightGBMRegressor \
  --timerange 20260101-20260630 \
  --fee 0.002
```

A profitable backtest is not sufficient for promotion. Follow the validation roadmap before
interpreting a candidate as robust.

## Run dry-run trading

```bash
freqtrade trade \
  --config user_data/config_ai_baseline.json \
  --strategy AiBaselineStrategy \
  --strategy-path ai_platform/strategies \
  --freqaimodel LightGBMRegressor
```

## Required next validation work

Before this baseline can be considered validated, implement and run:

1. out-of-sample evaluation policy;
2. walk-forward evaluation;
3. `lookahead-analysis`;
4. `recursive-analysis`;
5. drawdown and minimum-trade-count gates.

See `docs/ai_platform/ROADMAP.md`.

## Design intent

The baseline strategy is deliberately simple. Its purpose is to prove the research pipeline and
establish a benchmark. Complexity should be added only when it improves out-of-sample robustness.
