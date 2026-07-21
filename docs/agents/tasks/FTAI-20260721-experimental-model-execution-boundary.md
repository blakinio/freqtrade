---
task_id: FTAI-20260721-experimental-model-execution-boundary
status: implementing
branch: fix/experimental-model-execution-boundary-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: ""
owned_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/scripts/experimental_model_research_contract.py
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_research_contract.py
  - tests/ai_platform/test_experimental_model_oos_result_extractor.py
  - tests/ai_platform/test_experimental_model_historical_execution_preflight.py
  - .github/workflows/experimental-model-historical-execution-preflight.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-execution-boundary.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RESEARCH.md
  - docs/ai_platform/EXPERIMENTAL_MODEL_RUNTIME_SMOKE.md
search_first:
  - freqtrade/configuration/timerange.py
  - ai_platform/scripts/run_experiment.py
  - ai_platform/scripts/experimental_model_oos_result_extractor.py
---

# Experimental Model Execution Boundary Correction v1

## Goal

Correct the experimental PyTorch/RL Freqtrade execution timeranges so the already-declared semantic windows include all of June 30, while preserving the historical-OOS contract, frozen candidate, Phase 6 isolation, and protected final holdout.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-21T10:10:00Z
head: 4a11a176d17a74c646106db2000db15e8ca1b1c6
branch: fix/experimental-model-execution-boundary-v1
pr: none
status: implementing
context_routes:
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - ai_platform/scripts/experimental_model_research_contract.py
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
owned_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/scripts/experimental_model_research_contract.py
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_research_contract.py
  - tests/ai_platform/test_experimental_model_oos_result_extractor.py
  - tests/ai_platform/test_experimental_model_historical_execution_preflight.py
  - .github/workflows/experimental-model-historical-execution-preflight.yml
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-execution-boundary.md
proven:
  - develop source of truth was ccf98eab3fa90d867558cf2511111415e0bd3e51 when this replacement branch was created.
  - Closed unmerged PR #66 exposed an execution-boundary bug before any canonical experimental backtest or OOS scoring ran.
  - Freqtrade TimeRange.parse_timerange converts an eight-digit stop date to UTC midnight at the start of that date, so a stop of 20260630 excludes June 30 from execution.
  - The strict experimental OOS contract already uses semantic scoring window 20260501-20260630 with end_exclusive 2026-07-01T00:00:00Z.
  - Semantic prediction window remains 20260301-20260630 and semantic download window remains 20250801-20260630.
  - Boundary-corrected technical timeranges are prediction 20260301-20260701 and download 20250801-20260701.
  - Both canonical experimental manifests now use the boundary-corrected technical timeranges while model identities, configs, pairs, timeframes, fee, and artifact roots remain unchanged.
  - The foundation now explicitly separates semantic windows from technical execution timeranges.
  - The strict OOS extractor still scores only fully contained trades in the unchanged May-June semantic scoring window.
  - The replacement preflight uses a new boundary-v2 concurrency group and cache namespace; stale PR #66 download/cache is not accepted as evidence.
  - Protected final holdout 20260801-20260930 remains unused and forbidden; frozen thresholds 0.006/-0.009 and Phase 6 isolation remain unchanged.
derived:
  - Moving only the technical stop boundary to 20260701 is required to execute the already-declared June 30 semantic coverage and is not a retrospective expansion of the research window.
  - A successful boundary-v2 preflight can establish data availability through June 30 before any real PyTorch or RL historical backtest is authorized.
unknown:
  - Whether Kraken data for every required pair/timeframe covers the corrected technical download timerange through the final June 30 candle in GitHub Actions.
  - Whether the boundary-corrected implementation passes all dedicated and repository CI gates on the current branch.
conflicts: []
first_failure:
  marker: exclusive-stop-boundary-off-by-one
  evidence: Canonical manifests and stale PR #66 used stop 20260630, but Freqtrade parses that value as 2026-06-30T00:00:00Z; this omitted the entire semantic final day June 30 and invalidated the stale preflight as execution evidence.
rejected_hypotheses:
  - Accept stale PR #66 download or cache as evidence despite its incorrect stop boundary.
  - Change the semantic historical OOS, prediction, or download windows to July 1.
  - Access the protected 20260801-20260930 final holdout to validate the correction.
  - Run a canonical PyTorch or RL historical backtest before corrected data coverage is proven.
changed_paths:
  - ai_platform/experimental_model_research/foundation-v1.json
  - ai_platform/scripts/experimental_model_research_contract.py
  - ai_platform/experiments/pytorch-research-v1.json
  - ai_platform/experiments/rl-research-v1.json
  - ai_platform/scripts/experimental_model_historical_execution_preflight.py
  - tests/ai_platform/test_experimental_model_research_contract.py
  - tests/ai_platform/test_experimental_model_oos_result_extractor.py
  - tests/ai_platform/test_experimental_model_historical_execution_preflight.py
  - .github/workflows/experimental-model-historical-execution-preflight.yml
  - docs/agents/tasks/FTAI-20260721-experimental-model-execution-boundary.md
validation:
  - command: GitHub Actions
    result: NOT_RUN
    evidence: Boundary-corrected replacement pull request has not been opened yet.
blockers: []
next_action: Document the corrected semantic-versus-execution boundary, open the replacement pull request against develop, and require the boundary-v2 historical preflight, AI Platform CI, Freqtrade CI, and zizmor to pass before merge; fix only concrete failures and do not execute a canonical experimental backtest.
```
