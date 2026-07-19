# AI Trading Platform Roadmap

## Status model

Each phase should land as a separate, reviewable work package or small series of PRs.

Status values:

- `planned`
- `active`
- `blocked`
- `done`

## Phase 0 — Repository foundation

Status: `done`

Goal: establish project boundaries and a safe baseline without modifying Freqtrade core.

Deliverables:

- root `AGENTS.md`;
- architecture document;
- roadmap;
- `ai_platform/` project boundary;
- research-only FreqAI baseline strategy;
- dry-run baseline configuration.

Acceptance criteria:

- no secrets committed;
- baseline remains dry-run;
- project-specific code is isolated from upstream core;
- Python baseline compiles;
- configuration and strategy intent are documented.

## Phase 1 — Reproducible baseline backtest

Status: `done`

Goal: make the initial LightGBM baseline reproducible end-to-end.

Deliverables:

- documented data-download command;
- pinned experiment manifest format;
- baseline timerange policy;
- script/runner for backtest execution;
- persisted machine-readable result summary;
- exact fee assumptions recorded.

Acceptance criteria:

- a clean checkout can reproduce the same experiment definition;
- strategy/config/model identifiers are recorded;
- result artifacts identify Git commit and timerange;
- failures are explicit and non-zero.

## Phase 2 — Validation pipeline

Status: `done`

Goal: prevent promotion based on a single backtest.

Deliverables:

- out-of-sample split policy;
- walk-forward runner;
- lookahead-analysis automation;
- recursive-analysis automation;
- minimum-trade-count gate;
- maximum-drawdown gate;
- consolidated validation report.

Acceptance criteria:

- candidate receives pass/fail per gate;
- final out-of-sample data is not used for tuning;
- reports are reproducible from repository inputs;
- failed gates block promotion.

## Phase 3 — Experiment registry

Status: `done`

Goal: create durable memory of what has been tried.

Deliverables:

- experiment schema;
- unique experiment IDs;
- structured metadata/results storage;
- comparison tooling;
- promotion status field.

Acceptance criteria:

- duplicate experiment definitions can be detected;
- results can be compared by model/feature/target/timeframe;
- every validated candidate maps to a Git commit and FreqAI identifier.

## Phase 4 — Strategy discovery engine

Status: `done`

Goal: automate generation and rejection of strategy hypotheses.

Deliverables:

- hypothesis schema;
- bounded parameter/feature search space;
- strategy candidate generator;
- compile/import validation;
- automatic baseline backtest;
- candidate ranking.

Acceptance criteria:

- generated code never bypasses the validation pipeline;
- invalid strategies are rejected safely;
- ranking uses out-of-sample/robustness metrics, not raw in-sample profit alone.

## Phase 5 — Hyperparameter optimization

Status: `planned`

Goal: tune strategy thresholds and risk parameters without contaminating final evaluation.

Deliverables:

- staged Hyperopt spaces;
- train/tune/final-test separation;
- parameter stability analysis;
- overfitting checks.

Recommended tuning order:

1. signal thresholds;
2. exits;
3. risk/protections;
4. model parameters only after strategy baseline is stable.

Acceptance criteria:

- final test window remains untouched during tuning;
- selected parameters are recorded;
- local parameter perturbation does not catastrophically collapse results.

## Phase 6 — Model comparison

Status: `planned`

Goal: determine whether a model improves trading outcomes over the LightGBM baseline.

Candidates:

- LightGBM baseline;
- XGBoost;
- custom/PyTorch only when justified.

Acceptance criteria:

- identical evaluation windows;
- identical trading-cost assumptions;
- comparison based primarily on out-of-sample return, drawdown, stability, and trade count;
- complex model rejected if it does not materially improve robustness.

## Phase 7 — Market regime layer

Status: `planned`

Goal: adapt strategy behavior to broad market conditions.

Initial regimes:

- trend up;
- trend down;
- range;
- high volatility.

Acceptance criteria:

- regime definition uses only information available at decision time;
- regime filter improves walk-forward robustness, not just in-sample profit;
- fallback behavior is deterministic.

## Phase 8 — Dry-run operations

Status: `planned`

Goal: operate continuously without real capital.

Deliverables:

- dedicated dry-run config;
- model retraining policy;
- model-age monitoring;
- exchange/API health monitoring;
- PnL and drawdown monitoring;
- alerting;
- kill-switch rules for new entries.

Acceptance criteria:

- sustained dry-run operation;
- no secret leakage;
- stale data/model conditions are visible;
- observed live-market behavior is compared with backtest expectations.

## Phase 9 — Strategy/model registry lifecycle

Status: `planned`

Goal: formalize promotion and retirement.

States:

`experiment -> candidate -> validated -> dry-run -> shadow -> live-small -> production -> retired`

Acceptance criteria:

- promotion is explicit and auditable;
- strategy and model versions are immutable once promoted;
- rollback target exists;
- degradation can move a strategy to retired/disabled state.

## Phase 10 — Live-small readiness

Status: `planned`

This phase requires explicit owner approval before implementation.

Goal: prepare a separately reviewed path for minimal real capital.

Required controls before approval:

- withdrawal-disabled API key;
- separate production credentials;
- strict max exposure;
- daily/rolling loss limits;
- emergency stop procedure;
- monitoring and alerting;
- rollback procedure;
- documented dry-run evidence.

No work package may silently cross from dry-run into live trading.

## Experimental backlog

These are intentionally not part of the early critical path:

- reinforcement learning;
- deep-learning sequence models;
- order-flow models;
- alternative data;
- large dynamic pair universes;
- cross-exchange execution;
- automatic capital scaling;
- autonomous live promotion.

They should be evaluated only after the baseline research and validation system is reliable.
