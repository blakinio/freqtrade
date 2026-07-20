---
task_id: FTAI-20260720-phase6-materialization-hash-parity
status: done
branch: fix/phase6-materialization-exact-byte-hashes
base_branch: develop
created: 2026-07-20
updated: 2026-07-20
related_pr: "#57"
owned_paths:
  - ai_platform/scripts/model_comparison_harness.py
  - tests/ai_platform/test_model_comparison_harness.py
  - docs/ai_platform/PHASE6_MATERIALIZATION_HASH_PARITY.md
  - docs/agents/tasks/FTAI-20260720-phase6-materialization-hash-parity.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_platform/scripts/model_comparison_harness.py
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/model_comparison_result_provenance.py
  - docs/ai_platform/PHASE6_MATERIALIZATION_HASH_PARITY.md
search_first:
  - tests/ai_platform/test_model_comparison_harness.py
  - ai_platform/model_comparison/result-provenance-v1.json
optional_reads:
  - ai_platform/scripts/model_comparison_provenance_binding.py
---

# Phase 6 materialization exact-byte hash parity

## Goal

Make materialized config and manifest SHA-256 values match the exact bytes written by the Phase 6 harness and later hashed by `run_experiment`, before any real historical comparison execution occurs.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-20T22:40:01Z
head: 9b4098ea355823df2a398ef49d0e111981639cda
branch: develop
pr: "#57 merged"
status: done
context_routes:
  - ai_platform/scripts/model_comparison_harness.py
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/model_comparison_result_provenance.py
  - docs/ai_platform/PHASE6_MATERIALIZATION_HASH_PARITY.md
owned_paths:
  - ai_platform/scripts/model_comparison_harness.py
  - tests/ai_platform/test_model_comparison_harness.py
  - docs/ai_platform/PHASE6_MATERIALIZATION_HASH_PARITY.md
  - docs/agents/tasks/FTAI-20260720-phase6-materialization-hash-parity.md
proven:
  - Phase 6 materialization exact-byte hash parity was squash-merged by PR #57 into develop as 9b4098ea355823df2a398ef49d0e111981639cda.
  - The previous harness calculated materialized config and manifest hashes from compact canonical JSON while writing indented sorted JSON with a trailing newline.
  - run_experiment hashes exact on-disk config and manifest bytes for run provenance.
  - Result provenance requires runtime manifest/config hashes to equal the corresponding canonical materialization hashes.
  - The merged fix leaves compact canonical hashing in place for model identity derivation and uses one deterministic exact-byte serializer for both written materialized files and their recorded SHA-256 values.
  - The regression test writes each generated config and manifest through the harness serializer, hashes the resulting file bytes independently, and requires equality with materialization config_sha256 and manifest_sha256.
  - No real Phase 6 historical comparison artifacts or completed comparison evidence existed before this correction.
  - Original PR #54 was automatically closed when its head was reset to incorporate concurrently merged non-overlapping PR #52 and checkpoint PR #56; the same scoped changes were reapplied on current develop and merged through replacement PR #57.
  - Replacement PR #57 head 4365179158501247c06d7281363a9f1f6f164086 passed AI Platform CI #236, zizmor #226, and Freqtrade CI #247; Pre-commit Types #182 was skipped rather than failed.
  - Protected final holdout 20260801-20260930 was not accessed; frozen thresholds remain entry_prediction_threshold=0.006 and exit_prediction_threshold=-0.009.
derived:
  - Phase 6 can now build materialized config and manifest hashes that are compatible with the exact-byte provenance emitted by run_experiment.
  - The next bounded dependency is one-shot historical comparison execution workflow infrastructure, not the actual comparison trigger itself.
unknown: []
conflicts: []
first_failure:
  marker: pre-execution-provenance-hash-mismatch
  evidence: Static lifecycle review showed harness materialization digests and run_experiment provenance digests used different byte representations for the same JSON files before PR #57.
rejected_hypotheses:
  - The previous materialization hashes already represented exact written config and manifest file bytes.
  - The actual historical LightGBM-versus-XGBoost comparison could safely run before correcting materialization digest semantics.
  - Concurrent PR #52 or checkpoint PR #56 modified any path owned by this hash-parity fix.
changed_paths:
  - ai_platform/scripts/model_comparison_harness.py
  - tests/ai_platform/test_model_comparison_harness.py
  - docs/ai_platform/PHASE6_MATERIALIZATION_HASH_PARITY.md
  - docs/agents/tasks/FTAI-20260720-phase6-materialization-hash-parity.md
validation:
  - command: GitHub Actions AI Platform CI #236
    result: PASS
    evidence: replacement PR #57 completed AI Platform CI successfully on current develop base.
  - command: GitHub Actions Security Analysis with zizmor #226
    result: PASS
    evidence: workflow completed with conclusion success.
  - command: GitHub Actions Freqtrade CI #247
    result: PASS
    evidence: workflow completed with conclusion success, including Ubuntu Python 3.12 coverage.
  - command: Pre-commit Types update #182
    result: SKIPPED
    evidence: workflow was skipped, not failed.
  - command: local clone/test
    result: BLOCKED
    evidence: Sandbox has no repository clone and cannot resolve github.com; executable validation used GitHub Actions.
blockers: []
next_action: Create the next bounded Phase 6 task for one-shot historical LightGBM-versus-XGBoost comparison execution workflow infrastructure. The workflow must validate an exact run request and frozen contract before market-data access, materialize only historical inputs ending 20260630, execute both model backtests at the same checked-out commit, and chain strict-OOS extraction, deterministic selection, provenance binding, and final result assembly. The actual comparison trigger must be a separate run-request PR after the workflow infrastructure is merged. It must not access 20260801-20260930, retune thresholds or model parameters, promote a model, authorize live trading, or make a profitability claim.
```
