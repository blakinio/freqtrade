---
task_id: FTAI-20260726-rl-v2-provenance-tooling-v1
status: implementing
branch: docs/rl-v2-provenance-tooling-v1
base_branch: develop
created: 2026-07-26
updated: 2026-07-27
related_pr: null
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

This task creates no model execution path, canonical run request, workflow trigger or market-data capability. It must not import or initialize RL, PPO, Stable-Baselines3, Torch policy code or an environment.

## Declared implementation boundary

The implementation package is limited to the six owned paths in frontmatter. The core must use the Python standard library, have no import-time side effects, accept only caller-supplied synthetic structures and write nothing unless an explicit path is passed.

The contract will cover execution environment, runtime dependencies, code/configuration identity, determinism declaration, seed/RNG provenance, policy state, optimizer state, serialized model artifacts, dataset manifest identity, diagnostic artifacts, final evidence manifest, explicit missing optional fields, classification, authorization boundaries and deterministic self-hashing.

Canonical JSON will use UTF-8, lexicographically sorted object keys, preserved list order, JSON integers only, stable booleans and null, no floats or non-finite values, no locale dependence and exactly one trailing LF byte.

Semantic tensor-state digests will frame sorted logical names, role, element type, dtype, shape, normalized device, byte order and raw bytes. They will reject duplicate logical identities and byte-length inconsistencies and will not depend on dictionary insertion order, file paths, timestamps, archive ordering or filesystem metadata.

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
updated_at: 2026-07-27T00:03:00+02:00
head: PENDING
branch: docs/rl-v2-provenance-tooling-v1
pr: not_opened
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-hardening-contract.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-seed-effectiveness-determinism-audit.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-action-observability-execution.md
  - docs/ai_platform/RL_V2_SEED_EFFECTIVENESS_DETERMINISM_AUDIT.md
  - ai_platform/experimental_model_research/rl-v2-seed-effectiveness-determinism-audit-v1.json
owned_paths:
  - ai_platform/provenance/__init__.py
  - ai_platform/provenance/rl_v2.py
  - ai_platform/provenance/rl-v2-provenance-schema-v1.json
  - tests/ai_platform/test_rl_v2_provenance_tooling.py
  - docs/ai_platform/RL_V2_PROVENANCE_TOOLING.md
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
proven:
  - Current develop is 898361072489fb47a6f2a9eff639b75c2d262b7d, one path-disjoint task-closeout commit ahead of the expected provenance-contract head.
  - The merged provenance hardening contract explicitly requires a separate inert tooling task before any future RL-v2 execution declaration.
  - Open PRs 394, 400, 401, 402 and 406 do not own any declared provenance-tooling path.
  - Repository and branch searches found no active RL-v2 provenance tooling task, PR or branch with equivalent ownership.
  - The canonical RL-v2 action-observability request remains absent from develop according to the terminal hardening contract.
  - This declaration changes exactly one task-record path and authorizes no implementation or execution behavior.
derived:
  - A standard-library core can provide deterministic semantic state digests without importing Torch.
  - Exact schema keys and explicit null slots can make missing optional provenance fail-closed and auditable.
unknown:
  - Exact declaration PR number, exact-head CI run identifiers and declaration merge SHA until GitHub creates and completes them.
  - Implementation exact-head CI results until the separate implementation PR exists.
conflicts: []
first_failure:
  marker: LOCAL_CLONE_DNS_UNAVAILABLE
  evidence: The sandbox could not resolve github.com, so full local repository validation is unavailable; GitHub connector state and exact-head CI remain usable.
rejected_hypotheses:
  - Reuse or extend the completed execution workflow.
  - Import Torch in the dependency-light canonical digest core.
  - Read existing model artifacts or market data to validate the schema.
  - Create a canonical request while implementing provenance helpers.
  - Treat a determinism classification as proof of deterministic behavior.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
validation:
  - command: live-state develop, open-PR, branch and equivalent-scope preflight
    result: PASS
    evidence: Current develop and all open user PRs were inspected; searches found no overlapping RL-v2 provenance ownership.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md --require-checkpoint
    result: NOT_RUN
    evidence: The sandbox cannot clone or fetch repository bytes because github.com DNS resolution is unavailable.
  - command: python tools/agents/resume.py --task docs/agents/tasks/FTAI-20260726-rl-v2-provenance-tooling-v1.md
    result: NOT_RUN
    evidence: The sandbox cannot clone or fetch repository bytes because github.com DNS resolution is unavailable.
blockers: []
next_action: Merge the declaration-only PR after exact-head CI and review gates pass, then create a fresh implementation branch from current develop containing only the six declared owned paths.
```
