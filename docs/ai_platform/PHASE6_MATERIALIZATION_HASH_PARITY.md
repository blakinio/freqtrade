# Phase 6 Materialization Exact-Byte Hash Parity

Before the historical LightGBM-versus-XGBoost comparison can run, the hashes recorded in the canonical materialization plan must describe the exact config and manifest bytes that the execution runner later hashes into run provenance.

## Fixed mismatch

The Phase 6 harness previously used two different JSON representations:

- `config_sha256` and `manifest_sha256` were calculated from compact canonical JSON;
- `config.json` and `manifest.json` were written as indented, sorted JSON with a trailing newline.

`ai_platform.scripts.run_experiment` hashes the exact on-disk file bytes. The result-provenance contract requires those runtime hashes to equal the materialization hashes. A real comparison produced under the previous behavior would therefore fail provenance validation even when the semantic JSON content was identical.

The harness now uses one deterministic exact-byte serializer for materialized config and manifest files. The same serialized bytes are used both for:

- the SHA-256 values recorded in `materialization.json`;
- the actual `config.json` and `manifest.json` files written to disk.

Model experiment identities are unchanged. Their identity hash still uses the pre-existing compact canonical representation of the model identity object; only materialized file digests now follow the already-declared `exact_file_bytes` provenance semantics.

## Regression boundary

Tests write every generated model config and manifest through the harness serializer, hash the resulting files independently, and require equality with the corresponding `config_sha256` and `manifest_sha256` recorded by materialization.

This correction does not train a model, execute a backtest, access market data, change model parameters, or perform model selection.

The protected final holdout remains `20260801-20260930`. Frozen Phase 5.2 thresholds remain:

- `entry_prediction_threshold = 0.006`;
- `exit_prediction_threshold = -0.009`.

No retuning, promotion, live trading, or profitability claim is authorized.
