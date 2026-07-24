---
task_id: FTAI-20260724-liquidation-symbol-universe-v1
status: blocked
branch: develop
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "#254"
owned_paths:
  - ai_platform/research/liquidations/symbol-universes-v1.json
  - ai_platform/research/liquidations/symbol_universe.py
  - ai_platform/research/liquidations/evidence/liquid20-subscription-github-us-20260724-v1.json
  - ai_platform/scripts/liquidation_multi_source_runner.py
  - tests/ai_platform_integration/test_liquidation_symbol_universe.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-symbol-universe-v1.md
required_reads:
  - AGENTS.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
---

# Liquidation Symbol Universe v1

## Goal

Expand multi-source liquidation collection from two symbols to a frozen, auditable 20-symbol universe shared by Bybit linear and Binance USD-M.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T13:30:00Z
head: ce55009a5b87aae091df5f14a3a1c96ce1beedd4
branch: develop
pr: "#254"
status: blocked
proven:
  - PR #254 merged to develop as ce55009a5b87aae091df5f14a3a1c96ce1beedd4.
  - liquid20-v1 contains 20 exact versioned USDT perpetual symbols.
  - The loader enforces symbol format, uniqueness, counts, thresholds, a review gate above 50, and a hard maximum of 100.
  - The runner passes the same profile to both sources and preserves separate outputs plus one manifest.
  - Candidate 627e71d6df055c97444e98dbb919e7f5a8a6d6e1 passed AI Platform CI run 30089452937 and zizmor run 30089452946.
  - Freqtrade CI run 30089452933 passed pre-commit and the documentation build before merge.
  - Public subscription run 30089322467 job 89468775700 accepted all 20 symbols on both sources.
  - Subscription evidence is preserved in ai_platform/research/liquidations/evidence/liquid20-subscription-github-us-20260724-v1.json.
derived:
  - Twenty symbols should produce more observations than BTC and ETH alone while remaining manageable.
  - A changing market ranking is unsuitable for reproducible evidence; profile changes require a new version.
  - A 100-symbol profile requires a separate capacity and symbol-lifecycle work package.
unknown:
  - Per-symbol event frequency, 24-hour availability, latency, gaps, and storage growth.
  - Final result of the broad non-blocking core matrix in Freqtrade CI run 30089452933.
first_failure:
  marker: no-operational-liquid20-run
  evidence: Subscription compatibility is proven, but no accepted 24-hour liquid20-v1 run exists on the intended staging host.
validation:
  - command: AI Platform CI run 30089452937
    result: PASS
  - command: zizmor run 30089452946
    result: PASS
  - command: Freqtrade pre-commit and documentation jobs in run 30089452933
    result: PASS
  - command: public 20-symbol subscription run 30089322467
    result: PASS
blockers:
  - No accepted 24-hour multi-source liquid20-v1 run exists on the intended staging host.
next_action: Declare and run a 24-hour liquid20-v1 acceptance package measuring source availability, symbol coverage, gaps, latency, event counts, and storage growth.
```
