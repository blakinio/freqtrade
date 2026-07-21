# RL-v2 Design Contract

## Status

`rl-v2-design-contract-v1` is a **design-only** prospective contract.

It exists to prevent the next RL research iteration from repeating the structural failure mode observed
in `rl-research-v1`: a functionally successful execution that selected an inactive policy because the
reward geometry admitted permanent neutrality as a safe zero-reward solution.

This contract does not implement an RL-v2 model, strategy, config, action space, reward magnitude, or
evaluation workflow. It authorizes no training, backtest, market-data download, performance evaluation,
promotion, profitability claim, or superiority claim.

Machine-readable contract:

`ai_platform/experimental_model_research/rl-v2-design-contract-v1.json`

Validator:

`ai_platform.scripts.rl_v2_design_contract`

## Why the contract exists

The completed RL zero-trade diagnosis established that:

- `rl-research-v1` trained and predicted successfully;
- its action numbering matched the strategy;
- the source backtest contained zero trades before strict-OOS extraction;
- broad `do_predict` rejection did not explain the inactivity;
- its custom reward gave `0.0` both to staying neutral while flat and to a valid long entry;
- after entering, the agent became exposed to holding penalties and potentially negative exit reward;
- deterministic evaluation selected best models with zero episode reward;
- the artifact did not preserve the exact inference action histogram or pre-trade signal counts.

The next iteration therefore needs prospective design invariants and observability before any new model
execution is allowed.

## Reward geometry requirements

A future RL-v2 implementation must satisfy all of the following before historical execution:

1. remaining flat while already neutral has a strictly lower immediate reward than a valid long-entry
   transition;
2. perpetual neutral inactivity is not an unpenalized zero-reward solution by construction;
3. invalid actions remain penalized;
4. reward inputs use only state available at the decision tick and do not derive from future candles;
5. synthetic tests cover flat-neutral versus entry, invalid actions, bounded holding behavior,
   decision-time-only exit reward, and the perpetual-neutral episode case.

The contract intentionally does **not** select numeric reward magnitudes. Choosing or tuning those
values belongs to a later implementation/research task and may not use consumed historical OOS or the
protected final holdout.

## Position-state and inference parity

The v1 design used position-dependent action validity and reward while historical inference did not
explicitly expose position state to the memoryless policy. RL-v2 may not silently preserve that hidden
state dependency.

A future implementation must choose exactly one design mode:

1. **explicit position-state training and historical-inference parity** — the policy receives the
   required position state consistently in both environments; or
2. **position-independent action semantics** — the action contract is designed so correctness does not
   depend on hidden position state unavailable to the policy.

The design contract does not choose between them. That choice is deferred to a separate implementation
task and must pass a synthetic parity test before any historical execution.

The contract explicitly does not assume that FreqAI `add_state_info` is available in backtesting.

## Mandatory observability

Before any RL-v2 performance result may be interpreted, evidence must preserve separate counts for:

- deterministic inference actions by pair and action, including actions with zero occurrences;
- `do_predict` accepted and rejected rows by pair;
- pre-trade entry and exit signals by pair;
- raw backtest trades;
- strict-OOS input, included, and excluded trades.

These layers must remain separately attributable. A future zero-trade result must be diagnosable without
having to infer whether inactivity came from the model, FreqAI gating, strategy signals, trade execution,
or strict-OOS filtering.

## Evaluation isolation

The following windows are not available for RL-v2 redesign validation:

- consumed historical OOS: `20260501-20260630`;
- protected final holdout: `20260801-20260930`.

The final holdout remains unused and unavailable before `2026-10-01T00:00:00Z` under its existing
prospective declaration.

This design-contract task deliberately selects **no** future evaluation window. A later bounded task
must prospectively declare a fresh, non-protected, unconsumed window after the RL-v2 implementation is
frozen and before that window is evaluated.

## Phase 5 and Phase 6 isolation

The contract preserves:

- frozen candidate thresholds `0.006/-0.009`;
- completed Phase 6 with authoritative `selected_model = null`;
- no RL-v2 membership in Phase 6;
- no Phase 6 candidate or selection-policy changes;
- no consumption of future RL-v2 results by the completed comparison.

RL-v2 is a separate research track and cannot retroactively alter Phase 5 tuning or Phase 6 evidence.

## Validation

Validate the checked-in contract with:

```bash
python -m ai_platform.scripts.rl_v2_design_contract
```

Print the canonical contract with:

```bash
python -m ai_platform.scripts.rl_v2_design_contract --print-canonical
```

Run the targeted mutation tests with:

```bash
pytest -q tests/ai_platform/test_rl_v2_design_contract.py
```

The validator is intentionally fail-closed: any field, authorization, isolation rule, required
observability count, or design invariant that drifts from the canonical contract causes validation to
fail.

## What comes next

After this design contract is merged and closed, a separate prospectively declared RL-v2 implementation
task may choose one position-state/action-semantics mode and implement synthetic-only proof of the
reward and inference-parity requirements.

That future task still must not train or evaluate on consumed historical OOS or the protected final
holdout. Historical execution and selection of a fresh evaluation window require later, separately
reviewed work packages.
