---
task_id: FTAI-20260727-rl-v2-model-state-provenance-manifest-assembler-v1
status: implementing
branch: docs/rl-v2-model-state-provenance-manifest-assembler-v1-declaration
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
depends_on:
  - FTAI-20260726-rl-v2-provenance-tooling-v1
  - FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1
  - FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1
owned_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2_model_state_manifest.py
  - tests/ai_platform/test_rl_v2_model_state_manifest.py
  - docs/ai_platform/RL_V2_MODEL_STATE_PROVENANCE_MANIFEST_ASSEMBLER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-model-state-provenance-manifest-assembler-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - docs/ai_platform/RL_V2_TORCH_TENSOR_RECORD_ADAPTER.md
  - docs/ai_platform/RL_V2_TORCH_STATE_DICT_RECORD_COLLECTION_ADAPTER.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1.md
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl_v2_torch.py
  - ai_platform/provenance/rl_v2_torch_state_dict.py
  - tests/ai_platform/test_rl_v2_provenance_tooling.py
  - tests/ai_platform/test_rl_v2_torch_state_dict_adapter.py
  - .github/workflows/ai-platform.yml
  - .github/workflows/ci.yml
  - tools/agents/checkpoint.py
  - tools/agents/resume.py
search_first:
  - current develop HEAD, all open PRs, active RL-v2/provenance task records, overlapping branches and recent commits
  - ownership overlap for provenance manifests, model-state identities, policy_state, optimizer_state, canonicalization, self-hash or CI routing
  - predecessor terminal state and exact-head CI evidence
optional_reads: []
---

# RL-v2 model-state provenance manifest assembler v1

## Goal

Add one dependency-light, deterministic and fail-closed assembler that combines an explicitly supplied schema-shaped RL-v2 provenance draft with separately supplied semantic parameter, buffer and optionally optimizer-state digests, then delegates finalization and validation to the existing provenance core.

The assembler is inert. It obtains no model state, loads no artifact, reads no data and grants no execution authority.

## Exact ownership

Implementation may modify only the six `owned_paths` declared in frontmatter.

The following paths and concerns are explicitly not owned:

- `ai_platform/provenance/rl_v2.py`;
- `ai_platform/provenance/rl-v2-provenance-schema-v1.json`;
- `ai_platform/provenance/rl_v2_torch.py`;
- `ai_platform/provenance/rl_v2_torch_state_dict.py`;
- existing provenance and Torch-adapter tests;
- Freqtrade core, strategy, model, runner, deployment, request and execution paths;
- every workflow except the minimum classifier and mypy edits in `.github/workflows/ci.yml`;
- market-data, historical OOS, protected final-holdout, ranking, selection, promotion and live-capital paths.

Any required change outside the owned paths is a blocker requiring a separately declared task.

## Public API proposal

```python
def assemble_model_state_provenance_manifest(
    *,
    manifest_fields: Mapping[str, object],
    parameter_state_digest_sha256: str,
    buffer_state_digest_sha256: str,
    optimizer_state_digest_sha256: str | None = None,
) -> dict[str, Any]:
    ...
```

The exact return annotation may use the repository's established mutable mapping type, but the function name, keyword-only shape and bounded authority must remain materially equivalent.

The function will be exported from `ai_platform.provenance` because it is standard-library-only. Importing the package or assembler must not import Torch, NumPy, Stable-Baselines3, Gymnasium, Freqtrade or either optional Torch adapter.

## Input and binding contract

`manifest_fields` is a caller-supplied, already prepared in-memory mapping shaped as the existing schema. It must include all existing top-level sections, all explicit nullable fields, and the existing helper fields `missing_optional_fields` and `self_hash_sha256`. The assembler will not discover or synthesize code, configuration, dependency, environment, dataset, experiment, seed, determinism, authorization or artifact identities.

The model-state digest slots must be explicitly unbound in the supplied draft:

- `policy_state.trainable_parameters_digest_sha256` must be `null`;
- `policy_state.buffers_digest_sha256` must be `null`;
- `optimizer_state.state_digest_sha256` must be `null`.

Supplying a non-null value in any of those slots is rejected as duplicate or contradictory model-state identity. The separately supplied parameter and buffer digest arguments are mandatory non-null strings. The optimizer digest remains optional because the existing schema already explicitly defines `optimizer_state.state_digest_sha256`; `None` preserves the existing explicit-null semantics.

The assembler will bind:

- parameter digest to `policy_state.trainable_parameters_digest_sha256`;
- buffer digest to `policy_state.buffers_digest_sha256`;
- optional optimizer digest to `optimizer_state.state_digest_sha256`.

