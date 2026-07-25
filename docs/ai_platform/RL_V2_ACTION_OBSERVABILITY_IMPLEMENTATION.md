# RL-v2 Action-Level Observability Implementation

## Result

The prospective RL-v2 action-observability contract is implemented as a pure project-specific evidence library. The package contains no strategy integration, workflow, run request, model execution, backtest, market-data access or cache operation.

The implementation remains `implemented_not_authorized_for_execution`.

## Recorder

`RLV2ActionObservabilityRecorder` is disabled by default.

Disabled mode:

- does not inspect the supplied pair, dataframe, metadata or destination;
- records no rows;
- creates no directory or artifact;
- returns without changing strategy-visible data.

Enabled mode accepts a pair and an inference dataframe containing `date`, `&-action`, `do_predict` and `volume`. It creates the frozen normalized row fields:

- pair and UTC timestamp;
- source-row ordinal;
- raw desired-position action and canonical action label;
- raw `do_predict` value and accepted/rejected classification;
- positive-volume gate;
- deterministic pre-trade entry and exit booleans and tags.

The recorder reads the dataframe only. It never writes columns or changes values, index, ordering or strategy signals.

## Signal parity

The recorded booleans reproduce the existing strategy predicates exactly:

- entry: accepted prediction, `target_long`, and positive volume;
- exit: accepted prediction and `target_flat`.

Rejected predictions retain their raw integer rejection code and produce no pre-trade signal. Integer-valued numeric action and gating values are normalized to JSON integers; unsupported actions and non-integral values fail closed.

## Deterministic artifacts

An explicitly enabled recorder with at least one row writes exactly:

- `rl-v2-action-observability-timeline-v1.jsonl`;
- `rl-v2-action-observability-manifest-v1.json`;
- `rl-v2-action-observability-summary-v1.json`.

Rows are ordered by pair, UTC timestamp and source-row ordinal. The manifest records immutable runtime provenance and the SHA-256 digest of the exact UTF-8 JSONL bytes. The summary reconciles row, action, prediction-gate and pre-trade signal counts by pair and in total.

Writing uses staged files and atomic replacement within the destination directory. An enabled recorder refuses to emit an empty evidence package.

## Fail-closed validation

`validate_action_observability_artifacts()` independently verifies:

- non-empty UTF-8 JSONL with a final newline;
- exact row fields and JSON scalar types;
- UTC timestamps, valid desired-position actions and deterministic row semantics;
- stable ordering and unique pair/timestamp identity;
- manifest schema, pair set, row count and timeline SHA-256;
- exact summary reconciliation.

Malformed rows, duplicates, missing columns, non-UTC timestamps, non-finite volume, invalid actions, metadata drift, pair mismatch, sensitive metadata keys and tampered evidence fail closed.

The manifest accepts only the prospectively declared metadata fields. Extra fields are forbidden, and secret-like keys are rejected before serialization.

## Tests

Focused synthetic tests prove:

- exact descriptor identity and no-execution boundaries;
- strict disabled-mode no-op behavior;
- dataframe immutability and signal-predicate parity;
- normalization of integer-valued predictions and preservation of rejection codes;
- atomic rejection of malformed and duplicate rows;
- deterministic bytes independent of pair capture order;
- manifest, digest and summary reconciliation;
- tamper detection;
- sensitive and unknown metadata rejection;
- defensive row copies.

No model, strategy runtime, exchange, historical dataset, consumed OOS window or protected final holdout is used by these tests.

## Isolation and future boundary

The implementation does not modify upstream `freqtrade/` core or any strategy, model, reward, feature, configuration, workflow or lifecycle behavior.

The following remain forbidden:

- consumed historical OOS `20260501-20260630`;
- protected final holdout `20260801-20260930`;
- prior seed rerun, removal or replacement;
- retuning, ranking, promotion, dry-run or live use;
- reopening Phase 6 or changing authoritative `selected_model=null`.

A later instrumented run still requires a separate prospective execution declaration. That declaration must identify a fresh unconsumed research window, freeze all runtime inputs and define how the recorder is wired through project-specific hooks before any model or backtest operation occurs.
