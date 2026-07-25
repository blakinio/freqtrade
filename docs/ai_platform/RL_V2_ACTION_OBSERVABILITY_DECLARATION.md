# RL-v2 Action-Level Observability Declaration

## Purpose

The terminal seed-validity diagnosis preserved the frozen RL-v2 lifecycle seed-robustness decision as `inconclusive`. The two invalid seeds were associated with very long completed-position durations and sparse completed-position initiations, but the immutable artifacts retained no per-candle inference action, `do_predict`, or pre-trade signal timeline. The causal PPO mechanism therefore remains `unknown`.

This declaration prospectively freezes a research-only observability contract before any implementation. It authorizes no model change, training, backtest, market-data access, cache restore, seed rerun, retuning, ranking, promotion, dry-run or live operation.

## Frozen evidence gap

Existing RL-v2 code already exposes:

- desired-position actions `target_flat` and `target_long`;
- deterministic mapping to `hold_flat`, `enter_long`, `hold_long` and `exit_long`;
- count-level action, `do_predict`, and pre-trade signal observability;
- training-environment step information in memory.

The completed immutable backtest artifacts did not retain an inference-time row timeline. Counts and completed trades are insufficient to establish whether long positions persisted because the policy repeatedly emitted `target_long`, because accepted `target_flat` actions were absent, or because prediction gating suppressed an otherwise relevant action.

## Frozen capture surface

A later implementation may capture only the strategy inference dataframe after FreqAI prediction columns exist and after the exact deterministic entry/exit predicates are evaluated, but before Freqtrade trade-lifecycle handling.

The recorder must be observational:

- it must not alter dataframe values, strategy signals, action values, rewards, features, trade state, order handling or lifecycle behavior;
- it must be disabled by default behind an explicit research-only configuration flag;
- disabled mode must create no observability artifact;
- enabled mode must preserve exactly the same strategy signals as disabled mode;
- an enabled recorder may fail closed on malformed or ambiguous telemetry rather than silently emit incomplete evidence.

No upstream `freqtrade/` core modification is authorized. Any implementation must remain under project-specific `ai_platform/` and related test/documentation paths unless a new declaration explicitly changes that boundary.

## Frozen row schema

The normalized timeline must contain exactly one row per pair and UTC candle timestamp, sorted by pair, timestamp and source-row ordinal. Required row fields are:

- `pair`;
- `timestamp_utc`;
- `source_row_ordinal`;
- `action_raw`;
- `action_label` with values `target_flat` or `target_long`;
- `do_predict_raw`;
- `prediction_accepted`;
- `volume_positive`;
- `pre_trade_enter_long`;
- `pre_trade_exit_long`;
- `pre_trade_enter_tag`;
- `pre_trade_exit_tag`.

The recorder must reject duplicate pair/timestamp rows, invalid desired-position actions, missing required prediction columns, non-UTC timestamps and non-deterministic ordering.

The timeline must not contain secrets, private endpoints, wallet credentials, access tokens, model weights or raw feature vectors.

## Position and transition derivation

Runtime trade-state capture is not required and must not be added merely for this observability task. A later evidence-only analysis may derive current position state from immutable completed-trade intervals and then combine it with the retained desired-position action:

- flat plus `target_flat` -> `hold_flat`;
- flat plus `target_long` -> `enter_long`;
- long plus `target_long` -> `hold_long`;
- long plus `target_flat` -> `exit_long`.

This post-hoc derivation must be deterministic, explicit about candle-boundary assumptions and incapable of mutating runtime behavior.

## Frozen artifact contract

A later authorized execution must retain together:

- `rl-v2-action-observability-timeline-v1.jsonl`;
- `rl-v2-action-observability-manifest-v1.json`;
- `rl-v2-action-observability-summary-v1.json`;
- the immutable backtest result archive used for trade-interval reconciliation.

The manifest must record schema version, Git commit, strategy and model names and SHA-256 hashes, effective configuration SHA-256, FreqAI identifier, seed, timerange, timeframe, pairs, row count and timeline SHA-256. Duplicate pair/timestamp rows fail closed.

The timeline is workflow evidence, not a committed repository input.

## Future implementation acceptance

A separate bounded implementation task may add only the recorder, validator, deterministic serializer and tests. It must include:

- unit and synthetic-dataframe tests;
- deterministic serialization and digest tests;
- invalid-action, duplicate-row and missing-column fail-closed tests;
- secret-field rejection tests;
- disabled-mode no-op tests;
- enabled-versus-disabled signal-equivalence tests.

That implementation task may not train a model, run a backtest, restore a cache, download market data or select an evaluation window.

## Isolation

All future outputs remain research-only and non-promotable:

- `strict_oos=false`;
- `protected_final_validation=false`;
- profitability descriptive and non-gating;
- no statistical-proof, superiority, ranking, promotion, dry-run or live claim;
- consumed historical OOS `20260501-20260630` remains forbidden;
- protected final holdout `20260801-20260930` remains forbidden;
- Phase 6 remains complete with authoritative `selected_model=null`;
- no prior seed may be rerun, removed or replaced.

## Future sequence

This declaration does not authorize implementation or execution.

The next task must be a separate bounded implementation package that introduces the disabled-by-default project-specific recorder and tests without running any model or backtest. After that implementation is merged and validated, a second prospective execution declaration must select a fresh, previously unconsumed research window and freeze all execution inputs before any instrumented run.