It will not infer an initial policy digest, final policy digest, serialized-artifact digest or any other identity from these values.

## Deterministic and fail-closed behavior

The implementation will:

1. copy the caller mapping before any modification;
2. reject a non-mapping input;
3. reject missing or structurally invalid model-state sections and slots;
4. reject already bound model-state slots;
5. require non-null string parameter and buffer digest inputs;
6. require the optional optimizer digest to be `None` or a string;
7. bind the three semantic identities only to their existing schema fields;
8. call the existing `finalize_manifest()` so explicit missing fields and the existing self-hash contract remain authoritative;
9. call the existing `validate_manifest()` on the finalized result;
10. return the finalized copied mapping without mutating caller-owned mappings.

Malformed, uppercase or otherwise invalid digests will fail through the existing lowercase SHA-256 validator. Unknown fields, missing required fields, invalid explicit-null structure, secret-like content, private endpoints, prohibited authorization, cache restore, consumed historical OOS, protected final holdout, Phase 6 changes and non-null `phase6_selected_model` will fail through the existing validator.

Equivalent explicit inputs must produce identical canonical JSON bytes and identical self-hashes regardless of mapping insertion order. Changing any bound semantic model-state digest must change the finalized self-hash.

## No-execution and no-data-access boundary

The assembler must not:

- accept `torch.nn.Module`, tensors, state dictionaries, files or paths;
- call `state_dict()`, `named_parameters()`, `named_buffers()` or `load_state_dict()`;
- import Torch or optional Torch adapters;
- construct, traverse, execute, train or infer with a model;
- perform PPO, replay, backtesting, evaluation or seed reruns;
- load checkpoints, pickle, Torch archives or safetensors;
- inspect filesystems, caches, artifact directories or environment discovery APIs;
- access a network, market data, consumed historical OOS or protected final holdout;
- create a canonical run request or modify an execution workflow;
- rank, select, promote or authorize dry-run, shadow, live trading or order submission;
- alter Phase 6 or `selected_model=null`;
- add credentials, private endpoints, dependencies, jobs, runners or dynamic installation.

## Test plan

Focused synthetic in-memory tests will cover:

- deterministic finalized output and canonical bytes for equivalent mappings with different insertion order;
- binding of parameter and buffer digests to separate existing fields;
- optional optimizer digest binding and explicit-null behavior;
- every semantic digest changing the final self-hash;
- malformed and uppercase digest rejection through the existing validator;
- non-string or null mandatory digest rejection;
- unknown top-level and nested field rejection;
- missing required field rejection;
- rejection of pre-bound parameter, buffer or optimizer slots;
- explicit-null and `missing_optional_fields` coherence;
- caller mapping immutability;
- finalized self-hash validation and tampering rejection;
- secret-like content and private endpoint rejection;
- consumed historical OOS and protected final-holdout prohibition;
- Phase 6 and `phase6_selected_model=null` preservation;
- import and AST proof that the assembler has no Torch, filesystem, model-loading, network, market-data or execution path.

All test values are synthetic and constructed in memory. No historical model, checkpoint, cache, experiment artifact or market dataset may be read.

## CI routing plan

Lightweight AI Platform CI already covers the new source, focused tests and documentation without Torch.

The existing Freqtrade CI classifier will receive only the new assembler source and focused test paths in the existing provenance core-routing case so full repository tests and quality checks run. The existing mypy command will receive only the new assembler module. No new workflow, job, runner, dependency, cache, dynamic installation or Torch installation will be added.

## Governance stages

1. This declaration-only PR changes exactly this task record.
2. Implementation starts only after the declaration PR merges.
3. A fresh implementation branch starts from then-current `develop` and modifies only declared paths.
4. Implementation merge requires exact-head AI Platform CI, Freqtrade CI including CI Gate, security analysis, changed-path audit and zero unresolved review threads.
5. A fresh closeout branch starts from the implementation merge commit and changes exactly this task record.
6. Closeout merge requires exact-head validation, one-file audit and zero unresolved review threads.

## Terminal acceptance criteria

