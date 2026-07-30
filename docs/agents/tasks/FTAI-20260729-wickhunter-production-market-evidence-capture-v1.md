---
task_id: FTAI-20260729-wickhunter-production-market-evidence-capture-v1
status: active
branch: agent/wickhunter-production-market-evidence-capture-v1
base_branch: develop
created: 2026-07-29
updated: 2026-07-29
depends_on:
  - FTAI-20260729-wickhunter-production-evidence-inventory-v1
owned_paths:
  - ai_platform/wickhunter/production_market_evidence.py
  - ai_platform/wickhunter/production-market-evidence-contract-v1.json
  - .github/workflows/ai-platform-wickhunter-production-market-evidence.yml
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence.py
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-production-market-evidence-capture-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-production-evidence-inventory-v1.md
  - docs/ai_platform/WICKHUNTER_PRODUCTION_EVIDENCE_INVENTORY.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
---

# WickHunter production market evidence capture v1

## Goal

Implement the separately reviewed prospective evidence-capture package required by the production inventory: freeze source-separated Binance USD-M and Bybit Linear completed candles, spread and rolling-volume evidence with sufficient pre-roll and exact identities, without changing WH-01 materialization or granting downstream authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-29T23:35:00+02:00
head: e9b884a842ad972b48a7eace1f8449b6ddc9190b
branch: agent/wickhunter-production-market-evidence-capture-v1
pr: none
status: active
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-production-evidence-inventory-v1.md
  - docs/ai_platform/WICKHUNTER_PRODUCTION_EVIDENCE_INVENTORY.md
  - docs/ai_platform/WICKHUNTER_DATASET_BUILDER.md
owned_paths:
  - ai_platform/wickhunter/production_market_evidence.py
  - ai_platform/wickhunter/production-market-evidence-contract-v1.json
  - .github/workflows/ai-platform-wickhunter-production-market-evidence.yml
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence.py
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-production-market-evidence-capture-v1.md
proven:
  - The accepted production liquidation import is immutable and non-empty, but the reviewed repository and durable evidence paths contain no compatible July 29 historical spread, rolling-volume or completed-candle package.
  - Historical spread snapshots cannot be reconstructed truthfully from the current exchange state, so the first compatible evidence package must be prospective and overlap a newly closed Liquid20 archive.
  - Existing source-separated public candle normalization and the non-blocking durable incremental workflow pattern can be consumed without editing active Market Data Fabric or Liquid20 deployment paths.
  - The frozen prospective geometry uses 24 hours of candle pre-roll and a 12-hour decision interval ending six hours before the protected final holdout.
derived:
  - The implementation PR can remain no-network by excluding the exact-one-file request; public acquisition starts only through a separately reviewed trigger after merge.
  - An accepted capture will remove the market-context blocker but will not by itself establish dynamic-universe history, split geometry or a non-empty WH-01 dataset.
unknown:
  - Whether every scheduled Synology sample and all terminal public candle requests will complete successfully in the prospective interval.
  - Which contemporaneous closed Liquid20 archive will be selected after the capture becomes immutable.
conflicts: []
first_failure:
  marker: local_repository_clone_unavailable
  evidence: The local runtime could not resolve github.com, so repository reads and writes use the GitHub connector while deterministic module tests run against injected public-response fixtures.
rejected_hypotheses:
  - Backdate current spread, rolling-volume or instrument state into the July 29 accepted interval.
  - Put public endpoint access inside the unchanged WH-01 materialization operator.
  - Merge a live run request with the implementation package.
  - Start WH-02, train a model, execute replay or submit orders before a non-empty verified dataset exists.
changed_paths:
  - ai_platform/wickhunter/production_market_evidence.py
  - ai_platform/wickhunter/production-market-evidence-contract-v1.json
  - .github/workflows/ai-platform-wickhunter-production-market-evidence.yml
  - tests/ai_platform_integration/test_wickhunter_production_market_evidence.py
  - docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md
  - docs/agents/tasks/FTAI-20260729-wickhunter-production-market-evidence-capture-v1.md
validation:
  - command: PYTHONPATH=. pytest -q tests/ai_platform_integration/test_wickhunter_production_market_evidence.py with an import-compatible candle normalizer stub
    result: PASS
    evidence: Five deterministic tests passed, including a full 144-sample and 40-candle package, independent verification, not-due behavior, request/environment/state tamper refusal, missing-symbol refusal and workflow/contract boundaries.
  - command: python -m py_compile production_market_evidence.py test_wickhunter_production_market_evidence.py
    result: PASS
    evidence: New Python sources compile in the local Python runtime.
blockers: []
next_action: Publish the six-path implementation package, run exact-head repository CI, repair only evidenced failures, merge normally when green, then create and close the separately reviewed exact-one-file trigger PR after durable initialization succeeds.
```
