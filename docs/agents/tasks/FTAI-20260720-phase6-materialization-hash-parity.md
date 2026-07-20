---
task_id: FTAI-20260720-phase6-materialization-hash-parity
status: implementing
branch: fix/phase6-materialization-exact-byte-hashes
base_branch: develop
created: 2026-07-20
updated: 2026-07-20
related_pr: "#54"
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
updated_at: 2026-07-20T22:30:00Z
head: d424ff0bde3372c0dff6ef55db0739907eaef6a2
branch: fix/phase6-materialization-exact-byte-hashes
pr: "#54 open"
status: implementing
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
  - The previous harness calculated materialized config and manifest hashes from compact canonical JSON while writing indented sorted JSON with a trailing newline.
  - run_experiment hashes exact on-disk config and manifest bytes for run provenance.
  - Result provenance requires runtime manifest/config hashes to equal the corresponding canonical materialization hashes.
  - Therefore a real comparison executed before this fix would fail provenance binding despite semantically identical JSON.
  - The fix leaves compact canonical hashing in place for model identity derivation and changes only materialized file digests to the deterministic exact bytes actually written.
  - No real Phase 6 historical comparison artifacts or completed comparison evidence existed on develop before this correction.
  - The first PR #54 head 864286714e29ca14b5905397e34cc7c5fce9d59c passed AI Platform CI #222, zizmor #210, and Freqtrade CI #231.
  - While those checks ran, develop advanced through PR #52 and checkpoint PR #56 to 9d60cb6391d881d4f534d6dd051d2a93c63a88b3; their paths are isolated PyTorch/RL research foundation work and do not overlap this task.
  - PR #54 became non-mergeable on its stale base, so its branch was force-updated to current develop and the same four scoped changes were reapplied for fresh validation.
  - Protected final holdout 20260801-20260930 is not accessed; frozen thresholds remain entry_prediction_threshold=0.006 and exit_prediction_threshold=-0.009.
derived:
  - The canonical materialization plan SHA-256 and per-model config/manifest SHA-256 values will change after this correction, which is necessary before first real execution and does not invalidate any real Phase 6 result because none exists yet.
unknown:
  - CI outcome for the rebased/reapplied PR #54 head.
conflicts: []
first_failure:
  marker: pre-execution-provenance-hash-mismatch
  evidence: Static lifecycle review showed harness materialization digests and run_experiment provenance digests used different byte representations for the same JSON files.
rejected_hypotheses:
  - The existing materialization hashes already represented exact written config and manifest file bytes.
  - The actual historical LightGBM-versus-XGBoost comparison could safely run before correcting materialization digest semantics.
  - PR #52 or #56 modified any path owned by this hash-parity fix.
changed_paths:
  - ai_platform/scripts/model_comparison_harness.py
  - tests/ai_platform/test_model_comparison_harness.py
  - docs/ai_platform/PHASE6_MATERIALIZATION_HASH_PARITY.md
  - docs/agents/tasks/FTAI-20260720-phase6-materialization-hash-parity.md
validation:
  - command: GitHub Actions AI Platform CI #222 on pre-update head
    result: PASS
    evidence: AI Platform CI completed successfully before the base advanced.
  - command: GitHub Actions Security Analysis with zizmor #210 on pre-update head
    result: PASS
    evidence: workflow completed with conclusion success.
  - command: GitHub Actions Freqtrade CI #231 on pre-update head
    result: PASS
    evidence: workflow completed with conclusion success, including Ubuntu Python 3.12 coverage.
  - command: local clone/test
    result: BLOCKED
    evidence: Sandbox has no repository clone and cannot resolve github.com; executable validation uses GitHub Actions.
blockers: []
next_action: Validate the reapplied PR #54 head against current develop with required GitHub Actions checks. Fix any concrete CI failure before merge. After merge, close this checkpoint and only then continue toward a separate Phase 6 one-shot historical comparison execution workflow.
```
