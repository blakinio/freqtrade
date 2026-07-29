# ASE-02 constrained research and optimization

## Purpose

ASE-02 adds a bounded research layer above the canonical Feature Registry and Strategy DSL. It does not add execution authority, order submission, deployment, promotion, or access to the protected final holdout.

```text
immutable dataset manifest
        +
Feature Registry + Search Space Registry
        +
schema-constrained candidate request
        |
        v
validated StrategyDefinition DSL
        |
        v
constrained Optuna study
        |
        v
trial lineage + robustness evidence
```

## Dataset identity and holdout lock

`configs/dataset_manifest.v1.yaml` records immutable data-selection, code, and configuration SHA-256 identities. Training, tuning, and historical validation windows are ordered and non-overlapping. The manifest must match the canonical declaration at `ai_platform/validation/final-holdout-v2-declaration.json`.

The protected timerange remains exactly `20260801-20260930` with:

- `locked: true`;
- `used: false`;
- `retuning_allowed: false`.

A mismatch, overlap, reused holdout, or declaration permitting retuning fails closed.

## Candidate generation boundary

The generator accepts a versioned `CandidateRequest` and:

- resolves only canonical registry feature IDs;
- requires every feature to be both `validated` and `approved_for_ai`;
- validates parameter overrides against registry bounds and declared search spaces;
- emits the existing `StrategyDefinition` DSL, then validates it with `StrategyValidator` using `generated_by_ai=True`;
- requires a concrete falsification contract;
- limits feature and condition complexity;
- forces closed-bar, research-only behavior with `execution_authority=false` and `order_submission=false`.

Unknown, experimental, research-only, or unapproved features are rejected. There is no arbitrary code generation, `eval`, `exec`, Freqtrade execution import, or browser-to-execution path.

## Constrained Optuna study

`ConstrainedOptimizer` uses a seeded Optuna TPE sampler and median pruning. Every tunable parameter must be explicitly bound to a named registry search space and an allowlisted parameter subset.

Feasibility constraints include:

- minimum trade count;
- maximum drawdown;
- lookahead and recursive-analysis passes;
- mandatory falsification pass;
- explicit forbidden parameter combinations.

Optuna considers constraint values feasible only when each value is less than or equal to zero. Infeasible trials retain lineage but cannot become the selected best candidate.

## Trial lineage and robustness

Each trial records immutable links to:

- study ID;
- dataset manifest hash;
- base candidate request hash;
- sampled parameters;
- candidate DSL hash;
- constraint vector;
- evaluation metrics;
- score, state, and failure reason;
- canonical lineage hash.

The robustness score rewards mean and worst-fold profit plus sufficient trade count, while penalizing drawdown and cross-fold instability. It is research evidence, not a profitability claim or promotion decision.

## Non-goals

ASE-02 does not:

- use or unlock the final holdout;
- submit orders or mutate a running strategy;
- promote a candidate to dry-run, shadow, or live;
- bypass deterministic risk or validation gates;
- replace the existing experiment registry or Phase 4 discovery pipeline.
