---
task_id: FTAI-20260724-liquidation-data-only-staging
status: active
branch: feat/liquidation-data-only-staging-v1
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: pending
owned_paths:
  - ai_platform/research/liquidations/staging.py
  - ai_platform/research/liquidations/data-only-staging-policy-v1.json
  - ai_platform/scripts/liquidation_collector.py
  - ai_platform/scripts/liquidation_staging_evaluator.py
  - tests/ai_platform_integration/test_liquidation_data_only_staging.py
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/agents/tasks/FTAI-20260724-liquidation-data-only-staging.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
---

# Liquidation Data-Only Staging

## Goal

Make Stage 1 operationally measurable without loading a Freqtrade strategy, accepting exchange credentials,
submitting orders, enabling DCA, or using the protected final holdout for research.

## Prospective policy

The policy is frozen before live evidence is judged:

- smoke mode: at least 20 seconds, one received message, zero parse failures, synchronized clock, no
  disconnect, new output file, immutable hash, and exact endpoint/symbol contract;
- acceptance mode: at least 24 hours, availability at least `0.995`, no parse failures, at most two
  disconnects per hour, duplicate ratio at most `0.01`, at least ten latency samples, at most `0.01` of
  samples above five seconds, and at least one observed event for each declared symbol;
- both modes require a recorded 40-character Git commit and reject any detected exchange credential
  environment variable;
- smoke success proves transport and evidence generation only; it does not satisfy Stage 1 acceptance.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T11:20:00Z
head: f71b94f29553273c6ef991814bbe1143eef81af6
branch: feat/liquidation-data-only-staging-v1
pr: pending
status: implementing
context_routes:
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_REVERSAL_RESEARCH.md
owned_paths:
  - ai_platform/research/liquidations/staging.py
  - ai_platform/research/liquidations/data-only-staging-policy-v1.json
  - ai_platform/scripts/liquidation_collector.py
  - ai_platform/scripts/liquidation_staging_evaluator.py
  - tests/ai_platform_integration/test_liquidation_data_only_staging.py
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/agents/tasks/FTAI-20260724-liquidation-data-only-staging.md
  - docs/agents/tasks/FTAI-20260724-liquidation-reversal-foundation.md
proven:
  - Foundation PR #236 merged to develop as 8ab033dd771b3f4695328b22f61c3f6d05a6e1d4.
  - Bybit documents the public allLiquidation topic, 500 ms push frequency, source timestamps, symbol, side, size, and bankruptcy price.
  - Bybit documents the unauthenticated /v5/market/time endpoint with server seconds and nanoseconds.
  - The branch adds bounded collection, connection intervals, availability, reconnect, parse, duplicate, symbol, latency, clock, output-hash, and line-count evidence.
  - The frozen policy separates a short transport smoke from a 24-hour operational acceptance run.
  - Nine focused local tests pass.
derived:
  - A smoke run may legitimately contain zero liquidation events because the source pushes only actual liquidations.
  - An accepted research interval must remain outside 20260801-20260930 and be frozen separately before replay.
unknown:
  - Whether GitHub-hosted networking can reach the Bybit REST and public WebSocket endpoints.
  - Repository Ruff, mypy, pre-commit, and full CI results for the new implementation.
  - Operational 24-hour acceptance evidence from an always-on staging host.
conflicts: []
first_failure:
  marker: none
  evidence: No branch-local implementation failure is known before repository CI.
rejected_hypotheses:
  - Count a short smoke as Stage 1 acceptance.
  - Require a liquidation event during a short smoke.
  - Store or request exchange API credentials for the public collector.
  - Start a Freqtrade strategy or execution adapter in Stage 1.
changed_paths:
  - ai_platform/research/liquidations/staging.py
  - ai_platform/research/liquidations/data-only-staging-policy-v1.json
  - ai_platform/scripts/liquidation_collector.py
  - ai_platform/scripts/liquidation_staging_evaluator.py
  - tests/ai_platform_integration/test_liquidation_data_only_staging.py
validation:
  - command: PYTHONPATH=. python -m compileall -q ai_platform tests
    result: PASS
    evidence: New and modified Python files compile locally.
  - command: PYTHONPATH=. pytest -q tests/ai_platform_integration/test_liquidation_data_only_staging.py
    result: PASS
    evidence: Nine focused staging, policy, integrity, clock, and deduplication tests passed.
blockers:
  - No 24-hour accepted operational run exists yet.
next_action: Open a draft PR, repair the first repository validation failure, then run one bounded public-endpoint smoke and record its non-secret evidence.
```
