---
task_id: FTAI-20260726-liquidations-lq02-candle-artifact
status: ready
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#350, #371, #373, #375"
owned_paths:
  - ai_platform/research/liquidations/datasets/candle_artifact.py
  - ai_platform/research/liquidations/datasets/liquid20-candle-artifact-contract-v1.json
  - ai_platform/scripts/liquidation_candle_artifact.py
  - deploy/synology/liquid20-candle-artifact/
  - tests/ai_platform_integration/test_liquidation_candle_artifact.py
  - tests/ai_platform_integration/test_liquidation_candle_failure_evidence.py
  - tests/ai_platform_integration/test_liquidation_candle_synology_runtime.py
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
search_first:
  - published candle evidence envelope and workflow artifact retention
  - current Liquid20 final reports and passed true status
  - durable Synology raw artifact storage
optional_reads: []
---

# LQ-02 source-separated candle artifact

## Result

The infrastructure and bounded Synology runtime are merged. Trigger PR `#375` closed without merge after workflow run `30205769267` successfully created and verified source-separated Bybit linear and Binance USD-M 5-minute candles for `2026-07-24T00:00:00Z` through `2026-07-26T00:00:00Z`.

The package contains 40 source-symbol files, 576 records each and 23,040 records total. Independent verification reproduced the archive digest, exact manifest file hash, manifest self-hash, all 41 checksum entries, continuous timestamp coverage, source/pair identity, protected-holdout exclusion, zero orders and no trading credentials.

Repository evidence is published under `docs/ai_platform/liquidations/datasets/`. The raw GitHub artifact is retained until `2026-10-24T14:17:16Z`; a durable raw Synology archive is not yet proven.

The bound Liquid20 run remains failed and diagnostic-only. This package does not authorize replay or performance research.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T14:30:00Z
head: a4642ce59116e9e08eab37c0cdabcdbeace02314
branch: develop
pr: "#350, #371, #373, #375"
status: ready
context_routes:
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-evidence-publication.md
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-dataset-selection.md
  - docs/ai_platform/portal/liquidations-ai-bot-artifact-contracts-v1.json
owned_paths:
  - ai_platform/research/liquidations/datasets/candle_artifact.py
  - ai_platform/research/liquidations/datasets/liquid20-candle-artifact-contract-v1.json
  - ai_platform/scripts/liquidation_candle_artifact.py
  - deploy/synology/liquid20-candle-artifact/
  - tests/ai_platform_integration/test_liquidation_candle_artifact.py
  - tests/ai_platform_integration/test_liquidation_candle_failure_evidence.py
  - tests/ai_platform_integration/test_liquidation_candle_synology_runtime.py
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
  - docs/agents/tasks/FTAI-20260726-liquidations-lq02-candle-artifact.md
proven:
  - PR 350 merged deterministic candle artifact infrastructure.
  - PR 371 merged bounded failure evidence with source and symbol context.
  - PR 373 merged the non-root bounded Synology runtime.
  - PR 375 closed without merge after workflow run 30205769267 succeeded.
  - Artifact 8633031826 has archive digest d3d25327c1b8f70a89638f26d95aae495b27b96a684add830581f2755e146cfd.
  - The verified package has 40 files, 576 records per file and 23040 records total.
  - Manifest, manifest self-hash and all 41 checksum entries reproduced independently.
  - Source separation, no-zero missing policy, no-order boundary and holdout exclusion passed.
derived:
  - The source-separated candle identity blocker is closed for diagnostic use.
  - Complete candles do not change the failed Liquid20 acceptance result.
  - Performance research and replay remain unauthorized.
unknown:
  - Durable raw artifact storage after GitHub retention expires.
  - Whether a newer Liquid20 run has explicit passed true and complete immutable run hashes.
conflicts: []
first_failure:
  marker: NONE
  evidence: The final Synology trigger completed successfully and published verified evidence.
rejected_hypotheses:
  - Use a US runner despite Bybit HTTP 403 restrictions.
  - Replace one venue's candles with the other venue.
  - Deduplicate exchanges or fill missing candles with zero.
  - Treat diagnostic candles as performance authorization.
changed_paths:
  - ai_platform/research/liquidations/datasets/candle_artifact.py
  - ai_platform/research/liquidations/datasets/liquid20-candle-artifact-contract-v1.json
  - ai_platform/scripts/liquidation_candle_artifact.py
  - deploy/synology/liquid20-candle-artifact/Dockerfile
  - deploy/synology/liquid20-candle-artifact/run.sh
  - tests/ai_platform_integration/test_liquidation_candle_artifact.py
  - tests/ai_platform_integration/test_liquidation_candle_failure_evidence.py
  - tests/ai_platform_integration/test_liquidation_candle_synology_runtime.py
  - .github/workflows/ai-platform-liquidation-candle-artifact.yml
validation:
  - command: AI Platform Liquid20 Candle Artifact run 30205769267
    result: PASS
    evidence: Exact-one-file, credential refusal, bounded build, collection, verification and upload succeeded.
  - command: independent archive and record verification
    result: PASS
    evidence: Archive digest, manifest identities, 41 hashes and 23040 records reproduced.
  - command: infrastructure exact-head CI
    result: PASS
    evidence: PR 373 passed Freqtrade CI 1891 and zizmor 1756 before merge a4642ce59116e9e08eab37c0cdabcdbeace02314.
blockers: []
next_action: Publish the repository evidence envelope and use it only for diagnostic LQ-02 classification while separately proving durable raw storage before artifact expiry.
```
