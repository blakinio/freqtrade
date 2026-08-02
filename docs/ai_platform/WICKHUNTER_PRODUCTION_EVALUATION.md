# WickHunter production evaluation loader

The production evaluation loader joins the independently accepted WH-01 dataset with an independently accepted WH-02 deterministic replay package.

It is a read-only research boundary. It does not train or promote a model, optimize parameters, access the protected holdout, submit orders or authorize live capital.

## Inputs

`load_verified_evaluation_dataset(...)` requires three immutable roots:

- the WH-01 production materialization;
- the exact WH-02 price-path package used by deterministic replay;
- the resulting WH-02 deterministic replay label package.

Before reading rows, the loader runs the existing independent verifiers for the dataset and replay package.

## Reconstruction and join

The loader:

1. validates every declared partition path and SHA-256;
2. reconstructs each `DatasetRow`, nested `LiquidationFeatureVector`, source aggregate and market metric through the domain contracts;
3. recomputes each dataset row identity;
4. reconstructs each `CandidateLabel` and recomputes its serialized identity;
5. requires one unique LONG label and one unique SHORT label for every dataset row;
6. rejects missing rows, extra labels, duplicates, split/symbol/timestamp mismatches and unsafe authority fields;
7. returns an immutable `VerifiedEvaluationDataset` with deterministic `evaluation_sha256`.

The result is suitable as the sole input boundary for WH-04 model fitting and WH-05 bounded parameter optimization.

## Safety

A successful result always declares:

- `protected_holdout_accessed=false`;
- `immutable_inputs_mutated=false`;
- `model_execution_authorized=false`;
- `performance_research_authorized=false`;
- `execution_enabled=false`;
- `live_capital_authorized=false`;
- `trading_credentials_present=false`;
- `orders_submitted=0`.

Any violation fails closed.
