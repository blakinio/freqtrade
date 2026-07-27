---
task_id: FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1
status: ready
branch: docs/rl-v2-torch-tensor-record-adapter-v1-closeout
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#455 declaration; #457 implementation; terminal closeout pending"
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
  - tools/agents/checkpoint.py
  - tools/agents/resume.py
search_first:
  - current develop HEAD and open work overlapping RL-v2 provenance, TensorRecord or Torch adapters
optional_reads: []
---

# RL-v2 Torch TensorRecord adapter v1

## Goal

Provide one optional serialization-only adapter that converts one explicitly supplied in-memory `torch.Tensor` into the dependency-neutral `TensorRecord` from `ai_platform/provenance/rl_v2.py`.

## Implemented contract

The merged implementation provides:

- `tensor_to_record(*, logical_name, role, tensor)` for one caller-supplied in-memory tensor;
- exact logical name, role, dtype, shape, normalized source device and explicit byte-order framing;
- deterministic C-order bytes for contiguous and unambiguously serializable non-contiguous dense tensors;
- scalar and empty tensor support;
- fail-closed rejection of non-tensors, sparse or non-strided layouts, quantized, meta, nested, unsupported dtype/device and unresolved conjugate or negative views;
- synthetic CPU-only Torch tests and technical documentation;
- full-CI routing through the existing pinned Torch profile while the base provenance imports remain Torch-free.

## Safety boundary

The adapter does not discover, load, construct, traverse, execute or save models, state dictionaries, optimizers, environments, checkpoints, archives, caches or market data. It creates no request or execution workflow and grants no training, inference, backtest, replay, ranking, selection, promotion, dry-run, shadow or live authority. Phase 6 and `selected_model=null` remain unchanged.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T15:08:00+02:00
head: PENDING
base_develop: 22981a5e1a898f12730bb69354a8141a268598b2
branch: docs/rl-v2-torch-tensor-record-adapter-v1-closeout
pr: not_opened
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - docs/ai_platform/RL_V2_TORCH_TENSOR_RECORD_ADAPTER.md
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl_v2_torch.py
owned_paths:
  - .github/workflows/ci.yml
  - ai_platform/provenance/rl_v2_torch.py
  - tests/ai_platform/test_rl_v2_torch_adapter.py
  - docs/ai_platform/RL_V2_TORCH_TENSOR_RECORD_ADAPTER.md
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
proven:
  - Declaration PR 455 passed Freqtrade CI 30258421316 including CI Gate and zizmor 30258421923 on exact head 244bf010c533568ce5a4f00fe19ef52ad41fa44a, then merged as 90f24a649fa2a7fad376510d16691ed94a52970b.
  - Implementation PR 457 final exact head d5978598f3b297b5e59c8feb91992b338eccb59f passed AI Platform CI 30266438688, Freqtrade CI 30266438740 including pre-commit, documentation, all pinned-Torch core and compatibility lanes, Ruff, Ruff format, mypy, build and CI Gate, and zizmor 30266438701.
  - PR 457 changed exactly the five declared implementation paths, had no review threads, and merged as 22981a5e1a898f12730bb69354a8141a268598b2.
  - The public API preserves supported dtype, logical shape, normalized source device and exact logical bytes without casts or value conversion.
  - Base provenance imports neither Torch nor the optional adapter.
  - Synthetic tests cover 25 CPU cases including scalar, empty, contiguous, non-contiguous, all supported dtypes and fail-closed rejection paths.
  - No model, state dictionary, optimizer, checkpoint, archive, cache, network, market data, consumed OOS or protected holdout was accessed.
  - No canonical request, execution workflow, ranking, selection, promotion, runner behavior or Phase 6 state changed.
derived:
  - The adapter task is implementation-complete; only this one-file terminal closeout remains.
  - Any model traversal, artifact loading, canonical request or runtime execution requires a separate governed task.
unknown:
  - Closeout PR number, exact head, CI run IDs and merge SHA until the one-file closeout is opened and validated.
conflicts: []
first_failure:
  marker: RUFF_AND_FORMAT_DIAGNOSTICS_RESOLVED
  evidence: Exact diagnostics identified import grouping and one formatter change; both were corrected without changing adapter semantics or widening runtime authority.
rejected_hypotheses:
  - Import Torch from the dependency-neutral base provenance package.
  - Add Torch to lightweight AI Platform CI.
  - Load or traverse a model, state dictionary or optimizer.
  - Read real artifacts, caches or market data for tests.
  - Create a canonical request or execution workflow.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
validation:
  - command: declaration PR 455 exact-head repository CI
    result: PASS
    evidence: Freqtrade CI 30258421316 including CI Gate and zizmor 30258421923 succeeded.
  - command: implementation PR 457 final exact-head repository CI
    result: PASS
    evidence: AI Platform CI 30266438688, Freqtrade CI 30266438740 including CI Gate and zizmor 30266438701 succeeded on d5978598f3b297b5e59c8feb91992b338eccb59f.
  - command: implementation changed-path and review audit
    result: PASS
    evidence: Exactly five owned paths changed and no review threads were open before merge.
  - command: terminal closeout exact-head repository CI
    result: PENDING
    evidence: The one-file closeout PR has not yet been opened.
blockers:
  - Open and validate the one-file terminal closeout PR.
next_action: Open the one-file closeout PR, record its exact head and CI evidence, and merge it only after all required checks pass.
```
