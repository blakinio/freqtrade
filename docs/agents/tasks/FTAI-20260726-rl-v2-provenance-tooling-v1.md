---
task_id: FTAI-20260726-rl-v2-provenance-tooling-v1
status: implementing
branch: feat/rl-v2-provenance-tooling-v1
base_branch: develop
created: 2026-07-26
updated: 2026-07-27
related_pr: "408"
owned_paths:
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl-v2-provenance-schema-v1.json
  - tests/ai_platform/test_rl_v2_provenance_tooling.py
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-hardening-contract.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
  - docs/ai_platform/RL_V2_SEED_EFFECTIVENESS_DETERMINISM_AUDIT.md
  - ai_platform/experimental_model_research/rl-v2-seed-effectiveness-determinism-audit-v1.json
  - ai_platform/scripts/rl_v2_action_observability_execution_run_request.py
  - ai_platform/scripts/rl_v2_action_observability_execution_evidence.py
  - tools/agents/checkpoint.py
  - tools/agents/resume.py
search_first:
  - current develop HEAD and all open PRs and branches overlapping RL-v2, PPO, seeds, RNG, determinism, policy state, optimizer state, provenance, model artifacts or action observability
  - existing equivalent task records, serializers, digest helpers, validators, schemas and synthetic-test conventions
optional_reads: []
---

# RL-v2 provenance tooling v1

## Goal

Implement only static or inert, dependency-light provenance schemas, canonical JSON serialization, deterministic semantic state digests, self-hashed manifest helpers and fail-closed validators for separately authorized future RL-v2 experiments.

This task creates no model execution path, canonical run request, workflow trigger or market-data capability. It does not import or initialize RL, PPO, Stable-Baselines3, Torch policy code or an environment.

## Implemented contract

The package defines:

- a versioned, additional-fields-forbidden provenance manifest;
- integer-only canonical JSON with sorted keys, preserved list order and exactly one trailing LF;
- dependency-light `TensorRecord` framing and semantic SHA-256 over logical name, role, element type, dtype, shape, normalized device, byte order and raw bytes;
- deterministic self-hashing that excludes only `self_hash_sha256`;
- explicit null and `missing_optional_fields` coherence;
- secret-like content rejection;
- fail-closed authorization, OOS, holdout and Phase 6 boundaries;
- synthetic unit tests and technical documentation.

A future Torch adapter is intentionally absent. No runtime tensor, model artifact or market-data file is read by this package.

## Absolute prohibitions

- no model import for training or inference;
- no PPO, Stable-Baselines3, Torch policy or RL environment initialization;
- no market-data read, download, transformation or hashing;
- no training, backtest, inference, replay or seed rerun;
- no existing trained-model or cache access;
- no canonical request or execution workflow;
- no PPO, reward, strategy, lifecycle, feature, target or action-semantic change;
- no consumed historical OOS or protected final holdout access;
- no ranking, selection, promotion, dry-run, shadow or live behavior;
- no Phase 6 or `selected_model=null` change.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T00:12:00+02:00
head: PENDING
branch: feat/rl-v2-provenance-tooling-v1
pr: not_opened
status: validating
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-hardening-contract.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - ai_platform/provenance/rl_v2.py
owned_paths:
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl-v2-provenance-schema-v1.json
  - tests/ai_platform/test_rl_v2_provenance_tooling.py
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
proven:
  - Declaration PR 408 passed exact-head Freqtrade CI 30222399535 and zizmor 30222399566 and merged as 069243be28f373671c4f2b2c0223a35a0cb34337 from exact head 887b7ff18003f6b42a0b933e2e6331b5d0006f61.
  - The implementation branch starts exactly from declaration merge 069243be28f373671c4f2b2c0223a35a0cb34337.
  - The core imports only Python standard-library modules and has no file, network, model or market-data read path.
  - Canonical JSON is UTF-8, sorted-key, compact, integer-only and ends with exactly one LF.
  - Semantic tensor-state digests sort logical names and bind role, element type, dtype, shape, normalized device, byte order and raw bytes.
  - Manifest self-hashing excludes only self_hash_sha256 and validation recomputes it.
  - Authorization flags, cache restore, consumed OOS, protected holdout, Phase 6 changes and non-null selected_model fail closed.
  - Tests use only synthetic dictionaries and byte strings created in the test module.
  - Local targeted compilation and 23 synthetic tests pass in the isolated workspace.
derived:
  - A separately declared runtime adapter can later translate runtime tensors into TensorRecord without changing the canonical core.
  - The digest distinguishes policy parameters, buffers and optimizer entries without depending on archive or filesystem metadata.
unknown:
  - Exact implementation PR number, final head SHA, CI run identifiers and merge SHA until GitHub creates and completes them.
  - Ruff, Ruff format, mypy, codespell and full-repository results until exact-head CI runs.
conflicts: []
first_failure:
  marker: TEST_COLLECTION_PYTHONPATH
  evidence: The first isolated pytest invocation could not import ai_platform because the scratch workspace was not on sys.path; rerunning the same targeted test with PYTHONPATH=. produced one test-expectation failure, which was corrected without changing implementation behavior, and the final run passed 23 tests.
rejected_hypotheses:
  - Reuse or extend the completed execution workflow.
  - Import Torch in the dependency-light canonical digest core.
  - Read existing model artifacts or market data to validate the schema.
  - Create a canonical request while implementing provenance helpers.
  - Treat a determinism classification as proof of deterministic behavior.
  - Use file paths, ZIP timestamps or filesystem metadata in the semantic state digest.
changed_paths:
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl-v2-provenance-schema-v1.json
  - tests/ai_platform/test_rl_v2_provenance_tooling.py
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
validation:
  - command: python -m py_compile ai_platform/provenance/__init__.py ai_platform/provenance/rl_v2.py tests/ai_platform/test_rl_v2_provenance_tooling.py
    result: PASS
    evidence: The isolated workspace compiled all new Python files with exit status 0.
  - command: PYTHONPATH=. pytest -q tests/ai_platform/test_rl_v2_provenance_tooling.py
    result: PASS
    evidence: 23 synthetic tests passed; no market data, trained models or existing artifacts were read.
  - command: python -m json.tool ai_platform/provenance/rl-v2-provenance-schema-v1.json
    result: PASS
    evidence: The schema parsed as valid JSON with exit status 0.
  - command: ruff check and ruff format --check on changed Python files
    result: NOT_RUN
    evidence: Ruff is not installed in the isolated sandbox; exact-head repository CI must provide the result.
  - command: mypy ai_platform/provenance/__init__.py ai_platform/provenance/rl_v2.py
    result: NOT_RUN
    evidence: Mypy is not installed in the isolated sandbox; exact-head repository CI must provide the result.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md --require-checkpoint
    result: NOT_RUN
    evidence: Full repository bytes are unavailable locally because the sandbox cannot resolve github.com; exact-head repository CI or a connected runner must provide the result.
  - command: python tools/agents/resume.py --task docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
    result: NOT_RUN
    evidence: Full repository bytes are unavailable locally because the sandbox cannot resolve github.com; exact-head repository CI or a connected runner must provide the result.
blockers: []
next_action: Open the six-path implementation PR, resolve only exact-head validation or review failures, and merge it only after all required checks pass.
```
