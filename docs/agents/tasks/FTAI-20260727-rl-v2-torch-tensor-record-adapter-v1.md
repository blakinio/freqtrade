---
task_id: FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1
status: ready
branch: feat/rl-v2-torch-tensor-record-adapter-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#457"
depends_on:
  - FTAI-20260726-rl-v2-provenance-tooling-v1
owned_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/rl_v2_torch.py
  - tests/ai_platform/test_rl_v2_torch_adapter.py
  - docs/ai_platform/RL_V2_TORCH_TENSOR_RECORD_ADAPTER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
required_reads:
  - AGENTS.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-hardening-contract.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2.py
  - tests/ai_platform/test_rl_v2_provenance_tooling.py
  - pyproject.toml
  - requirements-dev.txt
  - requirements-freqai-rl.txt
  - .pre-commit-config.yaml
  - .github/workflows/ai-platform.yml
  - .github/workflows/ci.yml
  - .github/workflows/ai-platform-rl-v2-action-observability-execution.yml
  - tools/agents/checkpoint.py
  - tools/agents/resume.py
search_first:
  - current develop HEAD, open PRs, branches and task records overlapping RL-v2, provenance, TensorRecord, Torch, policy state, optimizer state, model artifacts, determinism or action observability
  - approved exact-head CI lanes that install Torch without dynamic dependency changes
optional_reads: []
---

# RL-v2 Torch TensorRecord adapter v1

## Goal

Implement one optional adapter that converts one explicitly supplied in-memory `torch.Tensor` into the existing dependency-neutral `TensorRecord` from `ai_platform/provenance/rl_v2.py`.

The adapter is serialization-only. It must not discover, load, construct, execute or save a model, state dictionary, optimizer, environment, archive, checkpoint, cache, market-data input or run request.

## Bounded scope

Implementation is limited to the five owned paths in frontmatter. The public API accepts only `logical_name`, `role` and a caller-supplied tensor. It preserves logical identity and role, normalizes the source device through the existing core, preserves dtype and logical shape, stages data on CPU only when needed to obtain bytes, and emits deterministic C-order logical bytes with explicit byte order.

The adapter may detach from autograd, create a contiguous staging representation and copy to CPU without modifying the source tensor. It fails closed for non-tensors, unsupported dtype or device, sparse, quantized, meta or nested tensors, unresolved conjugate or negative view bits, and any state that cannot be serialized without silent casting or value conversion.

The base `ai_platform.provenance` package and `ai_platform.provenance.rl_v2` remain importable without Torch. The adapter is not imported from `ai_platform/provenance/__init__.py`.

## CI and dependency boundary

Torch remains optional and no dependency file is owned by this task. Lightweight `AI Platform CI` remains Torch-free and verifies static import and inertness boundaries.

The approved full `Freqtrade CI` installs `requirements-dev.txt`, which includes `requirements-freqai-rl.txt` and pinned Torch. The implementation changes only two bounded parts of `.github/workflows/ci.yml`: exact adapter/test path routing to the existing core lane and inclusion of the adapter module in the existing mypy command. No job, runner, dependency or dynamic installation is added.

## Absolute prohibitions

- no `torch.load`, `torch.save` or `torch.jit.load`;
- no model or optimizer construction, traversal, forward, backward, inference, training or step;
- no Stable-Baselines3, Gymnasium or Freqtrade runtime initialization;
- no filesystem, archive, checkpoint, state-dict, cache, network or market-data access;
- no backtest, replay, PPO execution or seed rerun;
- no canonical request, execution workflow, ranking, selection or promotion;
- no consumed historical OOS or protected final holdout access;
- no dry-run, shadow, live or runner changes;
- no Phase 6 or `selected_model=null` change.

## Acceptance criteria

- declaration PR changes only this task record and merges before implementation starts;
- one small public adapter converts only an explicitly passed `torch.Tensor`;
- all dtypes represented by `DTYPE_BYTE_WIDTHS` are preserved without casts;
- scalar, empty, contiguous and unambiguously serializable non-contiguous CPU tensors work;
- source values, layout, gradient requirement and gradient state are not modified;
- unsupported layouts, tensor categories, dtypes, devices and unresolved view bits fail closed;
- output passes `semantic_tensor_state_digest([record])`;
- semantically equal values produce equal records independent of storage layout;
- synthetic tests cover identity, role, dtype, shape, byte length, byte order and import boundaries;
- base provenance imports neither Torch nor the adapter;
- no file I/O, network, model loading or runtime execution marker exists;
- targeted compile, pytest, Ruff, Ruff format and mypy gates pass;
- pre-commit, AI Platform CI, Freqtrade CI with real Torch, documentation, zizmor, checkpoint and resume gates pass on exact relevant heads;
- implementation and terminal closeout use separate fresh branches and PRs.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T14:44:00+02:00
head: 6ab4aaaf6bedaacbea74a4dff0b4305793124c97
base_develop: 9709293face7b7c0e42a8c46971586981286fc6f
branch: feat/rl-v2-torch-tensor-record-adapter-v1
pr: "#457"
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-hardening-contract.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - ai_platform/provenance/rl_v2.py
  - .github/workflows/ai-platform.yml
  - .github/workflows/ci.yml
