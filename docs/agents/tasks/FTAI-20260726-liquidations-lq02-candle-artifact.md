---
task_id: FTAI-20260726-liquidations-lq02-candle-artifact
status: ready
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#350"
owned_paths:
  - ai_platform/research/liquidations/datasets/__init__.py
  - ai_platform/research/liquidations/datasets/candle_artifact.py
  - ai_platform/research/liquidations/datasets/liquid20-candle-artifact-contract-v1.json
  - ai_platform/scripts/liquidation_candle_artifact.py
  - tests/ai_platform_integration/test_liquidation_candle_artifact.py
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - pyproject.toml
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
search_first:
  - current develop, open PR ownership and exact required checks
  - Synology issue 148 and completed Liquid20 run status
  - existing candle evidence, download workflows and protected-holdout boundaries
optional_reads: []
---

# LQ-02 source-separated candle artifact infrastructure

## Goal

Implement only the deterministic infrastructure needed to create a source-separated, versioned 5-minute candle artifact for the completed failed Liquid20 run. The first request remains diagnostic-only and cannot authorize replay or performance research.

## Declared artifact

The later exact-one-file trigger request will bind:

- Liquid20 run `liquid20-20260724T170830Z-1`;
- UTC window `2026-07-24T00:00:00Z` inclusive through `2026-07-26T00:00:00Z` exclusive;
- timeframe `5m`;
- exact ordered `liquid20-v1` membership and Freqtrade futures pair mapping;
- separate Bybit linear and Binance USD-M trade-price candle files;
- 576 candles for each of 40 source-symbol files;
- immutable file hashes, counts, coverage and source identities;
- `performance_research_authorized: false`.

The selected window ends before the protected holdout and contains only completed candles. A missing, duplicated, malformed or source-mismatched candle fails the entire artifact atomically.

## Execution separation

The merged infrastructure contains no run request and performs no network data download. A separate PR may add exactly:

`ai_platform/research/liquidations/datasets/run-requests/liquid20-candle-diagnostic-20260724-v1.json`

The dedicated workflow accepts only that one added file, uses public endpoints without credentials, writes source-separated evidence, verifies every hash and uploads a bounded 90-day diagnostic artifact. The trigger PR must close without merge after terminal evidence is captured.

The workflow path is an unavoidable dependency because the requested public source files do not exist in the repository and must be generated against a reviewed exact commit. The narrow `pyproject.toml` change adds per-file Ruff exceptions only for the fail-closed validator and frozen HTTPS transport; it changes no global lint rule. No deployment, order, portal, credential or live-capital behavior is added.

## Safety boundaries

- failed Liquid20 evidence remains diagnostic-only;
- no completed run is relabelled accepted;
- no cross-exchange deduplication or unlabeled summation;
- no missing candle becomes zero;
- no incomplete candle is admitted;
- no exchange credential is accepted;
- no order, strategy, replay, model, DCA, leverage or live capital;
- no protected-holdout access;
- no browser or portal exposure.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T12:16:00Z
head: e448c7137e4787525cbba1da2c90a8a98812e219
branch: develop
pr: "#350"
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
owned_paths:
  - ai_platform/research/liquidations/datasets/__init__.py
  - ai_platform/research/liquidations/datasets/candle_artifact.py
  - ai_platform/research/liquidations/datasets/liquid20-candle-artifact-contract-v1.json
  - ai_platform/scripts/liquidation_candle_artifact.py
  - tests/ai_platform_integration/test_liquidation_candle_artifact.py
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - pyproject.toml
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
proven:
  - Blocked LQ-02 dataset-selection preflight is merged as a9f818e1f5f5948fc095f374a554952e3d070e33.
  - Completed run liquid20-20260724T170830Z-1 failed exactly binance-usdm.maximum_latency_over_threshold_ratio and remains diagnostic-only.
  - Active run liquid20-20260725T212201Z-1 had no final report at the last Synology status check.
  - No adequate versioned candle artifact exists yet.
  - The declared 2026-07-24 through 2026-07-26 window is before the protected 2026-08-01 through 2026-10-01 holdout.
  - The contract binds source catalog and liquid20-v1 universe SHA-256 identities and preserves ordered source-separated membership.
  - Focused validation passes 10 deterministic tests, Python compilation, exact Ruff 0.15.21 lint and formatting, mypy and repository pre-commit.
  - PR 350 merged the eight-file infrastructure package as e448c7137e4787525cbba1da2c90a8a98812e219 with no run request or temporary diagnostic workflow.
  - Exact candidate head 4320eba3a68fb34359639236675c4d3bf50f7fe3 passed AI Platform CI 1523, Freqtrade CI 1839, GitHub Actions Security Analysis 1704 and Experimental Model Runtime Smoke 124.
  - Trigger PR 366 passed exact-one-file scope and stopped before network access because the merged checkpoint used unsupported status reviewing.
