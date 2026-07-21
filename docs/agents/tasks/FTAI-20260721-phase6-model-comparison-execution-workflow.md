---
task_id: FTAI-20260721-phase6-model-comparison-execution-workflow
status: done
branch: feat/phase6-model-comparison-execution-workflow-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#72"
owned_paths:
  - .github/workflows/ai-platform-phase6-model-comparison.yml
  - ai_platform/scripts/model_comparison_run_request.py
  - tests/ai_platform/test_model_comparison_run_request.py
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-execution-workflow.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - ai_platform/model_comparison/lightgbm-vs-xgboost-v1.json
  - ai_platform/scripts/model_comparison_harness.py
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/model_comparison_oos_result_extractor.py
  - ai_platform/scripts/model_comparison_selection_policy.py
  - ai_platform/scripts/model_comparison_provenance_binding.py
  - ai_platform/scripts/model_comparison_result_assembler.py
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
search_first:
  - .github/workflows/ai-platform-phase5-tuning.yml
  - ai_platform/scripts/model_comparison_run_request.py
  - tests/ai_platform/test_model_comparison_run_request.py
optional_reads:
  - docs/ai_platform/PHASE6_MATERIALIZATION_HASH_PARITY.md
  - docs/ai_platform/PHASE6_FINAL_RESULT_ASSEMBLER.md
---

# Phase 6 one-shot historical model comparison execution workflow

## Goal

Add fail-closed GitHub Actions infrastructure that can execute the already-frozen Phase 6 LightGBM-versus-XGBoost historical comparison only after a separate pull request adds one exact canonical run-request file. Keep workflow installation, actual execution trigger, durable evidence persistence, and any later promotion decision as separate work packages.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T10:07:00Z
head: a62f6ad02c68c006e660358ae304debaaf403419
branch: develop
pr: "#72 merged"
status: ready
context_routes:
  - .github/workflows/ai-platform-phase6-model-comparison.yml
  - ai_platform/scripts/model_comparison_run_request.py
  - tests/ai_platform/test_model_comparison_run_request.py
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
owned_paths:
  - .github/workflows/ai-platform-phase6-model-comparison.yml
  - ai_platform/scripts/model_comparison_run_request.py
  - tests/ai_platform/test_model_comparison_run_request.py
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-execution-workflow.md
proven:
  - PR #72 was squash-merged into develop as a62f6ad02c68c006e660358ae304debaaf403419 after all required validation gates completed successfully and GitHub reported the PR mergeable.
  - Final PR #72 head ec0a36ed71659305780e565db330514e8712bb7d passed AI Platform CI run 29820124167 (#292), GitHub Actions Security Analysis with zizmor run 29820124069 (#295), and Freqtrade CI run 29820124083 (#316); Pre-commit Types update run 29820124144 (#238) was skipped rather than failed.
  - The final AI Platform CI run passed compile validation, the AI Platform test suite, Ruff lint, Ruff format, codespell, and tracked JSON validation.
  - The final Freqtrade CI run passed CI scope classification, pre-commit checks, documentation build, and the required repository test matrix.
  - The workflow infrastructure contains no canonical run-request file and did not trigger the historical LightGBM-versus-XGBoost comparison while being installed or validated.
  - The trigger workflow is restricted to same-repository pull requests targeting develop and validates that the trigger PR adds exactly ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json.
  - Canonical request validation pins the current Phase 6 contract hash, historical windows, protected final holdout 20260801-20260930, frozen thresholds 0.006/-0.009, and all retuning/model-parameter/feature/promotion/live/profitability authorization flags to false.
  - Materialization validation occurs before market-data access and requires historical data to end at 20260630.
  - Both frozen model runs execute from the same exact trigger-PR head SHA before strict-OOS extraction, deterministic selection, provenance binding, and final result assembly.
  - Successful and failed workflow evidence are uploaded separately; successful historical evidence is not automatically a promotion, live-trading authorization, or profitability claim.
  - No historical comparison run, protected-final-holdout access, retuning, model promotion, live trading, or live-capital change was performed by this infrastructure work package.
derived:
  - Phase 6 now has merged one-shot execution infrastructure that can accept only a separate minimal canonical run-request PR without allowing contract, workflow, strategy, model, feature, or selection-policy changes in the same trigger PR.
  - The next bounded Phase 6 action can be the separate canonical run-request trigger PR; its workflow result must be treated as historical comparison evidence only and persisted durably through a later evidence work package if successful.
unknown:
  - The actual historical LightGBM-versus-XGBoost runtime has not yet been exercised through the merged workflow.
  - No runtime comparison result, selection decision, or successful execution evidence artifact exists from this infrastructure task itself.
conflicts: []
first_failure:
  marker: mutable-canonical-request-state
  evidence: The first AI Platform CI run failed targeted tests because canonical_model_comparison_run_request returned references to mutable nested EXPECTED_FROZEN_PARAMETERS and EXPECTED_AUTHORIZATION dictionaries; one negative test mutated shared state and contaminated later canonical expectations. The fix returns independent dictionary copies.
rejected_hypotheses:
  - The workflow infrastructure PR should also contain the canonical run-request trigger.
  - A trigger PR may modify the workflow, contract, model configuration, strategy, feature set, selection policy, or any additional file while requesting execution.
  - Shared mutable canonical request dictionaries are safe when negative tests intentionally mutate nested request values.
  - Ruff formatting generated with the default 88-character line length is equivalent to this repository's configured 100-character Ruff format; final formatting was regenerated against the repository configuration before CI passed.
  - Historical comparison evidence can authorize final-holdout access, model promotion, live trading, or a profitability claim.
changed_paths:
  - .github/workflows/ai-platform-phase6-model-comparison.yml
  - ai_platform/scripts/model_comparison_run_request.py
  - tests/ai_platform/test_model_comparison_run_request.py
  - docs/ai_platform/PHASE6_MODEL_COMPARISON_EXECUTION.md
  - docs/agents/tasks/FTAI-20260721-phase6-model-comparison-execution-workflow.md
validation:
  - command: GitHub Actions AI Platform CI run 29820124167 (#292)
    result: PASS
    evidence: Final PR #72 head passed compile, targeted tests, Ruff, Ruff format, codespell, and JSON validation.
  - command: GitHub Actions Security Analysis with zizmor run 29820124069 (#295)
    result: PASS
    evidence: Final PR #72 head completed security workflow analysis successfully.
  - command: GitHub Actions Freqtrade CI run 29820124083 (#316)
    result: PASS
    evidence: Final PR #72 head completed repository CI successfully.
  - command: Pre-commit Types update run 29820124144 (#238)
    result: SKIPPED
    evidence: Workflow was skipped, not failed.
  - command: local clone/test
    result: BLOCKED
    evidence: Sandbox had no repository clone; executable validation used GitHub Actions. Local Ruff 0.15.21 was used only to reproduce repository formatting semantics before final CI validation.
blockers: []
next_action: Create a separate bounded Phase 6 run-request trigger task and pull request that adds exactly ai_platform/model_comparison/run-requests/lightgbm-vs-xgboost-v1.json using the canonical payload printed by python -m ai_platform.scripts.model_comparison_run_request --print-canonical. Do not modify any other file in that trigger PR. Require the merged workflow to validate the exact request and frozen contract before historical market-data access, execute both frozen models, and produce bound historical comparison evidence without accessing 20260801-20260930, retuning, promotion, live trading, or profitability claims.
```
