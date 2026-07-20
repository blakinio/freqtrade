---
task_id: FTAI-20260720-phase6-provenance-binding
status: done
branch: feat/phase6-provenance-binding-v1
base_branch: develop
created: 2026-07-20
updated: 2026-07-20
related_pr: "#49"
owned_paths:
  - ai_platform/scripts/model_comparison_provenance_binding.py
  - tests/ai_platform/test_model_comparison_provenance_binding.py
  - docs/ai_platform/PHASE6_PROVENANCE_BINDING.md
  - docs/agents/tasks/FTAI-20260720-phase6-provenance-binding.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_platform/model_comparison/README.md
  - ai_platform/model_comparison/result-provenance-v1.json
  - docs/ai_platform/PHASE6_PROVENANCE_BINDING.md
search_first:
  - ai_platform/scripts/model_comparison_result_provenance.py
  - ai_platform/scripts/model_comparison_selection_policy.py
  - ai_platform/scripts/model_comparison_oos_result_extractor.py
optional_reads:
  - ai_platform/model_comparison/result-provenance-schema-v1.json
  - ai_platform/model_comparison/selection-decision-schema-v1.json
---

# Phase 6 provenance binding implementation

## Goal

Bind actual existing Phase 6 comparison artifact files by exact-byte SHA-256 and semantic identity checks without executing models, backtests, retuning, or protected-final-holdout access.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-20T21:32:21Z
head: 4fdea2e1d0a3ab5f0b154fe5c46dc64837a2f0a7
branch: develop
pr: "#49 merged"
status: done
context_routes:
  - ai_platform/model_comparison/result-provenance-v1.json
  - docs/ai_platform/PHASE6_PROVENANCE_BINDING.md
owned_paths:
  - ai_platform/scripts/model_comparison_provenance_binding.py
  - tests/ai_platform/test_model_comparison_provenance_binding.py
  - docs/ai_platform/PHASE6_PROVENANCE_BINDING.md
  - docs/agents/tasks/FTAI-20260720-phase6-provenance-binding.md
proven:
  - Provenance Binding Implementation v1 was squash-merged by PR #49 into develop as 4fdea2e1d0a3ab5f0b154fe5c46dc64837a2f0a7.
  - The binder consumes existing materialization, run provenance, backtest archive, extraction, and selection-decision files only.
  - Exact-byte SHA-256 bindings are verified for materialization, run provenance, backtest archives, OOS extractions, and selection decision before existing result-provenance semantic validation.
  - The supplied selection decision must equal the deterministic decision recomputed from the two bound OOS extraction payloads under the tracked predeclared policy.
  - Protected final holdout 20260801-20260930 is not an input; frozen thresholds remain entry_prediction_threshold=0.006 and exit_prediction_threshold=-0.009.
  - AI Platform CI run 29779531783 (#209), zizmor run 29779531843 (#193), and Freqtrade CI run 29779531784 (#214) completed successfully on PR head 369442a5cab919b909fccf54ffcdc9f1aea68b31.
derived:
  - The next missing dependency is deterministic final comparison-result assembly that consumes successfully bound provenance evidence rather than executing or re-evaluating models.
unknown: []
conflicts: []
first_failure:
  marker: ai-platform-ci-208-ruff
  evidence: Initial PR head passed compilation and tests but failed Ruff; a formatting-only line split was applied and AI Platform CI #209 then passed all steps.
rejected_hypotheses:
  - Provenance Binding Implementation v1 already existed on another branch or PR.
changed_paths:
  - ai_platform/scripts/model_comparison_provenance_binding.py
  - tests/ai_platform/test_model_comparison_provenance_binding.py
  - docs/ai_platform/PHASE6_PROVENANCE_BINDING.md
  - docs/agents/tasks/FTAI-20260720-phase6-provenance-binding.md
validation:
  - command: GitHub Actions AI Platform CI #209
    result: PASS
    evidence: compile, AI platform tests, Ruff, Ruff format, Codespell, and JSON validation all succeeded.
  - command: GitHub Actions Security Analysis with zizmor #193
    result: PASS
    evidence: workflow completed with conclusion success.
  - command: GitHub Actions Freqtrade CI #214
    result: PASS
    evidence: workflow completed with conclusion success.
  - command: local clone/test
    result: BLOCKED
    evidence: Sandbox DNS could not resolve github.com; executable validation used GitHub Actions instead.
blockers: []
next_action: Create the next bounded Phase 6 task and implement the smallest deterministic final comparison-result assembler that consumes only successfully bound provenance evidence and existing extraction/selection artifacts, without executing models or backtests and without accessing the protected final holdout.
```
