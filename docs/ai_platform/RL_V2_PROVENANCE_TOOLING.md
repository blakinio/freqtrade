# RL-v2 provenance tooling v1

## Status and authority

This package is static and inert. It defines a versioned provenance manifest, canonical JSON bytes, semantic tensor-state digests, deterministic self-hashing and fail-closed validators for a separately authorized future RL-v2 experiment.

It does not authorize or provide model training, inference, backtesting, replay, seed reruns, market-data access, canonical run requests, execution workflows, ranking, selection, promotion, dry-run, shadow or live activity. Phase 6 remains unchanged with `selected_model=null`.

## Files

- `ai_platform/provenance/rl-v2-provenance-schema-v1.json` is the human- and machine-readable static schema.
- `ai_platform/provenance/rl_v2.py` is the standard-library canonicalization, digest and validation core.
- `tests/ai_platform/test_rl_v2_provenance_tooling.py` uses only synthetic structures created in the test module.

The Python validator is authoritative for rules that JSON Schema cannot fully express, including self-hash verification, sorted explicit-missing paths, duplicate logical identities, device normalization, tensor byte-length coherence and secret-like content rejection.

## Canonical JSON contract

`canonical_json_bytes()` applies one policy:

- UTF-8 encoding with strict error handling;
- object keys sorted lexicographically by Python string value;
- compact separators `,` and `:` with no insignificant whitespace;
- list order preserved exactly and treated as semantically meaningful;
- object insertion order ignored;
- JSON integers accepted, but booleans are not treated as integers by validators;
- all floats rejected, including finite floats, `NaN`, `Infinity` and `-Infinity`;
- strings, booleans and `null` use their normal JSON representations;
- locale is not read or used;
- exactly one trailing line-feed byte (`0x0a`);
- tuples, sets, bytes, non-string object keys and custom objects rejected.

Decimal or scientific quantities must be represented by a separately defined canonical string field in a future schema revision. Version 1 does not silently convert them.

## Semantic tensor-state digest

`TensorRecord` is a dependency-light representation. The core does not import Torch, NumPy, Stable-Baselines3, Gymnasium, Freqtrade or a model implementation.

For each entry, the digest binds:

- sorted `logical_name`;
- role: `parameter`, `buffer` or `optimizer_state`;
- element type;
- dtype;
- shape;
- normalized device;
- byte order;
- raw bytes.

Metadata and raw bytes are independently length-framed before SHA-256. The digest therefore does not depend on mapping insertion order, file paths, modification times, ZIP timestamps, archive member order, filesystem metadata or temporary runner directories.

Device normalization maps `cpu:0` to `cpu`, and `gpu`, `gpu:0`, `cuda` and `cuda:0` to `cuda:0`. Indexed CUDA and XPU labels retain their numeric index. Unsupported or host-dependent labels fail closed.

The core rejects duplicate logical names, unknown roles, unknown dtypes, negative dimensions, native or unspecified multi-byte order and any raw-byte length inconsistent with dtype and shape. A future Torch adapter, if separately declared, must convert runtime tensors to `TensorRecord`; no adapter is included or invoked here.

## Manifest and self-hash

The top-level manifest requires every schema field. Nullable fields are present with explicit `null`; silent omission is invalid. `missing_optional_fields` must be sorted, unique and exactly equal the fixed nullable paths whose value is `null`.

`compute_manifest_self_hash()` removes only `self_hash_sha256`, canonicalizes every remaining field and computes SHA-256. No other field is excluded. `finalize_manifest()` fills the explicit-missing list, computes the self-hash and revalidates the result. `validate_manifest()` recomputes the digest and rejects any mismatch.

Changing any protected scalar, list order, nested structure, artifact reference, authorization flag or explicit-missing declaration changes or invalidates the self-hash.

## Fail-closed boundaries

The validator rejects:

- missing required or additional unknown fields;
- schema versions other than `1`;
- unknown provenance classifications;
- determinism classes outside the three frozen values;
- malformed lowercase SHA-256 values;
- inconsistent self-hashes;
- duplicate logical tensor or artifact identities;
- floats and non-finite numbers;
- implicit optional-field omission or an incorrect explicit-missing list;
- tensor dtype, shape, byte-order or byte-length inconsistency;
- required artifacts marked absent;
- secret-like field names or credential-like values;
- private endpoint values;
- dynamic dependency installation;
- cache restore;
- any execution, market-data, canonical-request, ranking, selection, promotion or live authorization;
- consumed historical OOS or protected final holdout access;
- a Phase 6 change or any non-null `phase6_selected_model`.

A determinism class is retained metadata only. It is not proof that an execution was deterministic.

## Secret policy

Version 1 rejects rather than persists suspected credential material. It does not attempt lossy automatic redaction. Callers must sanitize outside this core and provide only non-secret values. Recognized API-key, secret, token, password, cookie, authorization-header, private-endpoint and credential field names fail closed, as do bearer/basic credential values and private network endpoints.

No real credential values or fixtures are present in this package.

## Synthetic validation boundary

The tests construct small in-memory dictionaries and byte strings. They do not read market data, trained models, prediction caches, existing artifacts, consumed historical OOS or the protected final holdout. They statically inspect imports and file-I/O markers to prove that the core has no RL runtime import or data-reading path.
