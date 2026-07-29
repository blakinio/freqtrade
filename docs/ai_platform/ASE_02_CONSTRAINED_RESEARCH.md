# ASE-02 platform boundary

ASE-02 implements the dependency-ordered constrained research package after ASE-FR-01.

## Delivered contract

- immutable dataset manifest with data-selection, code, configuration, and manifest hashes;
- exact lock to the prospective final holdout `20260801-20260930`;
- constrained seeded Optuna studies with explicit parameter bindings, forbidden combinations, pruning, feasibility constraints, trial lineage, and robustness scoring;
- schema-constrained AI candidate requests producing only canonical Strategy DSL from validated, AI-approved Feature Registry entries;
- deterministic package and repository integration tests.

## Safety invariants

- `final_holdout_used` is always false;
- `execution_authority` is always false;
- `order_submission` is always false;
- no exchange credentials, execution adapter, deployment, promotion, live trading, `eval`, or `exec`;
- no reinterpretation of Phase 5 or Phase 6 evidence;
- no duplication of the existing durable experiment registry or discovery engine.

The next package, ASE-03, remains responsible for separately reviewed paper/shadow integration behind simulator parity and Risk Core approval.
