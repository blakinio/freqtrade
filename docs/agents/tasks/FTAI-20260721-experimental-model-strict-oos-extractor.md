---
task_id: FTAI-20260721-experimental-model-strict-oos-extractor
status: implementing
branch: feat/experimental-model-strict-oos-extractor-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
owned_paths:
  - ai_platform/experimental_model_research/oos-extraction-contract-v1.json
  - ai_platform/experimental_model_research/oos-extraction-schema-v1.json
  - ai_platform/scripts/experimental_model_oos_result_extractor.py
  - tests/ai_platform/test_experimental_model_oos_result_extractor.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-strict-oos-extractor.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/experimental_model_research/oos-extraction-contract-v1.json
search_first:
  - ai_platform/scripts/experimental_model_oos_result_extractor.py
  - ai_platform/scripts/model_comparison_oos_result_extractor.py
  - ai_platform/scripts/protected_final_holdout.py
---

# Experimental model strict historical-OOS extractor

## Goal

Add extraction-only evidence plumbing for the isolated PyTorch and RL research tracks so future already-produced backtest archives can be scored only on fully contained trades in the consumed historical OOS window `20260501-20260630`, without changing Phase 6, executing research, retuning the frozen candidate, or touching the protected final holdout.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T05:30:00Z
head: 6c23f361ae93bc5a9c6b792331865ebd20f7e459
branch: feat/experimental-model-strict-oos-extractor-v1
pr: none
status: implementing
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - ai_platform/experimental_model_research/oos-extraction-contract-v1.json
  - ai_platform/scripts/experimental_model_oos_result_extractor.py
owned_paths:
  - ai_platform/experimental_model_research/oos-extraction-contract-v1.json
  - ai_platform/experimental_model_research/oos-extraction-schema-v1.json
  - ai_platform/scripts/experimental_model_oos_result_extractor.py
  - tests/ai_platform/test_experimental_model_oos_result_extractor.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-strict-oos-extractor.md
proven:
  - develop was verified at f97365b1f5de3dc3cb32ce410a674534be7b9319 before branch creation and no open pull requests were present.
  - The prior experimental-model foundation checkpoint requires a strict fully-contained May-June OOS extractor before any PyTorch or RL performance conclusion.
  - The new extractor accepts only the two canonical experimental manifests and reuses no Phase 6 comparison membership or selection policy.
  - The scoring contract requires open_date at or after 2026-05-01T00:00:00Z and close_date before 2026-07-01T00:00:00Z.
  - The protected final holdout remains 20260801-20260930 and manifest validation occurs before archive scoring.
  - Extraction is artifact-only and does not download data, train, backtest, retune, promote, or claim profitability.
derived:
  - Existing strict trade parsing and partition helpers can be reused without modifying Phase 6 files or semantics.
  - Separate experimental contract and schema keep PyTorch/RL evidence distinguishable from Phase 6 OOS extractions.
unknown:
  - CI has not yet validated the new extractor, schema, tests, and documentation.
  - No real PyTorch or RL backtest archive has been produced or scored.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses:
  - Generic March-June run-summary metrics are sufficient historical-OOS evidence.
  - Experimental PyTorch or RL extraction should be emitted as a Phase 6 comparison artifact.
changed_paths:
  - ai_platform/experimental_model_research/oos-extraction-contract-v1.json
  - ai_platform/experimental_model_research/oos-extraction-schema-v1.json
  - ai_platform/scripts/experimental_model_oos_result_extractor.py
  - tests/ai_platform/test_experimental_model_oos_result_extractor.py
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-strict-oos-extractor.md
validation:
  - command: GitHub Actions CI
    result: NOT_RUN
    evidence: Implementation pull request has not been opened yet.
blockers: []
next_action: Open the implementation pull request against develop and use required CI to validate compile, targeted tests, Ruff, formatting, codespell, schema syntax, and repository checks before merge.
```
