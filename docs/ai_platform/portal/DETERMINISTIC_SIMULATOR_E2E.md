# Deterministic Exchange Simulator and Universal E2E

## Purpose

P10 provides a deterministic, no-capital execution environment and a scenario runner that exercises the portal's safety chain without using wall-clock sleeps or public runtime access.

## Scenario manifest

A `ScenarioManifest` pins:

- scenario, tenant and bot identity;
- pair, side and amount;
- portal environment;
- initial equity;
- explicit entry and exit market ticks with timestamps and prices.

Scenario manifests are immutable test inputs and are validated before execution.

## Simulator execution

`DeterministicExchangeSimulator` acts as a private approved-intent submitter and trusted risk-snapshot source. It:

- derives notional/exposure from deterministic market ticks;
- reports explicit healthy runtime state;
- accepts only `ApprovedExecutionIntent`;
- fills exactly one deterministic position per scenario;
- closes it at the declared exit tick;
- emits normalized synchronized `TradeOutcome` evidence.

It is not a production exchange adapter and has no live credentials.

## Universal scenario

`UniversalScenarioRunner` executes:

```text
Bot creation
  -> immutable risk policy
  -> deterministic risk evaluation
  -> approved simulated execution
  -> normalized trade outcome
  -> P8 DecisionSnapshot + TradeAnalysis
  -> P9 LearningHypothesis + LearningExperiment
  -> bounded LearningCandidate
  -> verify active bot model is unchanged
```

The scenario uses explicit state and timestamps rather than fixed sleeps.

## Failure evidence

`run_captured()` preserves the first scenario assertion failure with scenario ID, correlation ID, stage and reason code. It does not silently retry or overwrite the first failure.

## Safety invariants

- no real exchange or live-capital path;
- no browser-to-runtime bypass;
- risk rejection prevents simulated order submission;
- candidate creation does not mutate active model assignment;
- protected final holdout is not consumed;
- deterministic scenario inputs and evidence IDs remain attributable;
- failure evidence is preserved with the correlation ID.

## Validation scope

Final P10 validation runs from a clean branch based directly on merged P9 `develop`. The permanent `Portal Universal E2E` gate covers the deterministic backend scenario and the critical Chromium portal journey, while the existing AI Platform, Freqtrade and security workflows remain authoritative merge gates.

## Current boundary

The simulator proves the universal platform workflow without requiring production Freqtrade order submission. The existing production `FreqtradeExecutionAdapter.submit_approved_intent` remains independently fail-closed until a separate execution implementation is authorized.
