---
task_id: FTAI-20260720-phase6-provenance-binding
status: implementing
branch: feat/phase6-provenance-binding-v1
base_branch: develop
created: 2026-07-20
updated: 2026-07-20
related_pr: ""
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
updated_at: 2026-07-20T21:10:30Z
head: dd23679d8b920552e11fc64f4548e00a9798974d
branch: feat/phase6-provenance-binding-v1
pr: none
status: implementing
context_routes:
  - ai_platform/model_comparison/result-provenance-v1.json
  - docs/ai_platform/PHASE6_PROVENANCE_BINDING.md
owned_paths:
  - ai_platform/scripts/model_comparison_provenance_binding.py
  - tests/ai_platform/test_model_comparison_provenance_binding.py
  - docs/ai_platform/PHASE6_PROVENANCE_BINDING.md
  - docs/agents/tasks/FTAI-20260720-phase6-provenance-binding.md
proven:
  - develop was verified at 03e2865ba1bfda14ad88578413aa552b045afaaf before branch creation.
  - No open user PR and no provenance-binding branch existed before this task branch was created.
  - The binder consumes existing materialization, run provenance, backtest archive, extraction, and selection-decision files only.
  - Protected final holdout 20260801-20260930 is not an input; frozen thresholds remain entry_prediction_threshold=0.006 and exit_prediction_threshold=-0.009.
derived:
  - Selection-decision binding is enforced by recomputing the deterministic predeclared decision from the exact bound extraction payloads and requiring semantic equality before hashing the supplied decision bytes.
unknown:
  - CI outcome for the implementation branch.
conflicts: []
first_failure:
  marker: local-clone-dns
  evidence: Sandbox git clone could not resolve github.com, so executable validation must use GitHub Actions CI.
rejected_hypotheses:
  - Provenance Binding Implementation v1 already existed on another branch or PR.
changed_paths:
  - ai_platform/scripts/model_comparison_provenance_binding.py
  - tests/ai_platform/test_model_comparison_provenance_binding.py
  - docs/ai_platform/PHASE6_PROVENANCE_BINDING.md
  - docs/agents/tasks/FTAI-20260720-phase6-provenance-binding.md
validation:
  - command: local clone/test
    result: BLOCKED
    evidence: Sandbox DNS could not resolve github.com.
blockers: []
next_action: Open a pull request against develop and use required GitHub Actions checks to validate the implementation, fixing any code or test failures before merge.
```
