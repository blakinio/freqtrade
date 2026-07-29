---
task_id: FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1
status: validating
branch: agent/wickhunter-real-dataset-materialization-operator-v1
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
related_pr: 723
depends_on:
  - FTAI-20260729-wickhunter-real-dataset-materialization-preflight-v1
owned_paths:
  - ai_platform/wickhunter/materialization.py
  - ai_platform/scripts/wickhunter_dataset_materialization.py
  - tests/ai_platform_integration/test_wickhunter_dataset_materialization.py
  - docs/ai_platform/WICKHUNTER_DATASET_MATERIALIZATION_OPERATOR.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-preflight-v1.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
---

# WickHunter real dataset materialization operator v1

## Goal

Implement a deterministic no-network WH-01 operator that validates exact immutable accepted-import, market-context, universe-history and split-geometry inputs, produces a bounded missing-input report, calls the existing dataset builder only after a ready preflight, and independently verifies every output identity.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-07-29T18:20:00+02:00
branch: agent/wickhunter-real-dataset-materialization-operator-v1
validated_code_head: 7190534fd26fc81203795f3a0717900f8fda5845
pr: 723
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-preflight-v1.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
  - docs/ai_platform/WICKHUNTER_REAL_DATASET_MATERIALIZATION_PREFLIGHT.md
owned_paths:
  - ai_platform/wickhunter/materialization.py
  - ai_platform/scripts/wickhunter_dataset_materialization.py
  - tests/ai_platform_integration/test_wickhunter_dataset_materialization.py
  - docs/ai_platform/WICKHUNTER_DATASET_MATERIALIZATION_OPERATOR.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1.md
proven:
  - Preflight PR 718 merged as c6d939f77487676303ec9f5376f55b0097b88f92 and keeps WH-02 blocked.
  - Existing WH-01 build_wickhunter_dataset is atomic, no-overwrite, availability-ordered and emits non-empty hashed partitions or fails closed.
  - Existing accepted-import loader validates manifest, acceptance, event and artifact identities before returning events.
  - Request schema wickhunter-dataset-materialization-request-v1 binds relative paths, exact SHA-256 identities, accepted import selections, build parameters, split geometry and explicit false authority flags.
  - Package-root confinement rejects absolute paths, parent traversal, symlink traversal, duplicate accepted roots and output inside immutable input.
  - Missing files produce a bounded blocked report and no dataset; malformed, tampered, future-data or authority-bearing inputs fail closed.
  - Market rows require all nine WH-01 metrics, canonical snapshot hashes, deterministic decision ordering and decision-time availability.
  - Universe rows require canonical wickhunter-dynamic-universe-v1 snapshot hashes, deterministic ordering and duplicate refusal.
  - Ready materialization invokes the unchanged build_wickhunter_dataset only after accepted-import and input validation.
  - Independent verification covers manifest identity, every partition and row hash, row counts, temporal bounds, accepted source selections, universe history and artifact hashes.
  - Six integration regressions cover successful materialization, missing-input blocking, file tamper, future metrics, authority/path traversal and output partition tamper.
  - Exact code head 7190534fd26fc81203795f3a0717900f8fda5845 passed AI Platform CI 30470991440, Freqtrade CI 30470990920 and zizmor 30470996640.
  - Full Freqtrade validation included pre-commit, documentation, Python 3.11 through 3.14, Python 3.12 coverage, smoke tests, Ruff, format, mypy, distribution build and CI Gate.
derived:
  - The software boundary between exact immutable WH-01 inputs and a verified feature dataset is implemented.
  - This operator does not create the missing production market-context or universe evidence and grants no WH-02, model, trading, execution or live-capital authority.
  - A later operational package can safely run preflight against exact immutable roots and must stop with a bounded blocked report when source evidence is absent.
unknown:
  - Which production paths will supply immutable market-context and universe-history packages.
  - Whether the first accepted interval can produce a useful non-empty dataset under a prospectively frozen production split geometry.
conflicts: []
first_failure:
  gate: initial_exact_head_pre_commit
  cause: One fixture binding was unused and Ruff format required one list literal on a single line.
  resolution: Renamed the unused binding and applied the exact formatter output without changing behavior.
rejected_hypotheses:
  - Add a production request or Synology workflow before the operator is merged.
  - Query live endpoints from the materialization process.
  - Generate synthetic snapshots when inputs are missing.
  - Permit absolute paths, path traversal, symlinks or writable mutation of inputs.
  - Authorize labels, replay, model execution, trading or live capital.
changed_paths:
  - ai_platform/wickhunter/materialization.py
  - ai_platform/scripts/wickhunter_dataset_materialization.py
  - tests/ai_platform_integration/test_wickhunter_dataset_materialization.py
  - docs/ai_platform/WICKHUNTER_DATASET_MATERIALIZATION_OPERATOR.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-real-dataset-materialization-operator-v1.md
validation:
  - command: AI Platform CI 30470991440
    result: PASS
    evidence: 976 tests passed, 71 skipped; compile, Ruff, format, codespell and JSON validation succeeded on code head 7190534fd26fc81203795f3a0717900f8fda5845.
  - command: Freqtrade CI 30470990920
    result: PASS
    evidence: Pre-commit, docs, Python 3.11-3.14, full 3.12 coverage, smoke tests, Ruff, format, mypy, build distributions and CI Gate succeeded.
  - command: GitHub Actions security analysis 30470996640
    result: PASS
    evidence: zizmor completed successfully on the exact code head.
blockers: []
next_action: Revalidate this checkpointed five-file package on the latest develop head, then squash-merge PR 723 only if AI Platform CI, full Freqtrade CI and zizmor are all green on that exact refreshed head.
```
