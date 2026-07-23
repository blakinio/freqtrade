# Continual Learning Foundation

## Purpose

P9 turns durable trade intelligence into reproducible research proposals without allowing evidence, experiments or candidate creation to mutate an active model assignment.

## Provenance chain

```text
TradeInsight
  -> LearningHypothesis
  -> LearningExperiment
  -> LearningCandidate
```

Every hypothesis pins the source insight and evidence links. Every experiment pins an explicit evidence window and autonomy level. Every candidate pins dataset and feature-schema versions plus its source experiment.

## Protected evidence boundary

The future final holdout v2 is protected for `2026-08-01T00:00:00Z` through `2026-10-01T00:00:00Z` (exclusive end). Iterative experiment windows overlapping this period are rejected.

The workflow does not run the one-time final holdout evaluation and does not reinterpret previous research evidence.

## Autonomy levels

- `L0`: manual workflow;
- `L1`: assisted analysis;
- `L2`: autonomous proposal generation;
- `L3`: bounded research execution;
- `L4`: bounded candidate registration.

Candidate registration requires explicit L4 authority in the workflow. L4 still means **candidate only**: `promoted=false` and `assigned_to_bot=false` are immutable candidate facts in this layer.

## Negative evidence

Negative and inconclusive experiments are durable history. Only an explicitly positive experiment may produce a candidate metadata record. Candidate creation does not imply promotion.

## Safety invariants

- no protected holdout overlap in iterative learning windows;
- no model promotion or rollback call;
- no BotConfigRevision mutation;
- no live-capital authorization;
- source insight tenant must match trusted request tenant;
- negative experiments remain queryable and cannot be silently discarded.

## Merge-state validation

The clean P9 branch is synchronized with the current `develop` before final merge. Required CI must validate this synchronized tree; synchronization does not authorize protected-holdout access, model promotion, bot reassignment, or live-capital execution.