derived:
  - One 48-hour request fits both source limits with 576 rows per source-symbol file.
  - Source-separated public candles can remove the candle-identity blocker without changing failed liquidation acceptance.
  - An exact-one-file trigger prevents infrastructure review from silently executing data collection.
unknown:
  - Whether both public endpoints return complete 576-row coverage for all 20 symbols from GitHub-hosted Linux.
  - Exact hashes and sizes of the generated 40 files.
  - Whether the first generated package can later be copied to durable Synology storage without a separate deployment package.
conflicts: []
first_failure:
  marker: checkpoint-status-reviewing-not-allowed
  evidence: Trigger run 30201634582 failed before network access because reviewing is not an allowed governance checkpoint status.
rejected_hypotheses:
  - Add the run request to the infrastructure PR.
  - Use one exchange candle source for both liquidation venues.
  - Deduplicate or merge Bybit and Binance candles into an unlabeled artifact.
  - Fill missing candles or represent unavailable data as zero.
  - Include the protected holdout or an incomplete current candle.
  - Treat the diagnostic candle artifact as performance authorization.
  - Start replay, strategy, model or execution work.
changed_paths:
  - ai_platform/research/liquidations/datasets/__init__.py
  - ai_platform/research/liquidations/datasets/candle_artifact.py
  - ai_platform/research/liquidations/datasets/liquid20-candle-artifact-contract-v1.json
  - ai_platform/scripts/liquidation_candle_artifact.py
  - tests/ai_platform_integration/test_liquidation_candle_artifact.py
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - pyproject.toml
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
validation:
  - command: PYTHONPATH=. pytest -q -o addopts='' --confcutdir=tests/ai_platform_integration tests/ai_platform_integration/test_liquidation_candle_artifact.py
    result: PASS
    evidence: 10 tests passed for parsing, identity, coverage, source separation, determinism, hash drift, atomic failure, credentials, holdout and malformed input.
  - command: python -m compileall -q ai_platform tests
    result: PASS
    evidence: Candle artifact module, CLI and tests compiled successfully.
  - command: ruff 0.15.21 check and format plus mypy and repository pre-commit
    result: PASS
    evidence: Exact repository tooling accepted lint, formatting and typing; Freqtrade CI 1839 passed.
  - command: pull request scope and merge
    result: PASS
    evidence: PR 350 contained exactly eight final files and merged as e448c7137e4787525cbba1da2c90a8a98812e219.
  - command: exact-head repository CI
    result: PASS
    evidence: Head 4320eba3a68fb34359639236675c4d3bf50f7fe3 passed AI Platform CI 1523, Freqtrade CI 1839, GitHub Actions Security Analysis 1704 and Experimental Model Runtime Smoke 124.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md --require-checkpoint
    result: PASS
    evidence: The repaired checkpoint uses governance-allowed status ready and a concrete next action.
blockers: []
next_action: After this checkpoint repair merges, open a new exact-one-file diagnostic candle request trigger PR and close it without merge after terminal artifact evidence is captured.
```
