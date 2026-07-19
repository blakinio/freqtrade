# Strategy Discovery

Phase 4 adds a bounded, deterministic strategy-discovery pipeline above the existing experiment,
validation, and registry layers.

The discovery engine does **not** generate arbitrary Python from free-form prompts. It may only
combine explicitly whitelisted feature groups and bounded numeric parameters declared in a
versioned search-space contract.

## Current search space

`search-space-v1.json` explores combinations of:

- feature-group presets built from `price_action`, `momentum`, `trend`, `volatility_volume`, and
  `time_context`;
- FreqAI entry-prediction thresholds;
- exit-prediction thresholds;
- stop-loss values.

The model and target are fixed for this phase:

- model: `LightGBMRegressor`;
- target: `future-average-return-v1`.

The current contract expands to at most 18 deterministic candidates.

## Safety boundaries

Every generated strategy is:

- spot-only;
- long-only;
- research-only;
- generated from whitelisted source snippets;
- syntax-compiled before execution;
- import-validated with `freqtrade list-strategies`;
- checked against the durable experiment registry before expensive execution;
- executed through the existing experiment runner;
- evaluated through the existing walk-forward/holdout/lookahead/recursive validation pipeline;
- registered with exact strategy/config/manifest hashes and Git/FreqAI identity.

There is no live-trading command in the discovery engine.

## Inspect candidate specs

```bash
python ai_platform/scripts/discovery.py generate
```

Limit output:

```bash
python ai_platform/scripts/discovery.py generate --limit 3
```

Candidate IDs and class names are content-derived hashes, so identical search inputs generate the
same candidates in the same order.

## Materialize one candidate

```bash
python ai_platform/scripts/discovery.py materialize 0
```

Generated files are written below:

```text
ai_platform/artifacts/discovery/<candidate_id>/
```

Each directory contains:

- generated strategy source;
- derived dry-run FreqAI config with unique identifier;
- experiment manifest;
- validation plan;
- registry definition;
- eventually `candidate-result.json`.

The artifacts directory is ignored by Git.

## Execute discovery

Execute one candidate using already-downloaded data:

```bash
python ai_platform/scripts/discovery.py discover --limit 1
```

Download declared data first when needed:

```bash
python ai_platform/scripts/discovery.py discover --limit 1 --experiment-stage all
```

For every selected candidate the pipeline performs:

```text
materialize
  -> compile
  -> Freqtrade import validation
  -> registry duplicate check
  -> baseline experiment
  -> walk-forward + holdout validation
  -> lookahead analysis
  -> recursive analysis
  -> registry write
  -> candidate result artifact
```

Failures are preserved as `candidate-result.json` and do not silently promote a strategy.

## Duplicate behavior

The registry fingerprint is checked before the expensive experiment/validation stages. A semantic
duplicate is returned with status `duplicate` and is not executed again.

## Ranking

```bash
python ai_platform/scripts/discovery.py rank
```

Only candidates whose validation report has `promotion_allowed: true` are ranked. The current
robustness score combines:

- holdout profit;
- mean walk-forward profit;
- worst walk-forward profit;
- worst fold/holdout drawdown.

This intentionally favors out-of-sample consistency over the best single backtest result.

## Extension rules

Adding a new feature group requires an explicit code change, tests, and review. Extending the JSON
search space alone cannot inject Python or bypass the validation pipeline.
