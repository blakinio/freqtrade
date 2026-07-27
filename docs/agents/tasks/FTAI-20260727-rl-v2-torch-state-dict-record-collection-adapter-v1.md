---
task_id: FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1
status: implementing
branch: docs/rl-v2-torch-state-dict-record-collection-adapter-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
depends_on:
  - FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1
  - FTAI-20260726-rl-v2-provenance-tooling-v1
owned_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/rl_v2_torch_state_dict.py
  - tests/ai_platform/test_rl_v2_torch_state_dict_adapter.py
  - docs/ai_platform/RL_V2_TORCH_STATE_DICT_RECORD_COLLECTION_ADAPTER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1.md
required_reads:
  - AGENTS.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/REPOSITORY_MAP.md
  - docs/agents/CONTEXT_ROUTING.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - docs/ai_platform/RL_V2_TORCH_TENSOR_RECORD_ADAPTER.md
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl_v2_torch.py
  - tests/ai_platform/test_rl_v2_provenance_tooling.py
  - tests/ai_platform/test_rl_v2_torch_adapter.py
  - .github/workflows/ai-platform.yml
  - .github/workflows/ci.yml
  - tools/agents/checkpoint.py
  - tools/agents/resume.py
search_first:
  - current develop HEAD, open PRs, active task records, branches and recent commits overlapping state_dict, TensorRecord, rl_v2_torch, Torch provenance or model-state serialization
  - exact-head predecessor merge and required CI evidence
  - approved pinned-Torch lane routing for the new source and test paths
optional_reads: []
---

# RL-v2 Torch state-dict TensorRecord collection adapter v1

## Goal

Implement one optional serialization-only adapter that converts an explicitly supplied, already materialized in-memory `Mapping[str, torch.Tensor]` into a deterministic immutable collection of dependency-neutral `TensorRecord` values and computes one semantic digest over that collection.

The adapter must neither obtain a mapping from a model nor discover, load, construct, traverse, execute or save models, optimizers, environments, checkpoints, archives, caches, market data or execution requests.

## Bounded scope

Implementation is limited to the five owned paths in frontmatter. The public API is planned as:

```python
def state_dict_to_records(
    *,
    state_dict: Mapping[str, torch.Tensor],
    role: str,
) -> tuple[TensorRecord, ...]:
    ...


def semantic_state_dict_digest(
    *,
    state_dict: Mapping[str, torch.Tensor],
    role: str,
) -> str:
    ...
```

The exact names may change only if an existing repository convention requires it and the reason is recorded here and in the technical documentation.

## Collection contract

`state_dict_to_records()` will:

- accept only a caller-supplied `Mapping` already present in memory;
- materialize `state_dict.items()` exactly once;
- require textual keys and preserve each exact key as `logical_name`;
- reject duplicate logical names even when a non-standard `Mapping.items()` supplies them;
- deterministically sort entries by key independent of insertion order;
- delegate every tensor conversion to `tensor_to_record()` without alternate tensor serialization;
- pass the caller-supplied role unchanged to every record;
- return `tuple[TensorRecord, ...]` and return an empty tuple for an empty mapping;
- leave the mapping, keys and tensors unmodified.

The adapter will fail closed for non-mappings, non-string keys, invalid logical names, non-tensor values, nested mappings, metadata entries, lists, tuples, arbitrary objects and every tensor rejected by `tensor_to_record()`.

## Digest contract

`semantic_state_dict_digest()` will compute `semantic_tensor_state_digest()` only over records produced by `state_dict_to_records()`. It will not cast, normalize values, traverse a model or add archive/filesystem metadata.

The digest will be insertion-order independent and will bind each record's key, role, dtype, shape, normalized source-device framing, byte order and logical bytes. The empty mapping has the deterministic digest defined by the existing empty-record semantic digest.

## Dependency and CI boundary

Torch remains optional. The dependency-neutral `ai_platform.provenance` package and `ai_platform.provenance.rl_v2` must not import the new adapter or Torch.

Lightweight AI Platform CI remains Torch-free. The existing full Freqtrade CI installs the pinned Torch profile. Current path routing names only the single-tensor source and test, and current mypy explicitly names only the single-tensor module, so this task may add the new source/test paths to that existing routing case and add the new module to the existing mypy command. No job, runner, dependency or dynamic installation may be added.

## Absolute prohibitions

- no `torch.nn.Module` input;
- no `model.state_dict()`, `named_parameters()` or `named_buffers()`;
- no model construction or traversal;
- no `load_state_dict`, `torch.load`, pickle, safetensors, checkpoint, archive, file or cache access;
- no optimizer-state support;
- no forward, backward, training, inference, replay, backtest or environment execution;
- no network or market-data access;
- no consumed historical OOS or protected final holdout access;
- no canonical request, execution workflow, runner, ranking, selection or promotion change;
- no Phase 6 or `selected_model=null` change;
- no dry-run, shadow, live or order authority;
- no runtime dependency expansion.

## Acceptance criteria

