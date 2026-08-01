# WickHunter bounded walk-forward optimizer

## Purpose

WH-05 evaluates a finite, explicitly supplied set of bounded `WickHunterParameters`
candidates. The baseline phase uses the WH-03 deterministic evaluation interface and
exact WH-02 labels. The model-aware phase trains and compares WH-04 LightGBM advisory
artifacts through the same frozen evaluation interface.

WH-05 does not create unbounded parameters, access the protected holdout, use test
evidence for selection, claim profitability, mutate an approved parameter set, promote
a model or authorize execution.

```text
finite bounded candidates
  + purged/embargoed walk-forward folds
  + WH-03 baseline ranking
  + WH-04 advisory model validation
  -> validation-only global/regime/cluster packages
  -> descriptive test and perturbation evidence
```

## Finite baseline search

The caller supplies every allowed candidate. Each candidate is validated against
`WickHunterParameterBounds`; hashes must be unique and the search-space identity binds
the sorted hashes to the bounds. A seeded initial design and deterministic radial-basis
surrogate select trials inside that finite set. Ties are resolved by immutable parameter
hash.

The objective is `wickhunter-validation-stability-objective-v1`:

```text
validation net-return mean
- stability_penalty × dispersion across symbol/regime/side slices
- inactivity_penalty × ignored-decision ratio
```

Costs and outcomes come from WH-02 through WH-03 and are never recomputed.

## Walk-forward geometry

`WalkForwardFold` declares sorted, disjoint training, calibration, validation and test
split names plus explicit purge and embargo durations. A fold fails closed when:

- any required split group is empty;
- a protected holdout split appears;
- a training or calibration label overlaps the validation boundary after purge;
- a validation label overlaps the test boundary after embargo.

Multiple folds are aggregated by immutable fold hash. Selection uses validation evidence
from every fold.

## Model-aware phase

For each fold, the baseline optimizer produces a validation-ranked candidate cohort. The
model-aware phase then:

1. trains the deterministic WH-04 LightGBM artifact using only the fold's training and
   calibration cases;
2. evaluates every cohort candidate on the fold's validation cases through
   `evaluate_lightgbm_against_baseline`;
3. aggregates model validation objectives across all folds;
4. selects one candidate by validation objective and immutable hash;
5. evaluates test evidence only for that selected candidate;
6. verifies that validation and test evaluation reproduce the same model hash for the
   same training/calibration evidence.

The default adapter calls the frozen WH-04 `LightGBMTrainingPolicy`,
`train_lightgbm_scorer` and `evaluate_lightgbm_against_baseline` APIs. Model outputs
remain candidate/advisory evidence.

## Global, regime and symbol-cluster packages

`ScopeSpec` supports:

- `global`;
- `regime` (`uptrend`, `range`, `downtrend`);
- `symbol_cluster` using an explicit symbol-to-cluster mapping.

Each eligible scope receives an independent validation-only package. A sparse scope must
declare inheritance and reuses the broader global package instead of overfitting an
independent parameter set.

Every package records parameter version/hash, bounds hash, dataset hash, code SHA,
model hashes, fold hashes, seed, validation objective and descriptive test objective.

## Local perturbation evidence

The selected parameter is compared with its nearest normalized candidate. WH-05 records
distance, objective delta and a bounded stability decision. This is descriptive local
sensitivity evidence; it cannot mutate selection or authorize promotion.

## Safety boundary

Every result and package records:

```text
protected_holdout_accessed = false
test_used_for_selection = false
promotion_state = candidate
automatically_promoted = false
execution_enabled = false
live_capital_authorized = false
orders_submitted = 0
```

WH-05 contains no credentials, exchange adapter, order submission or live-capital
authority.
