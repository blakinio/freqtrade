# Hyperparameter Optimization

Phase 5 introduces staged Hyperopt research without allowing parameter selection to contaminate the
frozen final holdout. This directory contains the versioned optimization contract for the first
reviewable work package: **signal-threshold optimization**.

This is research infrastructure. It does not establish that the baseline or any selected parameter
set is profitable or suitable for live capital.

## Phase 5.1 scope

The first stage optimizes only:

- `entry_prediction_threshold`;
- Freqtrade Hyperopt `buy` space.

The following remain fixed in this work package:

- exit threshold;
- ROI schedule;
- stop-loss;
- protections and risk parameters;
- FreqAI model type and model-training parameters;
- feature set and target definition.

This preserves the staged order in the roadmap. Later Phase 5 work packages may address exits and
risk/protections only after the signal-threshold stage is reviewed.

## Data separation

The baseline plan is:

```text
training context: 2025-12-01 through 2026-02-28
parameter tuning: 2026-03-01 through 2026-04-30
frozen holdout:   2026-05-01 through 2026-06-30
```

The final holdout is copied exactly from
`ai_platform/validation/baseline-validation-v1.json` and is validated at runtime before Hyperopt can
start.

Hyperopt receives only the tuning timerange. The runner explicitly rejects overlapping windows and
never passes the final-holdout timerange to the Hyperopt command.

The `training` field describes the pre-tuning model-history context available to the existing FreqAI
rolling training process. Phase 5.1 does not tune model parameters. FreqAI continues to use the
baseline `train_period_days` and `backtest_period_days` behavior while the strategy threshold is
selected on the tuning window.

## Optimization objective

The runner uses Freqtrade's `MultiMetricHyperOptLoss` rather than raw in-sample profit alone. The
built-in loss combines several trading-quality dimensions, including profit, drawdown, trade count,
profit factor, expectancy, and win rate.

The plan pins:

- Hyperopt space;
- epoch count;
- random state;
- minimum trade count;
- loss function;
- worker setting;
- exact data windows.

The selected epoch is therefore reproducible from the repository inputs, historical data, Freqtrade
version, and Git revision recorded with the run.

## Local parameter stability

After Hyperopt selects an entry threshold, the runner backtests the immediate local neighbors on the
same tuning window:

```text
selected threshold - 0.001
selected threshold + 0.001
```

Neighbors outside the declared parameter bounds are omitted. Every available neighbor must satisfy
all configured stability limits relative to the selected result:

- maximum allowed profit deterioration;
- maximum allowed drawdown increase;
- minimum retained trade-count ratio.

A brittle optimum is reported as `rejected_unstable` and is not eligible for final validation.

## Selection identity and artifacts

A stable selection receives a deterministic `selection_id` derived from:

- optimization ID;
- Git commit;
- optimization stage;
- selected parameter name and value;
- training window;
- tuning window;
- frozen final holdout.

The runner also creates a unique FreqAI identifier derived from that selection identity. Selected
parameters are persisted explicitly in `selection.json` and in the strategy parameter JSON beside a
run-local copy of the strategy.

Artifacts are written below:

```text
ai_platform/artifacts/optimization/<optimization_id>/<run_id>/
```

The directory contains:

- `optimization-plan.json`;
- `provenance.json` with Git SHA and input hashes;
- Hyperopt log and result data;
- tuning-window perturbation backtests;
- `stability-report.json`;
- `selection.json` with the selected parameters;
- a materialized experiment manifest;
- a materialized validation plan;
- a materialized registry definition;
- `optimization-report.json`.

Generated artifacts remain ignored by Git.

## Run Phase 5.1

With the required historical data and FreqAI/Hyperopt dependencies available:

```bash
python ai_platform/scripts/run_optimization.py \
  ai_platform/optimization/baseline-signal-thresholds-v1.json
```

Exit codes:

- `0` — a parameter set was selected and passed local stability checks;
- `2` — optimization completed but the selection failed stability checks;
- `1` — the optimization contract or execution failed.

## One-shot CI tuning execution

The repository workflow `.github/workflows/ai-platform-phase5-tuning.yml` is an execution harness for
running the same Phase 5.1 contract on GitHub-hosted research compute when local market data or
FreqAI dependencies are unavailable.

The workflow is intentionally narrow:

- it triggers only when a pull request is **opened** with a change to
  `ai_platform/optimization/run-requests/signal-thresholds-v1.json`;
- it checks out the exact pull-request head SHA, so the selection identity points to a real research
  commit rather than the synthetic pull-request merge commit;
- it uses only read-only repository permissions and no exchange credentials;
- it downloads the manifest-declared public historical data;
- it runs `baseline-signal-thresholds-v1.json`, which passes only `20260301-20260430` to Hyperopt;
- it treats exit code `2` as a valid rejected research outcome rather than an infrastructure failure;
- it emits one `PHASE5_TUNING_RESULT=<json>` line containing the selection, tuning metrics, local
  stability evidence, Git SHA, and `final_holdout_used: false`.

The `opened` trigger is deliberate. Updating the request pull request with the recorded result does
not rerun tuning. A later tuning attempt requires opening a new request pull request and therefore
produces an explicit new research decision.

This workflow never runs final validation. A stable result must be frozen first, then evaluated
through a separate final-validation work package. That boundary prevents a tuning retry from
silently evaluating the final holdout again.

## Final evaluation boundary

Optimization never sets `promotion_allowed: true`.

A stable selection is only **eligible for final validation**. The materialized selected validation
plan must then be executed separately through the existing validation pipeline, including the frozen
final holdout and bias checks. The resulting experiment and validation evidence can then be written
to the existing registry.

The final holdout must be evaluated once as final evidence. Its result must not be used to retune the
threshold, change the feature set, choose a model, or iterate the optimization search. A failed final
holdout means rejection of that selected experiment, not another tuning pass against the holdout.
