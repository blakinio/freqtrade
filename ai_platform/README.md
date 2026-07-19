# AI Platform

This directory contains project-specific AI/FreqAI research and strategy code layered on top of
upstream Freqtrade.

It is intentionally separated from `freqtrade/` core to keep upstream synchronization manageable
and to preserve a strict boundary between research tooling and trading-engine code.

## Current scope

Phases 0 through 4 of the AI Trading Platform roadmap are implemented. Phase 5 is active through its
first reviewable work package: staged signal-threshold optimization.

The current system is research-only:

- spot trading;
- BTC/USDT and ETH/USDT baseline universe;
- 15m base timeframe with 1h and 4h context;
- FreqAI with `LightGBMRegressor` as the baseline model;
- long-only strategies;
- dry-run configuration;
- reproducible experiment manifests and provenance;
- walk-forward and final-holdout validation;
- automated lookahead and recursive analysis;
- promotion gates;
- durable SQLite experiment registry and duplicate detection;
- bounded deterministic strategy discovery;
- staged entry-threshold Hyperopt with a frozen final holdout and local perturbation checks;
- no live-capital automation.

The repository contains infrastructure for research and validation. It does not claim that any
strategy is profitable or ready for live capital merely because the pipeline exists or CI passes.

## Project layout

```text
ai_platform/
├── README.md
├── configs/
│   └── freqai-baseline.example.json
├── discovery/
│   ├── README.md
│   ├── search-space-schema-v1.json
│   └── search-space-v1.json
├── experiments/
│   ├── README.md
│   ├── baseline-v1.json
│   └── schema-v1.json
├── optimization/
│   ├── README.md
│   ├── baseline-signal-thresholds-v1.json
│   └── schema-v1.json
├── registry/
│   ├── README.md
│   ├── baseline-v1.json
│   └── schema-v1.json
├── scripts/
│   ├── discovery.py
│   ├── registry.py
│   ├── run_experiment.py
│   ├── run_optimization.py
│   └── run_validation.py
├── strategies/
│   └── AiBaselineStrategy.py
└── validation/
    ├── baseline-validation-v1.json
    └── schema-v1.json
```

Generated research artifacts are written below `ai_platform/artifacts/` and are ignored by Git.

## Safety invariants

- Do not commit exchange credentials or other secrets.
- Research configs must remain `dry_run: true`.
- The baseline and generated discovery strategies remain spot-only and long-only.
- Project-specific code stays outside upstream `freqtrade/` core unless a separately reviewed core
  change is explicitly required.
- A profitable backtest is never sufficient for promotion.
- Failed validation gates block promotion.
- Discovery candidates cannot bypass the experiment, validation, and registry pipeline.
- Hyperopt and parameter selection cannot use the frozen final holdout.
- A stable optimization result is not promoted automatically; it still requires final validation.
- No work package may silently transition from research/dry-run into live trading.

## Environment

Install Freqtrade with FreqAI dependencies using the repository-supported installation method.
For a local editable Python environment, the relevant optional dependency group is `freqai`.
Hyperopt dependencies are also required when running Phase 5 optimization.

## Reproducible baseline experiment

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
backtest archive, and a machine-readable scalar metric summary.

The baseline manifest uses a fixed `0.002` fee ratio, which Freqtrade applies on entry and exit.
This is a research assumption, not a statement of the current fee schedule of any exchange.

See `ai_platform/experiments/README.md` for the manifest and artifact contract.

## Validation pipeline

The baseline validation plan is `ai_platform/validation/baseline-validation-v1.json`.

Run the validation orchestrator:

```bash
python ai_platform/scripts/run_validation.py \
  ai_platform/validation/baseline-validation-v1.json
```

The pipeline performs separate walk-forward folds and a final holdout, then applies configured
performance gates together with lookahead and recursive-analysis checks. It emits a machine-readable
validation report with `promotion_allowed`.

The holdout is evidence for final evaluation and must not become tuning data in Phase 5.

## Experiment registry

Initialize the durable local registry:

```bash
python ai_platform/scripts/registry.py init
```

Check whether a semantic experiment definition already exists before an expensive run:

```bash
python ai_platform/scripts/registry.py check-definition \
  ai_platform/registry/baseline-v1.json
```

Compare registered results:

```bash
python ai_platform/scripts/registry.py compare
```

The registry links experiment definitions and runs to strategy/config/manifest hashes, FreqAI
identifier, model, feature/target identity, Git commit, Freqtrade version, metrics, and validation
evidence.

See `ai_platform/registry/README.md` for the registry contract and filters.

## Bounded strategy discovery

Inspect deterministic candidate specifications:

```bash
python ai_platform/scripts/discovery.py generate
```

Materialize one candidate without running market research:

```bash
python ai_platform/scripts/discovery.py materialize 0
```

Execute one candidate through the full research pipeline when historical data is available:

```bash
python ai_platform/scripts/discovery.py discover --limit 1
```

Discovery uses a bounded, versioned search space and whitelisted feature groups. Candidates are
compile/import validated, checked for semantic duplicates, backtested, validated, registered, and
only then eligible for robustness ranking.

See `ai_platform/discovery/README.md` for the exact execution chain and safety boundaries.

## Phase 5.1 signal-threshold optimization

The first Phase 5 work package exposes only the baseline entry prediction threshold to Freqtrade
Hyperopt. Exit, ROI, stop-loss, protection, feature, and model parameters remain fixed.

Run the pinned optimization plan when the required historical data is available:

```bash
python ai_platform/scripts/run_optimization.py \
  ai_platform/optimization/baseline-signal-thresholds-v1.json
```

The optimization contract separates:

```text
training context -> tuning/selection -> frozen final holdout
```

Hyperopt receives only the tuning window. A selected threshold must then survive local parameter
perturbation before it becomes eligible for a separate final validation run. Optimization artifacts
always keep `promotion_allowed: false`; the final holdout cannot be used to retune a failed result.

See `ai_platform/optimization/README.md` for the exact split, identity contract, stability gates, and
final-evaluation boundary.

## Optional interactive dry-run

For interactive dry-run trading, copy the tracked example into an ignored local config path:

```bash
cp ai_platform/configs/freqai-baseline.example.json user_data/config_ai_baseline.json
```

Keep `dry_run: true` and do not commit real API credentials.

```bash
freqtrade trade \
  --config user_data/config_ai_baseline.json \
  --strategy AiBaselineStrategy \
  --strategy-path ai_platform/strategies \
  --freqaimodel LightGBMRegressor
```

This command is for dry-run only. Continuous dry-run operations and monitoring are a later roadmap
phase.

## Current work package — Phase 5

Phase 5 is **Hyperparameter optimization** and remains active.

The required staged order is:

1. signal thresholds;
2. then exits;
3. then risk/protection parameters;
4. model parameters only after the strategy baseline is stable.

The final holdout window must remain untouched during tuning. Selected parameters must be recorded
in reproducible experiment metadata, and local parameter perturbation must be used to detect brittle
or overfit optima.

See `docs/ai_platform/ROADMAP.md`.

## Design intent

The baseline strategy, bounded discovery engine, and optimization workflow are intentionally
conservative. Complexity should be added only when it improves reproducible out-of-sample
robustness, not because it improves one in-sample backtest.
