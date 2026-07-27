---
task_id: FTAI-20260726-rl-v2-provenance-tooling-v1
status: ready
branch: docs/rl-v2-provenance-tooling-v1-closeout
base_branch: develop
created: 2026-07-26
updated: 2026-07-27
related_pr: "#408 declaration; #412 implementation; #449 terminal closeout"
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
  - current develop HEAD and open work overlapping RL-v2 provenance, policy state, optimizer state, model artifacts or action observability
  - existing task declarations before any runtime adapter, canonical request or execution work
optional_reads: []
---

# RL-v2 provenance tooling v1

## Goal

Implement only static or inert, dependency-light provenance schemas, canonical JSON serialization, deterministic semantic state digests, self-hashed manifest helpers and fail-closed validators for separately authorized future RL-v2 experiments.

This task creates no model execution path, canonical run request, workflow trigger or market-data capability. It does not import or initialize RL, PPO, Stable-Baselines3, Torch policy code or an environment.

## Implemented contract

The merged package defines:

- a versioned, additional-fields-forbidden provenance manifest;
- integer-only canonical JSON with sorted keys, preserved list order and exactly one trailing LF;
- dependency-light `TensorRecord` framing and semantic SHA-256 over logical name, role, element type, dtype, shape, normalized device, byte order and raw bytes;
- deterministic self-hashing that excludes only `self_hash_sha256`;
- explicit null and `missing_optional_fields` coherence;
- secret-like content rejection;
- fail-closed authorization, OOS, holdout and Phase 6 boundaries;
- synthetic unit tests and technical documentation.

A future runtime adapter is intentionally absent. No runtime tensor, model artifact or market-data file is read by this package.

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
updated_at: 2026-07-27T11:36:00+02:00
head: dc15a94388f33c81608acf566b066c845cac7b0f
branch: docs/rl-v2-provenance-tooling-v1-closeout
pr: "#449"
status: ready
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
  - Declaration PR 408 passed Freqtrade CI 30222399535 and zizmor 30222399566, then merged as 069243be28f373671c4f2b2c0223a35a0cb34337 from exact head 887b7ff18003f6b42a0b933e2e6331b5d0006f61.
  - Implementation PR 412 merged as dc15a94388f33c81608acf566b066c845cac7b0f from exact head acde29d9957eaaf41684f9439619a95f3872e6f5.
  - AI Platform CI 30252856106 passed compile, synthetic tests, Ruff, Ruff format, codespell and JSON validation on the implementation head.
  - Freqtrade CI 30252856272 passed pre-commit, documentation, Python 3.11 through 3.14 tests, coverage, smoke checks, Ruff, mypy, distributions and CI Gate.
  - Zizmor run 30252856021 passed and PR 412 had no open review threads before merge.
  - The core imports only Python standard-library modules and provides no file, network, model or market-data read path.
  - Authorization flags, cache restore, consumed OOS, protected holdout, Phase 6 changes and non-null selected_model fail closed.
  - Targeted local compilation, schema parsing and 23 synthetic tests passed without reading trained models, caches or market data.
derived:
  - A separately declared future adapter may translate authorized runtime tensors into TensorRecord without changing the canonical core.
  - Any runtime execution, canonical request or data access remains a separate governed task and is not implied by this merge.
unknown: []
conflicts: []
first_failure:
  marker: RUFF_FORMAT_AND_MYPY_DIAGNOSTICS_RESOLVED
  evidence: Exact-head CI isolated import ordering, formatter output and a set-versus-frozenset annotation mismatch; each was corrected without changing runtime scope or enabling prohibited behavior.
rejected_hypotheses:
  - Reuse or extend an execution workflow.
  - Import Torch in the dependency-light canonical digest core.
  - Read existing model artifacts, caches or market data to validate the schema.
  - Create a canonical request while implementing provenance helpers.
  - Treat a determinism classification as proof of deterministic behavior.
  - Use file paths, archive timestamps or filesystem metadata in the semantic state digest.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
validation:
  - command: python -m py_compile ai_platform/provenance/__init__.py ai_platform/provenance/rl_v2.py tests/ai_platform/test_rl_v2_provenance_tooling.py
    result: PASS
    evidence: The isolated workspace compiled all new Python files with exit status 0.
  - command: PYTHONPATH=. pytest -q tests/ai_platform/test_rl_v2_provenance_tooling.py
    result: PASS
    evidence: 23 synthetic tests passed with no model, cache or market-data access.
  - command: python -m json.tool ai_platform/provenance/rl-v2-provenance-schema-v1.json
    result: PASS
    evidence: The closed provenance schema parsed as valid JSON.
  - command: AI Platform CI on acde29d9957eaaf41684f9439619a95f3872e6f5
    result: PASS
    evidence: Run 30252856106 completed successfully.
  - command: Freqtrade CI on acde29d9957eaaf41684f9439619a95f3872e6f5
    result: PASS
    evidence: Run 30252856272 completed successfully with CI Gate success.
  - command: zizmor on acde29d9957eaaf41684f9439619a95f3872e6f5
    result: PASS
    evidence: Run 30252856021 completed successfully.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md --require-checkpoint
    result: PASS
    evidence: Repository checkpoint validator accepted the terminal checkpoint.
  - command: python tools/agents/resume.py --task docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
    result: PASS
    evidence: Repository resume generator rendered a valid continuation prompt with the concrete terminal next action.
blockers: []
next_action: Treat this task as closed after the one-file closeout PR merges; create a separately declared governed task before adding any runtime adapter, canonical request, model execution or market-data access.
```
