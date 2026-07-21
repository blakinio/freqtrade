---
task_id: FTAI-20260721-experimental-model-strict-oos-extractor
status: ready
branch: feat/experimental-model-strict-oos-extractor-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "59"
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
updated_at: 2026-07-21T06:47:00Z
head: 6b07e97a0c18927dfa766ae6f52689eec456e761
branch: develop
pr: 59
status: ready
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
  - Implementation PR 59 was squash-merged to develop as 6b07e97a0c18927dfa766ae6f52689eec456e761 after all required checks passed.
  - The extractor accepts only the canonical pytorch-research-v1 and rl-research-v1 manifests and validates strategy, model, FreqAI identifier, timerange, archive structure, and source hashes.
  - Strict scoring includes only trades with open_date at or after 2026-05-01T00:00:00Z and close_date before 2026-07-01T00:00:00Z.
  - April-crossing and July-crossing trades are excluded and counted; fully contained force_exit trades are included and counted.
  - Output reports profit, drawdown, included trade count, and two-fold May-June stability using included trades only.
  - The protected final holdout remains 20260801-20260930 and manifest validation rejects protected-holdout overlap before archive scoring.
  - Extraction artifacts are phase6_member false and cannot be consumed by the current Phase 6 comparison or selection policy.
  - No data download, training, backtest execution, retuning, model promotion, protected-holdout access, or profitability claim was performed.
derived:
  - Reusing lower-level strict trade parsing and partition helpers preserves boundary semantics without modifying Phase 6 contracts or result artifacts.
  - Experimental contract and schema keep PyTorch and RL evidence provenance separate from Phase 6 evidence.
unknown:
  - No real PyTorch or RL backtest archive has been produced or scored by the extractor.
  - Heavy freqai_rl runtime import and minimal real model integration remain unverified for both canonical research tracks.
conflicts: []
first_failure:
  marker: AI Platform CI Ruff
  evidence: Initial PR runs exposed import-order, line-length, and formatting failures; repository-configured Ruff formatting was applied and final AI Platform CI run 29807297838 passed.
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
  - command: AI Platform CI run 29807297838
    result: PASS
    evidence: Compile, complete AI Platform tests, Ruff, Ruff format, codespell, and configured JSON validation completed successfully on implementation head e46aae21c7e901c4a93c853e93fecbfa86827256.
  - command: Freqtrade CI run 29807297832
    result: PASS
    evidence: Pre-commit, documentation, core test matrix, coverage, repository smoke checks, Ruff, formatting, and mypy gates completed successfully.
  - command: GitHub Actions Security Analysis with zizmor run 29807297829
    result: PASS
    evidence: Security analysis completed successfully on implementation head e46aae21c7e901c4a93c853e93fecbfa86827256.
  - command: PR 59 mergeability and review-thread check
    result: PASS
    evidence: PR was mergeable and had no inline review threads or submitted reviews before squash merge.
blockers: []
next_action: Run a minimal heavy-runtime proof-of-integration smoke for both canonical PyTorch and RL model classes using the freqai_rl dependency profile and synthetic or minimal pre-OOS data only, without historical-OOS scoring or model-performance conclusions.
```
