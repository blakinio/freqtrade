---
task_id: FTAI-20260724-liquidation-reversal-foundation
status: validating
branch: feat/liquidation-reversal-foundation-v1
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: pending
owned_paths:
  - ai_platform/research/liquidations/**
  - ai_platform/scripts/liquidation_collector.py
  - tests/ai_platform_integration/test_liquidation_research_foundation.py
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
---

# Liquidation Reversal Foundation

## Goal

Prepare the minimum safe data, signal, validation, and deployment foundation for a Wick Hunter-inspired
liquidation reversal strategy without enabling execution, DCA, live capital, profitability claims, or use of
the protected final holdout.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T08:30:00Z
head: 035feedcb3a1146b553db8685979064a262caacf
branch: feat/liquidation-reversal-foundation-v1
pr: pending
status: validating
context_routes:
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/TRADINGVIEW_STRATEGY_RESEARCH.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
owned_paths:
  - ai_platform/research/liquidations/**
  - ai_platform/scripts/liquidation_collector.py
  - tests/ai_platform_integration/test_liquidation_research_foundation.py
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
proven:
  - Existing Wick Hunter research was blocked because the repository had only VWAP gates and no trustworthy liquidation event stream or deterministic alignment contract.
  - Public Wick Hunter behavior requires a real liquidation event plus a minimum notional and an out-of-band VWAP or VWMA condition before counter-trading the liquidated side.
  - Bybit documents a public linear allLiquidation topic with source timestamps, symbol, side, size, and bankruptcy price.
  - The new profile is research-only, disabled, dry-run, execution-disabled, and has DCA and exits disabled.
  - Local compile and eleven focused tests pass in the sandbox.
derived:
  - The first safe operational step is data-only collection with no exchange credentials or Freqtrade execution adapter.
  - Completed-candle-only alignment is conservative and prevents use of unfinished candle OHLCV in replay.
unknown:
  - Repository CI conclusion for the branch.
  - Operational event volume, gap rate, and latency distribution for BTCUSDT and ETHUSDT.
  - Exact volume filter metric, exit policy, and DCA policy for a future replay contract.
conflicts: []
first_failure:
  marker: local-clone-dns
  evidence: Sandbox git clone could not resolve github.com; changes were written through GitHub API and executable validation relies on focused local files plus repository CI.
rejected_hypotheses:
  - Treat a VWAP band breach without a real liquidation observation as a valid entry.
  - Use the current unfinished candle final OHLCV in historical replay.
  - Enable DCA or real order execution before a frozen replay and dry-run evidence package exists.
changed_paths:
  - ai_platform/research/liquidations/__init__.py
  - ai_platform/research/liquidations/contracts.py
  - ai_platform/research/liquidations/bybit.py
  - ai_platform/research/liquidations/alignment.py
  - ai_platform/research/liquidations/signals.py
  - ai_platform/research/liquidations/profile-example-v1.json
  - ai_platform/scripts/liquidation_collector.py
  - tests/ai_platform_integration/test_liquidation_research_foundation.py
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
validation:
  - command: PYTHONPATH=. python -m compileall -q ai_platform tests
    result: PASS
    evidence: New project Python files and focused tests compiled successfully in the sandbox.
  - command: PYTHONPATH=. pytest -q tests/ai_platform_integration/test_liquidation_research_foundation.py
    result: PASS
    evidence: Eleven focused parser, serialization, alignment, deduplication, and signal-policy tests passed.
  - command: ruff check and ruff format --check on changed Python files
    result: BLOCKED
    evidence: Ruff is not installed in the sandbox; repository AI Platform CI is the authoritative lint path.
blockers:
  - No collected immutable liquidation dataset exists yet; this blocks historical replay and any profitability conclusion.
next_action: Open the pull request against develop and inspect the first failing repository CI check; fix only branch-local foundation defects without enabling execution.
```
