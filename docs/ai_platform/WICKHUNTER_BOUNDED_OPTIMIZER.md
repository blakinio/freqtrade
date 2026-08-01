# WickHunter bounded validation optimizer

## Purpose

WH-05 evaluates a finite, explicitly supplied set of bounded `WickHunterParameters` candidates. It uses the WH-03 deterministic evaluation interface and exact WH-02 labels. It does not create unbounded parameters, access the protected holdout, use the test split for selection, claim profitability or promote any candidate automatically.

```text
finite parameter candidates
  + explicit bounds
  + WH-03 training and validation reports
  -> seeded bounded surrogate search
  -> validation-only ranking
  -> descriptive test evidence for top-k only
```

## Finite search space

The caller supplies every allowed parameter candidate. Before optimization:

- each candidate is validated against `WickHunterParameterBounds`;
- parameter hashes must be unique;
- the search-space identity binds the sorted parameter hashes and the bounds;
- the number of evaluations is capped by `maximum_trials`;
- `initial_trials` and `top_k` must fit inside the evaluated budget.

The optimizer never extrapolates a new parameter value outside this explicit set.

## Deterministic surrogate selection

The optimizer canonically sorts candidates and converts numeric parameter fields into normalized vectors. A fixed NumPy generator chooses the initial observations. Later trials use a deterministic radial-basis surrogate:

- fixed length scale and numerical jitter;
- posterior mean and standard deviation from the observed validation objectives;
- acquisition = mean + `exploration_ratio` × standard deviation;
- ties resolved by immutable parameter hash.

Running the same policy and immutable evidence with candidates in any input order produces the same trial sequence and result identity.

## Objective

The objective version is `wickhunter-validation-stability-objective-v1`. It is calculated only from a WH-03 report:

```text
validation net-return mean
- stability_penalty × dispersion across symbol/regime/side slices
- inactivity_penalty × ignored-decision ratio
```

This is a bounded research ranking score, not a profitability claim. Costs and outcomes are inherited from WH-02 through WH-03 and are never recomputed by the optimizer.

## Split isolation

Training, validation and test split names are explicit and disjoint.

- training reports are recorded for every evaluated candidate;
- validation reports provide the only selection objective;
- candidates are ranked exclusively by validation objective and immutable hash;
- test reports are generated only after ranking and only for final top-k candidates;
- test objectives cannot change rank or selection;
- `holdout` and `protected_holdout` cases fail closed before any evaluation.

## Stability evidence

For each top-k candidate the result records:

- validation and test objective;
- validation–test delta;
- validation and test slice dispersion;
- rank and immutable parameter hash.

Every non-top-k trial is forbidden from carrying test evidence.

## Safety boundary

Every result records:

```text
selection_source = validation_only
protected_holdout_accessed = false
test_used_for_selection = false
model_promoted = false
profitability_claimed = false
execution_enabled = false
live_capital_authorized = false
orders_submitted = 0
```

WH-05 contains no credentials, order adapter, automatic promotion or live-capital authority.
