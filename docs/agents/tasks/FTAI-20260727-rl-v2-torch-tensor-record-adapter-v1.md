---
task_id: FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1
status: implementing
branch: docs/rl-v2-torch-tensor-record-adapter-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
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

Implementation is limited to the five owned paths in frontmatter. The public API will accept only `logical_name`, `role` and a caller-supplied tensor. It will preserve logical identity and role, normalize the source device through the existing core, preserve dtype and logical shape, stage data on CPU only when needed to obtain bytes, and emit deterministic C-order logical bytes with explicit byte order.

The adapter may detach from autograd, create a contiguous read-only staging representation and copy to CPU without modifying the source tensor. It must fail closed for non-tensors, unsupported dtype or device, sparse, quantized, meta or nested tensors, unresolved conjugate or negative view bits, and any state that cannot be serialized without silent casting or value conversion.

The base `ai_platform.provenance` package and `ai_platform.provenance.rl_v2` must remain importable without Torch. No eager adapter import may be added to `ai_platform/provenance/__init__.py`.

Implementation begins only after this declaration-only PR merges and a fresh implementation branch is created from the then-current `develop`.

## CI and dependency boundary

Torch remains optional and no dependency file is owned by this task. Lightweight `AI Platform CI` must not gain Torch. Static import/inertness tests may run there without importing the adapter.

The approved full `Freqtrade CI` installs `requirements-dev.txt`, which includes `requirements-freqai-rl.txt` and pinned Torch. Its current path classifier excludes `ai_platform/**` from core tests, so the implementation may make only two bounded changes in `.github/workflows/ci.yml`: route the adapter source and test paths to the existing core lane, and include the adapter module in that lane's existing mypy command. It must not add a job, runner, dependency, dynamic installation, model execution or market-data behavior.

No dynamic `pip install torch` is permitted. The adapter is not complete unless a real-Torch exact-head CI lane executes its tests successfully and the aggregate `CI Gate` passes.

## Absolute prohibitions

- no `torch.load`, `torch.save` or `torch.jit.load`;
- no model or optimizer construction, traversal, forward, backward, inference, training or step;
- no Stable-Baselines3, Gymnasium or Freqtrade runtime initialization;
- no filesystem, archive, checkpoint, state-dict, cache, network or market-data access;
- no backtest, replay, PPO execution or seed rerun;
- no canonical request, execution workflow, ranking, selection or promotion;
- no consumed historical OOS or protected final holdout access;
- no dry-run, shadow, live or runner changes;
- no CI dependency, runner or new-job changes beyond exact path routing and mypy coverage in the existing full CI lane;
- no Phase 6 or `selected_model=null` change;
- no schema or semantic change to `ai_platform/provenance/rl_v2.py` unless a separately documented blocking defect is proven.

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
- pre-commit, AI Platform CI, Freqtrade CI with real Torch, documentation, zizmor, checkpoint and resume gates pass on the exact relevant heads;
- `.github/workflows/ci.yml` changes only the exact adapter/test path routing and existing mypy target list;
- implementation and terminal closeout use separate fresh branches and PRs.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T12:48:00+02:00
head: 9f52b033dc8ccdbfe1cfca7a92184ff611998658
branch: docs/rl-v2-torch-tensor-record-adapter-v1
pr: "#455"
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
  - Current develop HEAD is e3c065c5d094e908e6d313323c082658740020b9; intervening merged PRs 451 and 452 are path-disjoint from all declared owned paths.
  - Provenance tooling task FTAI-20260726-rl-v2-provenance-tooling-v1 is terminal after declaration PR 408, implementation PR 412 and closeout PR 449.
  - Open PR, branch, task-id and API searches found no equivalent Torch-to-TensorRecord adapter work or conflicting ownership.
  - Existing TensorRecord validation binds logical name, role, dense element type, dtype, shape, normalized device, byte order and exact raw-byte length.
  - Lightweight AI Platform CI intentionally installs no Torch and must remain lightweight.
  - Freqtrade CI installs requirements-dev.txt, which includes requirements-freqai-rl.txt with pinned Torch, and runs the repository test suite plus aggregate CI Gate.
  - Current Freqtrade CI path classification does not set core=true for ai_platform-only changes, so the adapter tests would otherwise not run in the approved Torch environment.
  - Pre-commit runs mypy on changed Python files, but the full CI quality command currently excludes ai_platform; exact adapter mypy coverage therefore needs one bounded existing-command target addition.
  - The action-observability execution workflow also installs the RL profile but is request-path-specific and prohibited for this adapter task because it executes models and reads market data.
  - No additional AGENTS.md exists under the declared ai_platform/provenance, tests/ai_platform, docs/ai_platform or docs/agents/tasks paths.
derived:
  - Static tests can preserve lightweight AI Platform CI while a minimal full-CI routing change supplies the required real-Torch verification.
  - Reinterpreting a contiguous CPU uint8 view can expose exact tensor bytes without dtype conversion.
unknown:
  - Declaration exact final head, CI run IDs and merge SHA until PR 455 completes.
  - Implementation and closeout exact heads, CI evidence and merge SHAs until those PRs exist.
conflicts: []
first_failure:
  marker: LOCAL_CLONE_DNS_UNAVAILABLE
  evidence: The sandbox cannot resolve github.com for git clone; repository reads and writes use the authenticated GitHub connector, while targeted code tests use reconstructed exact source inputs and exact-head GitHub CI remains authoritative.
rejected_hypotheses:
  - Add Torch to lightweight AI Platform CI.
  - Treat an untriggered full-CI core lane as real-Torch verification.
  - Reuse the model-executing action-observability workflow.
  - Import the adapter from the base provenance package.
  - Load or traverse a model, state_dict or optimizer.
  - Read real artifacts, caches or market data for tests.
changed_paths:
  - docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
validation:
  - command: live develop, open-PR, branch, task and equivalent-scope preflight
    result: PASS
    evidence: Develop, active work and relevant task/API searches were inspected with no overlapping adapter ownership.
  - command: declaration PR 455 changed-path audit
    result: PASS
    evidence: GitHub reports exactly docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md changed.
  - command: approved Torch CI lane and routing preflight
    result: PASS
    evidence: Freqtrade CI installs pinned Torch, but ai_platform-only changes do not currently trigger core tests; the declaration owns a minimal routing and mypy-target correction without dependency changes.
  - command: python tools/agents/resume.py --task docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
    result: PASS
    evidence: The terminal predecessor checkpoint rendered the closed-task boundary and required separate adapter declaration.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md --require-checkpoint
    result: PASS
    evidence: The repository checkpoint validator accepted the declaration checkpoint.
  - command: python tools/agents/resume.py --task docs/agents/tasks/FTAI-20260727-rl-v2-torch-tensor-record-adapter-v1.md
    result: PASS
    evidence: The repository resume generator rendered a valid continuation with exactly one concrete next action.
blockers: []
next_action: Merge declaration PR 455 only after exact-head CI, review and mergeability checks pass; then create a fresh implementation branch from current develop.
```
