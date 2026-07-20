---
task_id: FTAI-20260720-phase6-final-result-assembler
status: implementing
branch: feat/phase6-final-result-assembler-v1
base_branch: develop
created: 2026-07-20
updated: 2026-07-20
related_pr: ""
owned_paths:
  - ai_platform/scripts/model_comparison_result_assembler.py
  - tests/ai_platform/test_model_comparison_result_assembler.py
  - docs/ai_platform/PHASE6_FINAL_RESULT_ASSEMBLER.md
  - ai_platform/model_comparison/README.md
  - docs/agents/tasks/FTAI-20260720-phase6-final-result-assembler.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_platform/model_comparison/README.md
  - ai_platform/model_comparison/result-schema-v1.json
  - ai_platform/model_comparison/result-provenance-v1.json
  - docs/ai_platform/PHASE6_FINAL_RESULT_ASSEMBLER.md
search_first:
  - ai_platform/scripts/model_comparison_result_provenance.py
  - ai_platform/scripts/model_comparison_provenance_binding.py
  - ai_platform/scripts/model_comparison_selection_policy.py
optional_reads:
  - ai_platform/model_comparison/result-provenance-schema-v1.json
  - ai_platform/model_comparison/selection-decision-schema-v1.json
---

# Phase 6 final comparison result assembler

## Goal

Assemble the existing Phase 6 comparison result schema deterministically from successfully bound provenance evidence and existing strict-OOS extraction/selection artifacts, without executing models or backtests and without accessing the protected final holdout.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-20T21:40:00Z
head: 4673d8a5b7d170ad7cd6514afe80e74de3ab1173
branch: feat/phase6-final-result-assembler-v1
pr: none
status: implementing
context_routes:
  - ai_platform/model_comparison/result-schema-v1.json
  - ai_platform/model_comparison/result-provenance-v1.json
  - docs/ai_platform/PHASE6_FINAL_RESULT_ASSEMBLER.md
owned_paths:
  - ai_platform/scripts/model_comparison_result_assembler.py
  - tests/ai_platform/test_model_comparison_result_assembler.py
  - docs/ai_platform/PHASE6_FINAL_RESULT_ASSEMBLER.md
  - ai_platform/model_comparison/README.md
  - docs/agents/tasks/FTAI-20260720-phase6-final-result-assembler.md
proven:
  - develop was verified at 0a798cba4628b5fbe9d15cf26e5aaa514daf2fe4 before branch creation.
  - No open user PR existed before this task branch was created.
  - Provenance Binding Implementation v1 was already merged and its durable checkpoint closed before this task started.
  - The assembler consumes bound result-provenance evidence, exactly one strict-OOS extraction per canonical model, and the bound selection-decision artifact only.
  - Result git_commit and plan_sha256 are populated only through the existing canonical result_binding_values provenance mapping.
  - Supplied extraction and selection-decision exact-byte hashes are checked against bound provenance before their contents are used.
  - Selection is recomputed deterministically from the two bound extraction payloads and must equal the supplied bound selection decision.
  - Protected final holdout 20260801-20260930 is not an input; frozen thresholds remain entry_prediction_threshold=0.006 and exit_prediction_threshold=-0.009.
derived:
  - Per-model artifact_paths can safely record only the extraction path actually consumed by the assembler; earlier runtime artifacts remain represented by hashes in bound provenance rather than invented paths.
unknown:
  - CI outcome for the implementation branch.
conflicts: []
first_failure:
  marker: local-clone-dns
  evidence: Sandbox git clone could not resolve github.com, so executable validation must use GitHub Actions CI.
rejected_hypotheses:
  - A final deterministic comparison-result assembler already existed on develop or an open PR.
changed_paths:
  - ai_platform/scripts/model_comparison_result_assembler.py
  - tests/ai_platform/test_model_comparison_result_assembler.py
  - docs/ai_platform/PHASE6_FINAL_RESULT_ASSEMBLER.md
  - docs/agents/tasks/FTAI-20260720-phase6-final-result-assembler.md
validation:
  - command: local clone/test
    result: BLOCKED
    evidence: Sandbox DNS could not resolve github.com; executable validation will use GitHub Actions.
blockers: []
next_action: Update the model-comparison README to reflect merged provenance binding and the final result assembler, then open a pull request against develop and use required GitHub Actions checks to validate the implementation, fixing any code or test failures before merge.
```