owned_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/rl_v2_torch.py
  - tests/ai_platform/test_rl_v2_torch_adapter.py
  - docs/ai_platform/RL_V2_TORCH_TENSOR_RECORD_ADAPTER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
proven:
  - Declaration PR 455 exact head 244bf010c533568ce5a4f00fe19ef52ad41fa44a passed Freqtrade CI 30258421316 including CI Gate and zizmor 30258421923, then merged as 90f24a649fa2a7fad376510d16691ed94a52970b.
  - The first complete implementation candidate head 0eea01c628d2f2ad3f54b7bb0e62c5cea6aae0ac passed AI Platform CI 30263551134, Freqtrade CI 30263551161 including pre-commit, documentation, all real-Torch core and compatibility lanes, mypy and aggregate CI Gate, and zizmor 30263551190.
  - Current develop advanced to 9709293face7b7c0e42a8c46971586981286fc6f only through eleven paths disjoint from all five owned paths.
  - The implementation branch was rebuilt directly from current develop 9709293face7b7c0e42a8c46971586981286fc6f with the same five-file diff and no other path changes.
  - Rebased head 6ab4aaaf6bedaacbea74a4dff0b4305793124c97 passed AI Platform CI 30265333136, Freqtrade CI 30265333192 including pre-commit, documentation, all real-Torch core and compatibility lanes, Ruff, Ruff format, mypy, build and aggregate CI Gate, and zizmor 30265332797.
  - Focused real-Torch tests cover 25 synthetic CPU cases across scalar, empty, contiguous, non-contiguous, supported dtypes and fail-closed rejection paths.
  - PR 457 is open and mergeable, changes exactly the five declared owned paths, and has zero review threads and zero submitted reviews.
  - Base provenance imports neither Torch nor the optional adapter.
  - No model, state dictionary, optimizer, checkpoint, archive, cache, network, market data, OOS or protected holdout was accessed.
derived:
  - The adapter implementation is complete and eligible for merge after the final checkpoint-head workflow cycle.
unknown:
  - Implementation merge SHA until PR 457 merges.
  - Closeout branch, PR, exact head, CI evidence and merge SHA until implementation merges.
conflicts: []
first_failure:
  marker: NONE
  evidence: Earlier lint and formatting findings were corrected; both complete implementation candidates passed all required repository gates.
rejected_hypotheses:
  - Add Torch to lightweight AI Platform CI.
  - Treat an untriggered full-CI core lane as real-Torch verification.
  - Reuse the model-executing action-observability workflow.
  - Import the adapter from the base provenance package.
  - Load or traverse a model, state_dict or optimizer.
  - Read real artifacts, caches or market data for tests.
changed_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/rl_v2_torch.py
  - tests/ai_platform/test_rl_v2_torch_adapter.py
  - docs/ai_platform/RL_V2_TORCH_TENSOR_RECORD_ADAPTER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
validation:
  - command: declaration PR 455 exact-head repository CI
    result: PASS
    evidence: Freqtrade CI 30258421316 including CI Gate and zizmor 30258421923 succeeded before declaration merge.
  - command: implementation candidate head 0eea01c628d2f2ad3f54b7bb0e62c5cea6aae0ac exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30263551134, Freqtrade CI 30263551161 including CI Gate and zizmor 30263551190 succeeded; pre-commit, docs, Ruff, Ruff format, mypy and all real-Torch test lanes passed.
  - command: rebased implementation head 6ab4aaaf6bedaacbea74a4dff0b4305793124c97 exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30265333136, Freqtrade CI 30265333192 including CI Gate and zizmor 30265332797 succeeded; all core and compatibility lanes used the approved pinned Torch profile.
  - command: implementation PR 457 changed-path audit
    result: PASS
    evidence: GitHub reports exactly the five declared owned paths.
  - command: review thread and review submission audit
    result: PASS
    evidence: GitHub reports zero review threads and zero submitted reviews.
  - command: final ready-checkpoint exact-head repository CI
    result: PENDING
    evidence: Required workflows must complete on the checkpoint commit before merge.
blockers:
  - Final ready-checkpoint AI Platform CI, Freqtrade CI including CI Gate, and zizmor are not yet terminal.
next_action: Observe exact-head workflows on the ready checkpoint; if all required gates pass and PR 457 remains mergeable with exactly five changed paths and no open review threads, merge the implementation and start a separate closeout branch from current develop.
```