- declaration-first governance is proven;
- no overlapping active ownership exists;
- the assembler uses only the existing schema, missing-field calculation, canonical JSON, finalization, validation and self-hash contract;
- parameter and buffer semantic identities are mandatory and separately bound;
- optimizer identity is optional only through the already existing schema field;
- equivalent explicit inputs produce identical canonical bytes and hashes;
- any semantic model-state digest change changes or invalidates the manifest;
- missing provenance remains explicit and is never fabricated;
- caller inputs remain unchanged;
- no Torch import, model traversal, loading, execution, training, inference, replay, backtest, market-data or protected-data path exists;
- Phase 6 remains unchanged and `selected_model` remains null;
- focused tests, Ruff, Ruff format and mypy pass;
- exact-head required CI and security checks pass;
- implementation and one-file closeout PRs merge with zero unresolved review threads;
- terminal checkpoint records exact PR numbers, final heads, merge SHAs, changed-path audit and workflow evidence;
- terminal `unknown`, `conflicts` and `blockers` are empty.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T18:49:00+02:00
head: 05d585fcc0af1457442017057b2f37c0fc7171b0
branch: docs/rl-v2-model-state-provenance-manifest-assembler-v1-declaration
pr: none
status: implementing
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1.md
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl_v2_torch_state_dict.py
  - .github/workflows/ai-platform.yml
  - .github/workflows/ci.yml
owned_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2_model_state_manifest.py
  - tests/ai_platform/test_rl_v2_model_state_manifest.py
  - docs/ai_platform/RL_V2_MODEL_STATE_PROVENANCE_MANIFEST_ASSEMBLER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-model-state-provenance-manifest-assembler-v1.md
proven:
  - Current develop HEAD is 05d585fcc0af1457442017057b2f37c0fc7171b0 after PR 493 merged.
  - The requested AI_TRADING_PLATFORM_ROADMAP.md path is absent; the repository source of truth is docs/ai_platform/ROADMAP.md.
  - Provenance tooling and both Torch adapter predecessor tasks are terminal ready with unknown, conflicts and blockers empty.
  - The existing schema explicitly defines trainable parameter, buffer and nullable optimizer-state digest fields.
  - Existing finalize_manifest computes explicit missing paths and the self-hash; validate_manifest recomputes and verifies the self-hash.
  - All nine current open PRs are path- and scope-disjoint from the declared assembler ownership.
  - Relevant open-PR and branch searches found no active model-state provenance manifest assembler owner.
  - The requested task checkpoint does not already exist on develop.
  - AI Platform CI is standard-library compatible for this package; current Freqtrade CI requires bounded classifier and mypy additions for the new paths.
  - No repository deployment path is required or owned for this inert package.
derived:
  - The narrowest compositional API accepts a complete schema-shaped draft and separately binds only the three existing model-state digest slots.
  - Requiring those slots to be explicitly null prevents duplicate or contradictory authoritative identities.
  - Existing validation can remain the sole digest-format, authorization, protected-data and self-hash authority.
unknown:
  - Declaration PR number, exact final head, workflow run IDs and merge SHA until the declaration PR completes.
  - Implementation and closeout exact heads, workflow evidence and merge SHAs until those stages exist.
conflicts: []
first_failure:
  marker: LOCAL_CLONE_DNS_UNAVAILABLE
  evidence: The sandbox cannot resolve github.com for git clone; authenticated GitHub connector reads and writes are used, and exact-head repository CI remains authoritative.
rejected_hypotheses:
  - Treat completed predecessor tasks as active conflicting ownership.
  - Modify the existing schema or canonical hash format.
  - Accept a model, tensor, state dictionary, file or path.
  - Discover or load model state inside the assembler.
  - Permit duplicate pre-bound model-state identities.
  - Import Torch or optional Torch adapters from the dependency-light assembler.
  - Add a new workflow, job, runner, dependency or dynamic installation.
  - Read models, checkpoints, caches, market data or protected evaluation data.
  - Create a canonical request, execution workflow or runtime authority.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-rl-v2-model-state-provenance-manifest-assembler-v1.md
validation:
  - command: live develop, open PR, branch, task and ownership preflight
    result: PASS
    evidence: Develop 05d585fcc0af1457442017057b2f37c0fc7171b0 has no active overlapping PR, branch or task owner.
  - command: predecessor terminal checkpoint and exact-head evidence review
    result: PASS
    evidence: Base provenance and both Torch adapter tasks are terminal ready with recorded green exact-head CI and no blockers.
  - command: schema, implementation, focused tests and CI classifier review
    result: PASS
    evidence: Existing model-state fields, finalization contract, dependency boundaries and the minimum required CI routing changes are identified.
  - command: declaration changed-path audit
    result: NOT_RUN
    evidence: Declaration branch exists; PR is not open yet.
blockers: []
next_action: Create the one-file declaration commit, open the declaration PR, validate its exact head and merge it before starting implementation.
```
