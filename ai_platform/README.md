# AI Platform

This directory contains project-specific research and strategy code layered on top of upstream Freqtrade.

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
- no live-capital automation.

Files:

```text
ai_platform/
├── README.md
├── configs/
│   └── freqai-baseline.example.json
└── strategies/
    └── AiBaselineStrategy.py
```

## Environment

Install Freqtrade with FreqAI dependencies using the repository-supported installation method.

For a local editable Python environment, the relevant optional dependency group is `freqai`.

## Prepare a local configuration

Copy the tracked example into an ignored local config path:

```bash
cp ai_platform/configs/freqai-baseline.example.json user_data/config_ai_baseline.json
```

Do not commit real API credentials.

The example is already configured with:

```json
"dry_run": true
```

Keep it that way for the baseline phases.

## Download baseline data

Example:

```bash
freqtrade download-data \
  --config user_data/config_ai_baseline.json \
  --pairs BTC/USDT ETH/USDT \
  --timeframes 15m 1h 4h \
  --days 240
```

The exact historical period used for an experiment must be recorded with the result.

## Run a baseline backtest

Provide an explicit timerange appropriate to the downloaded data:

```bash
freqtrade backtesting \
  --config user_data/config_ai_baseline.json \
  --strategy AiBaselineStrategy \
  --strategy-path ai_platform/strategies \
  --freqaimodel LightGBMRegressor \
  --timerange <YYYYMMDD-YYYYMMDD>
```

A profitable backtest is not sufficient for promotion. Follow the validation roadmap before interpreting a candidate as robust.

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

1. reproducible experiment manifest;
2. out-of-sample evaluation;
3. walk-forward evaluation;
4. `lookahead-analysis`;
5. `recursive-analysis`;
6. drawdown and minimum-trade-count gates.

See `docs/ai_platform/ROADMAP.md`.

## Design intent

The baseline strategy is deliberately simple. Its purpose is to prove the research pipeline and establish a benchmark. Complexity should be added only when it improves out-of-sample robustness.
