---
task_id: FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1
status: implementing
branch: feat/rl-v2-torch-state-dict-record-collection-adapter-v1
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
  - current develop HEAD, open PRs, task records, branches and commits overlapping state_dict, TensorRecord, rl_v2_torch, Torch provenance or model-state serialization
  - predecessor exact-head merge and required CI evidence
  - pinned-Torch routing and mypy coverage for the new paths
optional_reads: []
---

# RL-v2 Torch state-dict TensorRecord collection adapter v1

## Goal

Provide one optional serialization-only adapter that converts an explicitly supplied, already materialized in-memory `Mapping[str, torch.Tensor]` into a deterministic immutable tuple of dependency-neutral `TensorRecord` values and computes one semantic digest over that tuple.

The adapter obtains no mapping from a model and grants no model, artifact, data or execution authority.

## Public API

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

The declared names were retained because they match the repository's explicit keyword-only adapter convention.

## Implemented contract

`state_dict_to_records()`:

- accepts only a caller-supplied `Mapping` already present in memory;
- restricts collection roles to `parameter` or `buffer`, excluding optimizer state;
- calls and materializes `state_dict.items()` exactly once;
- requires key-value pairs with exact string keys;
- rejects duplicate logical names from non-standard mappings;
- rejects nested mappings and every non-tensor value;
- sorts by exact key independent of insertion order;
- delegates each tensor exclusively to `tensor_to_record()`;
- returns `tuple[TensorRecord, ...]`, including `()` for an empty mapping;
- does not modify the mapping or tensors.

`semantic_state_dict_digest()` obtains records only through `state_dict_to_records()` and passes them directly to `semantic_tensor_state_digest()`. It performs no cast, normalization, archive framing or alternate tensor serialization.

## Dependency and CI boundary

The new adapter imports Torch only in its optional module. Neither `ai_platform.provenance.__init__` nor `ai_platform.provenance.rl_v2` imports Torch or the adapter.

Lightweight AI Platform CI remains Torch-free. The existing full Freqtrade CI classifier routes the new source and test paths to the existing core lane, and the existing mypy command names the new module. No dependency, job, runner or dynamic installation was added.

## Absolute prohibitions

- no `torch.nn.Module` input or model construction;
- no `model.state_dict()`, `named_parameters()` or `named_buffers()`;
- no model traversal, forward, backward, training, inference, replay or backtest;
- no `load_state_dict`, `torch.load`, pickle, safetensors, checkpoint, archive, file or cache access;
- no optimizer-state support;
- no network or market-data access;
- no consumed historical OOS or protected final holdout access;
- no canonical request, execution workflow, runner, ranking, selection or promotion change;
- no Phase 6 or `selected_model=null` change;
- no dry-run, shadow, live or order authority;
- no runtime dependency expansion.

## Validation target

Before implementation merge, exact final-head evidence must include focused adapter tests, existing single-tensor regression, Ruff, Ruff format, mypy, required full repository CI, pinned-Torch core and compatibility lanes, build, CI Gate, zizmor, changed-path audit and zero open review threads.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T16:35:00+02:00
head: c4272449417be6a78b6eead12a17c10678ceca24
branch: feat/rl-v2-torch-state-dict-record-collection-adapter-v1
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
  - Predecessor task is terminal ready with unknown, conflicts and blockers empty; PRs 457, 472 and 475 are merged with green recorded exact-head CI.
  - Relevant open-PR, branch, task and recent-commit searches found no active equivalent or conflicting owner before declaration or implementation.
  - Declaration PR 478 changed exactly this task record, final head 78348ac72015b91f403a9257a12d12c3549b1e1c, and merged as 11e7d49747040477b75356719c64afa456a7b0d8.
  - Declaration head passed Freqtrade CI run 30271647700 and zizmor run 30271647734; changed-path audit found one declared file and review-thread audit found zero threads.
  - After develop advanced through disjoint PR 481, the implementation branch was cleanly re-rooted on current develop 6eede8936eab87ec5ba5eb5f733c9b07c3f39899 and only the five owned paths were replayed.
  - Public names match the declaration and existing keyword-only adapter convention.
  - Collection code materializes items once, validates role, item shape, string keys, duplicate names and tensor values, sorts keys, and delegates solely to tensor_to_record.
  - Digest code passes only state_dict_to_records output to semantic_tensor_state_digest.
  - Local reconstructed exact-relevant-source focused validation passed 27 tests on CPU Torch 2.10.0; a direct single-tensor regression also passed.
  - Workflow modification is bounded to the new source/test classifier patterns and the existing mypy target list.
  - Static tests prove dependency-neutral base imports no Torch or adapter and source contains no model traversal, artifact, market-data or execution markers.
  - Lightweight AI Platform CI remains unchanged and Torch-free; full CI routing and mypy additions reuse existing jobs and pinned dependencies.
derived:
  - Empty state has the existing semantic digest of an empty record tuple while still validating the role.
  - Restricting roles to parameter and buffer preserves the declared model-state boundary and rejects optimizer-state authority.
unknown:
  - Implementation PR number, exact final head, workflow runs, merge SHA and final review audit until the implementation PR completes.
  - Terminal closeout PR exact evidence and final develop SHA until closeout completes.
conflicts: []
first_failure:
  marker: LOCAL_CLONE_DNS_UNAVAILABLE
  evidence: The sandbox cannot resolve github.com for git clone; authenticated connector state and exact-head GitHub Actions are authoritative, with local validation using reconstructed exact relevant sources.
rejected_hypotheses:
  - Treat the closed predecessor task as active conflicting ownership.
  - Accept a torch.nn.Module or invoke model.state_dict.
  - Support optimizer state in the collection adapter.
  - Add alternate tensor serialization, casts or value normalization.
  - Import the adapter from the dependency-neutral provenance package.
  - Add Torch to lightweight AI Platform CI.
  - Add a dependency, job, runner or dynamic installation.
  - Read models, checkpoints, caches, market data or protected evaluation data.
  - Create a canonical request, execution workflow or runtime authority.
changed_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/rl_v2_torch_state_dict.py
  - tests/ai_platform/test_rl_v2_torch_state_dict_adapter.py
  - docs/ai_platform/RL_V2_TORCH_STATE_DICT_RECORD_COLLECTION_ADAPTER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1.md
validation:
  - command: declaration PR 478 exact-head CI and audits
    result: PASS
    evidence: Freqtrade CI 30271647700 and zizmor 30271647734 succeeded on 78348ac72015b91f403a9257a12d12c3549b1e1c; one changed path and zero review threads.
  - command: python -m compileall -q ai_platform tests/ai_platform
    result: PASS
    evidence: Reconstructed exact relevant source and test tree compiled without error.
  - command: pytest -q tests/ai_platform/test_rl_v2_torch_state_dict_adapter.py
    result: PASS
    evidence: 27 tests passed on CPU Torch 2.10.0 with no model, artifact, network or data access.
  - command: direct tensor_to_record single-tensor regression
    result: PASS
    evidence: Supported float32 record creation and unsupported uint16 fail-closed behavior passed.
  - command: clean re-root on current develop and bounded replay
    result: PASS
    evidence: Branch was force-moved to 6eede8936eab87ec5ba5eb5f733c9b07c3f39899 and only the five declared owned paths were reapplied.
blockers: []
next_action: Open the implementation PR, fix only exact-head failures within owned paths, then merge after all required CI, changed-path and review-thread audits pass.
```
