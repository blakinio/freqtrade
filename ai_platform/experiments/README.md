# Experiment Manifests

Experiment manifests pin the inputs needed to reproduce a research run.

The current contract is `schema_version: 1` and is described by `schema-v1.json`.

## Required identity

Each manifest records:

- experiment ID;
- tracked Freqtrade config path;
- strategy class and strategy path;
- FreqAI model;
- backtest timerange;
- historical-data download timerange;
- pairs;
- timeframes;
- fixed fee assumption;
- artifact output root.

The runner additionally records at execution time:

- Git commit;
- SHA-256 of the manifest;
- SHA-256 of the config;
- SHA-256 of the strategy source;
- executed commands;
- start/end timestamps;
- result archive name;
- scalar strategy metrics extracted from the Freqtrade backtest archive.

## Fee semantics

The manifest `fee` value is passed directly to Freqtrade's `--fee` option.
Freqtrade applies this ratio on both entry and exit.

The baseline value `0.002` is a fixed research assumption of 0.2% per side. It is not a claim
about the current fee schedule of the configured exchange. Later experiments should explicitly
model the fee tier and slippage assumptions they intend to validate.

## Baseline periods

`baseline-v1.json` uses:

- data download: `20250801-20260630`;
- evaluated backtest: `20260101-20260630`.

The earlier download start provides history before the evaluated period for the FreqAI training
window and startup candles. The evaluation window remains fixed so repeated runs can be compared.

## Running

Download data and execute the pinned backtest:

```bash
python ai_platform/scripts/run_experiment.py \
  ai_platform/experiments/baseline-v1.json \
  --stage all
```

Backtest only, when data is already present:

```bash
python ai_platform/scripts/run_experiment.py \
  ai_platform/experiments/baseline-v1.json \
  --stage backtest
```

Generated artifacts are written below `ai_platform/artifacts/` and are ignored by Git.

## Artifact layout

```text
ai_platform/artifacts/
└── <experiment_id>/
    └── <run_id>/
        ├── manifest.json
        ├── provenance.json
        ├── download.log          # when download stage is run
        ├── backtest.log          # when backtest stage is run
        ├── backtest-result-*.zip # produced by Freqtrade
        ├── backtest-result-*.meta.json
        └── run-summary.json
```

A failed command still produces `run-summary.json` with `status: failed` when the run directory
has already been created.
