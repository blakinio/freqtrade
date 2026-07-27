# RL-v2 model-state provenance manifest assembler v1

## Status and authority

`ai_platform/provenance/rl_v2_model_state_manifest.py` is a dependency-light, inert assembler for the existing RL-v2 provenance manifest schema. It binds explicitly supplied semantic model-state digests to an explicitly supplied in-memory manifest draft, then delegates missing-field calculation, self-hashing and validation to the existing provenance core.

It does not obtain, discover, traverse, load or execute model state. It authorizes no training, inference, replay, backtest, market-data access, canonical run request, ranking, selection, promotion, dry-run, shadow, live trading or order submission. Phase 6 remains unchanged with `selected_model=null`.

## Public API

```python
from ai_platform.provenance import assemble_model_state_provenance_manifest

manifest = assemble_model_state_provenance_manifest(
    manifest_fields=prepared_manifest_fields,
    parameter_state_digest_sha256=prepared_parameter_digest,
    buffer_state_digest_sha256=prepared_buffer_digest,
    optimizer_state_digest_sha256=None,
)
```

The function is keyword-only and accepts:

- `manifest_fields`: a complete, already prepared in-memory mapping shaped as the existing schema;
- `parameter_state_digest_sha256`: the already computed semantic parameter-state digest;
- `buffer_state_digest_sha256`: the already computed semantic buffer-state digest;
- `optimizer_state_digest_sha256`: an optional already computed optimizer-state digest, supported only because the existing schema explicitly defines this nullable field.

The assembler imports only the Python standard library and the dependency-neutral RL-v2 core. Importing it does not import Torch or either optional Torch adapter.

## Bounded flow

```text
already materialized parameter state
    -> existing TensorRecord collection adapter
    -> semantic parameter digest

already materialized buffer state
    -> existing TensorRecord collection adapter
    -> semantic buffer digest

existing explicit provenance fields
+ semantic parameter digest
+ semantic buffer digest
+ optional semantic optimizer digest
    -> model-state manifest assembler
    -> existing finalize_manifest()
    -> existing validate_manifest()
    -> finalized self-hashed manifest
```

The assembler does not perform either adapter step. It accepts only the resulting digest strings and caller-prepared manifest values.

## Binding contract

The supplied draft must contain the existing model-state fields with explicit `null` values:

- `policy_state.trainable_parameters_digest_sha256`;
- `policy_state.buffers_digest_sha256`;
- `optimizer_state.state_digest_sha256`.

The assembler rejects a draft where any of these fields is absent, structurally invalid or already non-null. This prevents overwriting, duplicate authority or contradictory identities.

It binds the mandatory parameter and buffer digests to their separate policy-state fields. An optimizer digest binds only to the existing optimizer-state field; `None` preserves explicit-null semantics. The assembler does not derive initial or final policy-state digests, artifact digests or any other provenance value.

## Determinism and validation

The caller mapping is copied before binding. The original mapping and nested values are not modified.

The existing core remains authoritative for:

- lowercase SHA-256 syntax;
- exact known fields and required fields;
- canonical JSON and insertion-order independence;
- explicit-null and `missing_optional_fields` coherence;
- manifest self-hash calculation and verification;
- code, configuration, dependency, environment, dataset, seed and determinism structure;
- secret-like content and private-endpoint rejection;
- cache, consumed historical OOS and protected final-holdout prohibitions;
- all-false authorization, unchanged Phase 6 and `phase6_selected_model=null`.

Equivalent explicit mappings produce identical canonical bytes and hashes regardless of object insertion order. Changing a bound parameter, buffer or optimizer semantic digest changes the manifest self-hash.

## Fail-closed boundary

The assembler rejects:

- a non-mapping manifest input;
- non-string or empty mandatory digest inputs;
- a non-null optimizer input that is not a non-empty string;
- missing or non-object model-state sections;
- absent or already bound model-state fields;
- every malformed digest, unknown field, missing required field, invalid explicit-null structure, sensitive value, private endpoint, prohibited data-access flag, authorization flag, Phase 6 change or self-hash inconsistency rejected by the existing core.

No provenance identity is discovered, inferred or fabricated.

## Hard safety boundary

The module contains no Torch, NumPy, Stable-Baselines3, Gymnasium or Freqtrade import. It accepts no module, tensor, state dictionary, file or path and provides no model construction, state traversal, checkpoint/archive loading, filesystem inspection, network access, market-data access, training, inference, replay, backtesting, evaluation or order path.

Synthetic tests construct all values in memory and statically verify the import and inertness boundary. The existing AI Platform CI remains Torch-free. The existing full Freqtrade CI receives only the minimum path-classifier and mypy target additions needed to validate this module through established jobs.
