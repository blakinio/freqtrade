---
task_id: FTAI-20260726-liquidations-lq02-dataset-selection
status: blocked
branch: feat/liquidations-lq02-dataset-selection-20260726
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#346"
owned_paths:
  - ai_platform/research/liquidations/datasets/
  - ai_platform/scripts/liquidation_dataset_selector.py
  - tests/ai_platform_integration/test_liquidation_dataset_selection.py
  - docs/ai_platform/liquidations/datasets/liquidations-lq02-dataset-selection-preflight-20260726-v1.json
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-architecture-v1.json
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/agents/tasks/FTAI-20260726-liquidations-ai-bot-agent-package.md
search_first:
  - current develop HEAD, open PRs, path ownership and required checks
  - current Synology collector image, container state, latest runs and final reports
  - immutable source artifacts, hashes and versioned candle evidence
optional_reads: []
---

# LQ-02 Liquid20 dataset selection preflight and contract

## Goal

Start only LQ-02 and determine whether immutable Liquid20 and candle evidence permit a `DatasetSelectionManifest`. Replay, strategy tuning, AI training, execution, DCA, leverage and live capital remain out of scope.

## Contract decision

`docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json` remains authoritative. No selection manifest or selector implementation is emitted while required evidence is absent.

A future selector must fail closed unless it verifies:

- explicit final `passed: true` for every performance-selected run;
- source-separated Bybit and Binance files, summaries, manifest and report with hashes and counts;
- collector, parser, source-catalog, universe and policy identities;
- accepted and quarantined interval boundaries;
- versioned candle files with source/version, logical names, pair mapping, timeframe, coverage, counts and SHA-256;
- protected-holdout and prior-use classification;
- deterministic canonical manifest hashing.

Failed evidence remains `diagnostic_only` and cannot authorize performance research.

## Live-state result

- `develop` was rechecked at `c1b8b9186cffbd6dcadf6c1df7a395e8b52f51cc`.
- H0 historical-provider preflight merged and selected Tardis for future event imports, but it remains `owner_action_required` and produced no candle artifact.
- Synology still reports immutable collector image and commit `c00a091c5adc67cf75c46db5805e358ffc72fad7`.
- Completed run `liquid20-20260724T170830Z-1` has `passed: false` and failed exactly `binance-usdm.maximum_latency_over_threshold_ratio`.
- Active run `liquid20-20260725T212201Z-1` is still running without a final report.
- No adequate versioned candle artifact was located.
- Exact completed-run source and metadata hashes remain unpublished through the explicit non-mutating collect path.
- Checked intervals precede protected holdout `2026-08-01T00:00:00Z` through `2026-10-01T00:00:00Z`.

Machine-readable preflight:

`docs/ai_platform/liquidations/datasets/liquidations-lq02-dataset-selection-preflight-20260726-v1.json`

## Scope boundaries

Only the task record and immutable blocked-preflight evidence are changed. No replay, strategy, feature, model, execution, portal, credential or deployment path is modified.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T09:12:00Z
head: c1b8b9186cffbd6dcadf6c1df7a395e8b52f51cc
branch: feat/liquidations-lq02-dataset-selection-20260726
pr: "#346"
status: blocked
context_routes:
  - docs/ai_platform/portal/LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md
  - docs/ai_platform/portal/LIQUIDATIONS_AI_BOT_IMPLEMENTATION_BLUEPRINT.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
owned_paths:
  - ai_platform/research/liquidations/datasets/
  - ai_platform/scripts/liquidation_dataset_selector.py
  - tests/ai_platform_integration/test_liquidation_dataset_selection.py
  - docs/ai_platform/liquidations/datasets/liquidations-lq02-dataset-selection-preflight-20260726-v1.json
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
proven:
  - Develop was rechecked at c1b8b9186cffbd6dcadf6c1df7a395e8b52f51cc and open ownership remains disjoint from LQ-02 paths.
  - H0 merged Tardis provider preflight but did not create or authorize a candle artifact.
  - Synology reports immutable collector image and commit c00a091c5adc67cf75c46db5805e358ffc72fad7.
  - Completed run liquid20-20260724T170830Z-1 failed exactly binance-usdm.maximum_latency_over_threshold_ratio.
  - Completed run counts were 771 Bybit and 1777 Binance with all 20 symbols observed on both sources.
  - Active run liquid20-20260725T212201Z-1 is running without a final acceptance report.
  - No completed inspected run explicitly contains passed true.
  - No adequate versioned candle artifact with hashes, coverage, timeframe and pair mapping was located.
  - Immutable preflight canonical hash is 2097a64f7ab9c577745fd20ace5f231611d129df8a6551f94943139b094cf004.
derived:
  - Performance research and replay remain unauthorized.
  - The failed completed run is diagnostic-only and cannot later become strict OOS.
  - Tardis H0 does not remove the independent candle-evidence blocker.
unknown:
  - Final acceptance result of active run liquid20-20260725T212201Z-1.
  - Exact source NDJSON, summary, manifest and report hashes until explicit collection.
  - Exact Synology free-space and retention capacity.
  - Final source-specific candle provider and immutable artifact layout.
conflicts: []
first_failure:
  marker: versioned-candle-evidence-unavailable
  evidence: No logical candle artifact with source/version, SHA-256, record count, interval coverage, timeframe and pair mapping exists.
rejected_hypotheses:
  - Treat passed false evidence as performance-authorizing.
  - Treat an active run without a final report as accepted.
  - Treat Tardis event-provider preflight as candle evidence.
  - Invent candle files, hashes, coverage or pair mappings.
  - Weaken the frozen Binance latency gate.
  - Deduplicate Bybit and Binance observations across exchanges.
  - Start replay, strategy, AI or execution while blocked.
changed_paths:
  - docs/ai_platform/liquidations/datasets/liquidations-lq02-dataset-selection-preflight-20260726-v1.json
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
validation:
  - command: repository, PR ownership, H0, Synology and immutable-evidence recheck
    result: PASS
    evidence: Develop c1b8b9186cffbd6dcadf6c1df7a395e8b52f51cc, H0 merge, issue 148 and PR 346 were inspected.
  - command: canonical JSON hash recomputation excluding preflight_sha256
    result: PASS
    evidence: Canonical JSON reproduced 2097a64f7ab9c577745fd20ace5f231611d129df8a6551f94943139b094cf004.
  - command: repository CI on rebased PR head
    result: NOT_RUN
    evidence: Rebased head has not been created yet.
blockers:
  - No completed Liquid20 run has a final report with explicit passed true.
  - No adequate versioned candle artifact exists for the requested interval.
  - Exact immutable run artifact hashes are not published through explicit collection.
next_action: Create and publish a source-separated versioned candle artifact manifest with exact logical files, SHA-256 hashes, record counts, start and end coverage, 5m timeframe and Liquid20 pair mapping.
```
