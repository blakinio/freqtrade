---
task_id: FTAI-20260720-phase6-result-provenance
status: ready
branch: develop
base_branch: develop
created: 2026-07-20
updated: 2026-07-20
related_pr: "#45"
owned_paths:
  - ai_platform/model_comparison/README.md
  - ai_platform/model_comparison/result-provenance-schema-v1.json
  - ai_platform/model_comparison/result-provenance-v1.json
  - ai_platform/scripts/model_comparison_result_provenance.py
  - tests/ai_platform/test_model_comparison_result_provenance.py
required_reads:
  - ai_platform/model_comparison/README.md
  - ai_platform/model_comparison/result-provenance-v1.json
search_first:
  - ai_platform/scripts/model_comparison_result_provenance.py
  - ai_platform/scripts/model_comparison_oos_result_extractor.py
  - ai_platform/scripts/model_comparison_selection_policy.py
optional_reads:
  - ai_platform/model_comparison/result-schema-v1.json
---

# Phase 6 comparison result provenance contract

## Goal

Pin unambiguous provenance semantics for the future Phase 6 LightGBM-versus-XGBoost result before runtime artifact binding or final assembly.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-20T20:18:02Z
head: efe0e9d3a6866b01eaf0d5710e8bf2e24dc0f25d
branch: develop
pr: "#45 merged"
status: ready
context_routes:
  - ai_platform/model_comparison/README.md
  - ai_platform/model_comparison/result-provenance-v1.json
owned_paths:
  - ai_platform/model_comparison/README.md
  - ai_platform/model_comparison/result-provenance-schema-v1.json
  - ai_platform/model_comparison/result-provenance-v1.json
  - ai_platform/scripts/model_comparison_result_provenance.py
  - tests/ai_platform/test_model_comparison_result_provenance.py
proven:
  - PR #45 squash-merged to develop at efe0e9d3a6866b01eaf0d5710e8bf2e24dc0f25d.
  - result.git_commit is the shared model backtest execution commit from run provenance.
  - result.plan_sha256 is SHA-256 of exact canonical materialization.json bytes.
  - Semantic validation enforces canonical model identities, materialized manifest/config hashes, one shared execution commit, and one shared strategy hash.
  - Protected final holdout 20260801-20260930 was not used; retuning, promotion, live trading, and profitability claims remain forbidden.
  - Frozen thresholds remain entry_prediction_threshold=0.006 and exit_prediction_threshold=-0.009.
derived:
  - The next bounded dependency is Provenance Binding Implementation v1 consuming existing artifact files only.
unknown: []
conflicts: []
first_failure:
  marker: pr45-lint-format-mypy
  evidence: Earlier PR heads failed Ruff, Ruff format, then Mypy; final head 57f1693af00eb1725844fafe1f96988845f2ba6c passed all required gates.
rejected_hypotheses:
  - A feat/phase6-provenance-binding branch or PR already existed; live GitHub showed no such branch or PR.
changed_paths:
  - ai_platform/model_comparison/README.md
  - ai_platform/model_comparison/result-provenance-schema-v1.json
  - ai_platform/model_comparison/result-provenance-v1.json
  - ai_platform/scripts/model_comparison_result_provenance.py
  - tests/ai_platform/test_model_comparison_result_provenance.py
validation:
  - command: AI Platform CI #206
    result: PASS
    evidence: success on final PR #45 head 57f1693af00eb1725844fafe1f96988845f2ba6c
  - command: GitHub Actions Security Analysis with zizmor #188
    result: PASS
    evidence: success on final PR #45 head 57f1693af00eb1725844fafe1f96988845f2ba6c
  - command: Freqtrade CI #209
    result: PASS
    evidence: success on final PR #45 head 57f1693af00eb1725844fafe1f96988845f2ba6c
  - command: compare efe0e9d3a6866b01eaf0d5710e8bf2e24dc0f25d...develop
    result: PASS
    evidence: identical; ahead_by=0; behind_by=0
blockers: []
next_action: Create a dedicated branch from develop and implement Provenance Binding Implementation v1 that verifies exact-byte hashes of actual materialization plan, run provenance, backtest ZIP, extraction, and selection-decision artifacts without executing models or using the protected final holdout.
```