- declaration-only PR changes exactly this task record and merges before implementation starts;
- predecessor task is terminal, PRs 457, 472 and 475 are merged, and predecessor exact-head required CI is green;
- no active equivalent or conflicting owner exists at implementation start;
- standard dict, OrderedDict and compatible Mapping inputs work;
- items are materialized once, keys are unique strings, records are key-sorted and output is a tuple;
- empty, scalar, empty-tensor, contiguous and supported non-contiguous values work;
- parameter and buffer roles work through caller-supplied role;
- bool, integer, floating and complex dtypes are covered;
- insertion order cannot change records or digest;
- key, role, value, dtype and shape changes change the digest;
- invalid mappings, keys, values, nested mappings, duplicate items and single-tensor adapter failures propagate fail closed;
- base provenance remains Torch-free;
- source contains no model traversal, artifact loading, market-data or execution marker;
- focused tests, single-tensor regression, Ruff, Ruff format and mypy pass;
- full required CI, pinned-Torch core and compatibility lanes, build and CI Gate pass on exact final heads;
- changed-path and review-thread audits pass before every merge;
- implementation and terminal closeout use fresh branches and separate PRs.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T15:40:00+02:00
head: 59775a93fb606ac5bf25796f3f43ef912928bade
branch: docs/rl-v2-torch-state-dict-record-collection-adapter-v1
pr: none
status: implementing
context_routes:
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - docs/ai_platform/RL_V2_TORCH_TENSOR_RECORD_ADAPTER.md
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl_v2_torch.py
  - .github/workflows/ai-platform.yml
  - .github/workflows/ci.yml
owned_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/rl_v2_torch_state_dict.py
  - tests/ai_platform/test_rl_v2_torch_state_dict_adapter.py
  - docs/ai_platform/RL_V2_TORCH_STATE_DICT_RECORD_COLLECTION_ADAPTER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1.md
proven:
  - Current develop HEAD is 59775a93fb606ac5bf25796f3f43ef912928bade.
  - Predecessor task FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1 is terminal with status ready, unknown empty, conflicts empty and blockers empty.
  - PR 457 merged as 22981a5e1a898f12730bb69354a8141a268598b2, PR 472 merged as 813d59fe59e2becc42f3b6942125da28edec2cd3 and PR 475 merged as 36ae30742f21cbea772220ea2529c75be335e6b4.
  - Implementation head d5978598f3b297b5e59c8feb91992b338eccb59f passed AI Platform CI 30266438688, Freqtrade CI 30266438740 including CI Gate, and zizmor 30266438701.
  - Terminal evidence head e95433712ad5cfc4cdeed05accffff9be9ebeca8 passed Freqtrade CI 30268515759 and zizmor 30268515673.
  - Open PRs 477, 474, 465, 453 and 109 are path- and scope-disjoint from state-dict TensorRecord serialization.
  - Relevant open-PR, branch, task-id and recent-commit searches found no active equivalent or conflicting state_dict, TensorRecord, rl_v2_torch, Torch provenance or model-state serialization owner.
  - Existing tensor_to_record is the single source of truth for dtype, shape, source device, byte order and logical bytes, and semantic_tensor_state_digest sorts by logical name and rejects duplicates.
  - Lightweight AI Platform CI installs no Torch, while full Freqtrade CI installs requirements-dev.txt and routes only the existing single-tensor adapter paths to its pinned-Torch core lane.
  - docs/agents/REPOSITORY_MAP.md and docs/agents/CONTEXT_ROUTING.md do not exist on current develop; no substitute content was inferred.
derived:
  - A collection adapter can remain serialization-only by accepting Mapping directly, materializing items once, validating keys and values, sorting by key and delegating exclusively to tensor_to_record.
  - The current full-CI classifier and mypy command require bounded additions for the new module and test paths.
unknown:
  - Declaration exact final head, CI run IDs and merge SHA until the declaration PR completes.
  - Implementation and terminal closeout exact heads, CI evidence and merge SHAs until those PRs exist.
conflicts: []
first_failure:
  marker: LOCAL_CLONE_DNS_UNAVAILABLE
  evidence: The sandbox cannot resolve github.com for git clone; repository reads and writes use the authenticated GitHub connector, focused tests use reconstructed exact relevant sources, and exact-head GitHub CI remains authoritative.
rejected_hypotheses:
  - Treat the closed single-tensor task as conflicting ownership.
  - Accept a torch.nn.Module or invoke model.state_dict.
  - Add alternate tensor serialization or normalize tensor values.
  - Import the adapter from the dependency-neutral provenance package.
  - Add Torch to lightweight AI Platform CI.
  - Add a dependency, job, runner or dynamic installation.
  - Read model artifacts, checkpoints, caches or market data.
  - Create a canonical request or execution workflow.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1.md
validation:
  - command: live develop, predecessor, PR, branch, task and equivalent-scope preflight
    result: PASS
    evidence: All mandatory predecessor and overlap gates passed on develop 59775a93fb606ac5bf25796f3f43ef912928bade.
  - command: predecessor exact-head workflow verification
    result: PASS
    evidence: Required implementation and terminal-evidence workflows are completed successfully on their recorded final heads.
  - command: dependency and pinned-Torch CI routing review
    result: PASS
    evidence: Lightweight CI stays Torch-free; the existing full CI requires only bounded path and mypy target additions.
  - command: required repository reads
    result: PASS
    evidence: All present required paths were read; the two requested routing-map paths are proven absent on current develop.
blockers: []
next_action: Open and merge the declaration-only PR after exact-head CI, changed-path, review-thread and mergeability checks pass; then create the implementation branch from current develop.
```
