---
task_id: FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1
status: ready
branch: docs/rl-v2-torch-state-dict-record-collection-adapter-v1-terminal-closeout
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#478 declaration; #484 implementation; terminal closeout pending"
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

## Implemented contract

The merged implementation provides:

- `state_dict_to_records(*, state_dict, role)` for one caller-supplied in-memory tensor mapping;
- `semantic_state_dict_digest(*, state_dict, role)` over only the generated records;
- exact-key deterministic ordering independent of insertion order;
- one-time `items()` materialization and duplicate logical-name detection;
- immutable `tuple[TensorRecord, ...]` output, including `()` for an empty mapping;
- roles restricted to `parameter` and `buffer`;
- fail-closed rejection of non-mappings, malformed items, non-string or invalid keys, nested mappings, non-tensors, unsupported dtypes and sparse tensors;
- exclusive delegation of tensor serialization to the existing `tensor_to_record()` adapter;
- synthetic CPU-only tests, technical documentation and existing pinned-Torch full-CI routing.

## Dependency and safety boundary

The optional module imports Torch, while dependency-neutral provenance imports neither Torch nor this adapter. No dependency, job, runner or dynamic installation was added.

The adapter does not accept or discover `torch.nn.Module`, call `model.state_dict()`, traverse models, load artifacts, checkpoints, archives or caches, support optimizer state, read network or market data, execute models, train, infer, replay or backtest, create canonical requests or execution workflows, change ranking or promotion, reopen Phase 6, or grant dry-run, shadow, live or order authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T18:04:00+02:00
head: 121f1b10dd584a81fb0ba93e83356833a2399110
base_develop: 121f1b10dd584a81fb0ba93e83356833a2399110
branch: docs/rl-v2-torch-state-dict-record-collection-adapter-v1-terminal-closeout
pr: none
status: ready
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
  - Predecessor task is terminal ready with unknown, conflicts and blockers empty; PRs 457, 472 and 475 are merged with recorded green exact-head CI.
  - Declaration PR 478 changed exactly this task record, final head 78348ac72015b91f403a9257a12d12c3549b1e1c, passed Freqtrade CI 30271647700 and zizmor 30271647734, had zero review threads, and merged as 11e7d49747040477b75356719c64afa456a7b0d8.
  - Implementation PR 484 final exact head 6bd0c941676e5bbe51350da9afe934ea5030c745 passed AI Platform CI 30281670238, Freqtrade CI 30281670255 and zizmor 30281670319.
  - Freqtrade CI 30281670255 passed pre-commit, documentation, all pinned-Torch core and compatibility lanes, coverage, Ruff, Ruff format, mypy, build and CI Gate.
  - Implementation PR 484 changed exactly the five declared owned paths; its workflow delta was exactly two additions and two removals.
  - Both historical security review threads created by temporary diagnostic permissions were resolved and outdated; zero review threads remained open before merge.
  - Implementation PR 484 merged as 121f1b10dd584a81fb0ba93e83356833a2399110.
  - The merged API preserves exact logical names, roles, dtype, shape and deterministic tensor bytes through the predecessor tensor adapter without casts or alternate serialization.
  - Tests cover empty, scalar, parameter, buffer, contiguous, non-contiguous, representative dtypes, ordering, digest binding, single materialization and fail-closed rejection paths.
  - No model, optimizer, artifact, cache, network, market data, consumed OOS or protected holdout was accessed.
  - No canonical request, execution workflow, ranking, selection, promotion, runner behavior, Phase 6 state or runtime authority changed.
derived:
  - This task is ready for terminal closeout after the one-file closeout PR records its own exact-head evidence and merges.
  - Any model traversal, artifact loading, optimizer support, canonical request or runtime execution requires a separate declared governed task.
unknown:
  - Terminal closeout PR number, exact heads, workflow runs, merge SHA and final develop SHA until closeout completes.
conflicts: []
first_failure:
  marker: RUFF_FORMATTING_DIAGNOSTIC_RESOLVED
  evidence: The pinned Ruff hook identified two assertion line-wrap changes; canonical formatting was committed, all temporary workflow permissions and diagnostic steps were removed, and final exact-head pre-commit plus zizmor passed.
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
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-state-dict-record-collection-adapter-v1.md
validation:
  - command: declaration PR 478 exact-head CI and audits
    result: PASS
    evidence: Freqtrade CI 30271647700 and zizmor 30271647734 succeeded on 78348ac72015b91f403a9257a12d12c3549b1e1c; exactly one declared path changed and zero review threads were open.
  - command: implementation PR 484 exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30281670238, Freqtrade CI 30281670255 including CI Gate, and zizmor 30281670319 succeeded on 6bd0c941676e5bbe51350da9afe934ea5030c745.
  - command: implementation changed-path and review audit
    result: PASS
    evidence: Exactly five owned paths changed, the workflow delta was two additions and two removals, and zero review threads were open before merge.
  - command: implementation merge
    result: PASS
    evidence: PR 484 merged exact head 6bd0c941676e5bbe51350da9afe934ea5030c745 as 121f1b10dd584a81fb0ba93e83356833a2399110.
blockers: []
next_action: Open the one-file terminal closeout PR, record its exact-head repository CI and audits, then merge only after Freqtrade CI, CI Gate, zizmor and zero-open-thread checks pass.
```
