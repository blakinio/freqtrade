---
task_id: FTAI-20260721-experimental-model-execution-boundary
status: validating
branch: fix/experimental-model-execution-boundary-v1
base_branch: develop
created: 2026-07-21
updated: 2026-07-21
related_pr: "#75"
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
updated_at: 2026-07-21T10:30:00Z
head: b4c66a4766fa6d35d408807aaac1551611893dff
branch: fix/experimental-model-execution-boundary-v1
pr: "#75"
status: validating
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
  - develop source of truth was ccf98eab3fa90d867558cf2511111415e0bd3e51 when this replacement branch was created; independent Phase 6 PR #72 later advanced develop without overlapping owned paths.
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
  - PR #75 AI Platform CI run 29821140109 and zizmor run 29821140013 completed successfully on implementation head b4c66a4766fa6d35d408807aaac1551611893dff.
  - PR #75 Experimental Model Runtime Smoke run 29821140074 completed successfully with the boundary-corrected canonical manifests.
  - Freqtrade core Python 3.13 checks, including Ruff, Ruff format, Mypy, generated-file checks, backtesting smoke and Hyperopt smoke, completed successfully; only the separate pre-commit job failed on the first implementation run.
derived:
  - Moving only the technical stop boundary to 20260701 is required to execute the already-declared June 30 semantic coverage and is not a retrospective expansion of the research window.
  - A successful boundary-v2 preflight can establish data availability through June 30 before any real PyTorch or RL historical backtest is authorized.
unknown:
  - Whether Kraken data for every required pair/timeframe covers the corrected technical download timerange through the final June 30 candle in GitHub Actions.
  - Whether the first pre-commit failure is transient or a fixer-only issue not covered by the already-green Ruff, format, Mypy, codespell, zizmor and generated-file gates.
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
  - docs/ai_platform/EXPERIMENTAL_MODEL_HISTORICAL_EXECUTION_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260721-experimental-model-execution-boundary.md
validation:
  - command: AI Platform CI run 29821140109
    result: PASS
    evidence: Boundary contract tests, Ruff, Ruff format, Codespell, and manifest validation completed successfully.
  - command: GitHub Actions Security Analysis with zizmor run 29821140013
    result: PASS
    evidence: Workflow security analysis completed successfully.
  - command: Experimental Model Runtime Smoke run 29821140074
    result: PASS
    evidence: Canonical PyTorch reproducibility and RL environment/PPO runtime paths remained green with corrected manifests.
  - command: Freqtrade CI run 29821140003
    result: FAIL
    evidence: Core matrix remains otherwise green/in progress, but the first pre-commit checks job failed; final retry is deferred until the workflow run completes.
  - command: Experimental Model Historical Execution Preflight run 29821140343
    result: NOT_RUN
    evidence: Contract and resolver gates passed; boundary-corrected Kraken download and final coverage verification are still running.
blockers: []
next_action: Let the boundary-v2 preflight finish and save corrected coverage evidence, let the current Freqtrade CI run complete, then rerun only the failed pre-commit job to distinguish a transient hook failure from a concrete fixer issue; require all gates green before merge and do not execute a canonical experimental backtest.
```
