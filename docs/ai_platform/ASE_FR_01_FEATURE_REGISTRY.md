# ASE-FR-01 Feature Registry service

## Purpose

ASE-FR-01 publishes the canonical Strategy Engine Feature Registry as a deterministic,
read-only Portal capability. It reuses the existing `FeatureRegistry` loader, parameter
validation and dependency resolver instead of creating a second registry implementation.

## Flow

```text
feature_registry.v1.yaml
→ Draft 2020-12 schema validation
→ FeatureRegistry semantic loading
→ deterministic feature read models and hashes
→ GET-only Portal API
→ append-only replay evidence
```

## API

The control plane exposes only read operations:

- `GET /v1/feature-registry/snapshot`
- `GET /v1/feature-registry/features`
- `GET /v1/feature-registry/features/{feature_id}`
- `GET /v1/feature-registry/resolve?feature_id=...`
- `GET /v1/feature-registry/replay`

Every route requires `model.read`. There is no create, update, delete, deployment,
order-submission or execution-authority route.

## Determinism and parity

The service publishes:

- the raw manifest SHA-256;
- a canonical SHA-256 for every feature definition;
- a snapshot SHA-256 binding registry version, manifest and ordered definitions;
- an append-only replay with contiguous sequence numbers and its own SHA-256.

`feature_registry_parity.v1.json` freezes the existing 21-feature prefix, selected
semantics and dependency-resolution outputs. New features may be appended, but silent
removal, reordering or mutation of frozen semantics fails tests.

## Safety boundary

- read-only metadata;
- no browser-to-Freqtrade path;
- no private exchange credentials;
- no `eval` or `exec`;
- no strategy generation, optimization, deployment or live trading;
- `execution_authority` is always false and contract validation rejects true.

## Validation

The AI Strategy Engine workflow validates the registry JSON Schema, package parity tests,
Portal read-model tests, deterministic repository E2E, Ruff, mypy, compileall and
architecture/security scans. The full repository CI remains the final merge gate.
