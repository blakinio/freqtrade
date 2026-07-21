# AI Platform

This directory contains project-specific AI/FreqAI research and strategy code layered on top of
upstream Freqtrade.

It is intentionally separated from `freqtrade/` core to keep upstream synchronization manageable
and to preserve a strict boundary between research tooling and trading-engine code.

## Current scope

Phases 0 through 4 are implemented. Phase 5 tuning work through Phase 5.2 is complete, but Phase 5
remains active until its prospectively declared final holdout v2 can be evaluated no earlier than
`2026-10-01 UTC`. Phase 6 model comparison is complete with authoritative `selected_model = null`.

The currently frozen candidate parameters are:

- `entry_prediction_threshold = 0.006`;
- `exit_prediction_threshold = -0.009`.

The protected prospective final holdout v2 is `20260801-20260930`. It remains unused and may not be
used for training, tuning, Hyperopt, feature selection, model selection, or iterative evaluation as
data arrives.

The current system is research-only:

- spot trading;
- BTC/USDT and ETH/USDT baseline universe;
- 15m base timeframe with 1h and 4h context;
- long-only strategies;
- dry-run configuration;
- reproducible experiment manifests and provenance;
- walk-forward and historical OOS validation;
- automated lookahead and recursive analysis;
- promotion gates;
- durable SQLite experiment registry and duplicate detection;
- bounded deterministic strategy discovery;
- staged threshold optimization with frozen candidate parameters;
- completed LightGBM-versus-XGBoost Phase 6 comparison with no eligible model selected;
- separate evidence-only PyTorch and reinforcement-learning historical research tracks;
- no live-capital automation.

The repository contains infrastructure and evidence for research and validation. It does not claim
that any current strategy or model is profitable or ready for live capital merely because a pipeline
exists, CI passes, or a historical backtest completed.

## Project layout

```text
ai_platform/
├── README.md
├── configs/
├── discovery/
├── experiments/
├── experimental_model_research/
│   └── evidence/
├── freqaimodels/
├── optimization/
├── registry/
├── scripts/
├── strategies/
└── validation/
```

Generated research artifacts are written below `ai_platform/artifacts/` and are ignored by Git.
Durable evidence that must survive GitHub Actions artifact expiry is stored explicitly in tracked
project evidence records.

## Safety invariants

- Do not commit exchange credentials or other secrets.
- Research configs must remain `dry_run: true`.
- The baseline and generated discovery strategies remain spot-only and long-only unless a separate
  reviewed work package explicitly changes that boundary.
- Project-specific code stays outside upstream `freqtrade/` core unless a separately reviewed core
  change is explicitly required.
- A profitable backtest is never sufficient for promotion.
- Failed validation gates block promotion.
- Discovery candidates cannot bypass the experiment, validation, and registry pipeline.
- Hyperopt and parameter selection cannot use the protected final holdout.
- Frozen Phase 5 thresholds may not be retuned from consumed historical OOS inside the completed
  tuning work package.
- Phase 6 ended with `selected_model = null`; no model is promoted by that comparison.
- PyTorch and RL historical evidence is independent and cannot retroactively change Phase 6.
- A stable optimization result is not promoted automatically; it still requires authorized final
  validation.
- No work package may silently transition from research/dry-run into live trading.

## Environment

Install Freqtrade with FreqAI dependencies using the repository-supported installation method.
For a local editable Python environment, the relevant optional dependency group is `freqai`.
Hyperopt dependencies are required for optimization work. Experimental RL execution additionally
uses the explicitly bounded `freqai_rl` runtime profile where declared by its work package.

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

The pipeline performs separate walk-forward folds and holdout evaluation, then applies configured
performance gates together with lookahead and recursive-analysis checks. It emits a machine-readable
validation report with `promotion_allowed`.

Historical validation windows that have already been consumed by tuning or model research must not
be silently reused as fresh final evidence. The currently protected prospective final holdout v2 is
`20260801-20260930` and its one-shot final evaluation is not authorized before `2026-10-01 UTC`.

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

## Phase 5 threshold optimization status

The staged threshold-tuning work has frozen:

```text
entry_prediction_threshold = 0.006
exit_prediction_threshold = -0.009
```

Phase 5.1 handled entry-threshold selection and Phase 5.2 handled exit-threshold selection under the
repository's train/tune/holdout separation and local stability requirements. These thresholds are
now frozen for the current candidate.

The protected final holdout v2 is:

```text
20260801-20260930
```

It was declared prospectively and remains unavailable for tuning or selection. The final one-shot
evaluation cannot run before `2026-10-01 UTC`. A future failed final evaluation must not be used to
retune the same candidate against that holdout.

See `ai_platform/optimization/README.md` and the tracked final-holdout-v2 contracts for exact
execution boundaries.

## Phase 6 model comparison status

The canonical Phase 6 comparison evaluated the frozen LightGBM and XGBoost candidates under the same
historical evaluation geometry and trading-cost assumptions.

The boundary-corrected authoritative outcome is:

```text
selected_model = null
```

Neither `LightGBMRegressor` nor `XGBoostRegressor` passed the predeclared minimum-profit and
minimum-stability eligibility gates. Phase 6 is therefore complete with no model selected and no
promotion authorized.

PyTorch and reinforcement-learning research were executed later as separate isolated experimental
tracks. They were not Phase 6 candidates and cannot change its result.

## Experimental PyTorch and RL evidence

The bounded historical execution work package ran exactly one frozen historical backtest for each of
the two isolated research tracks and preserved independent strict historical-OOS evidence.

Observed evidence:

- PyTorch `SeededPyTorchMLPRegressor`: 20 strict-OOS trades, negative aggregate profit, stability
  `0.0`, with negative May and June folds;
- RL `LongOnlyReinforcementLearner`: zero strict-OOS trades, profit `0.0`, drawdown `0.0`, stability
  `0.0`; the zero values reflect inactivity and are not profitability evidence.

See:

`docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_BACKTEST_EVIDENCE.md`

The tracks remain evidence-only. No cross-track winner, promotion, retuning, profitability claim, or
superiority claim is authorized.

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

This command is for dry-run only. Continuous dry-run operations and monitoring remain a later
roadmap phase and should not be confused with evidence of a validated or promoted model.

## Current work package boundary

No current model is promoted for live or dry-run lifecycle advancement by Phase 6 or the experimental
PyTorch/RL evidence.

The active time-gated program boundary is the future Phase 5 final holdout v2 evaluation:

```text
holdout: 20260801-20260930
not before: 2026-10-01 UTC
```

Until then, work may improve infrastructure, monitoring, documentation, or separately declared
research contracts, but must not consume the protected holdout or retune the frozen `0.006/-0.009`
candidate using already-consumed historical OOS.

See `docs/ai_platform/ROADMAP.md`.

## Design intent

The baseline strategy, bounded discovery engine, optimization workflow, model comparison, and
experimental-model tracks are intentionally conservative. Complexity should be added only when it
improves reproducible out-of-sample robustness under a prospectively declared evaluation policy, not
because it improves one in-sample backtest.
