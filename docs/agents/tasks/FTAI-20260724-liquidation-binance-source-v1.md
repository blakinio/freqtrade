---
task_id: FTAI-20260724-liquidation-binance-source-v1
status: blocked
branch: develop
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "#250"
owned_paths:
  - ai_platform/research/liquidations/binance.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/research/liquidations/evidence/binance-smoke-github-us-20260724-v1.json
  - ai_platform/scripts/liquidation_binance_collector.py
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-binance-source-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
---

# Binance Liquidation Source v1

## Goal

Add Binance USD-M Futures as a second public liquidation source without changing the frozen Bybit staging policy,
enabling execution, merging unlike feed semantics, or making a profitability claim.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T10:57:00Z
head: 767b4f570c5cffca34e0ba0ebfa7284a95cd1da5
branch: develop
pr: "#250"
status: blocked
context_routes:
  - docs/ai_platform/LIQUIDATION_DATA_ONLY_STAGING.md
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
owned_paths:
  - ai_platform/research/liquidations/binance.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/research/liquidations/evidence/binance-smoke-github-us-20260724-v1.json
  - ai_platform/scripts/liquidation_binance_collector.py
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-binance-source-v1.md
proven:
  - Bybit Stage 1 collection and its frozen policy remain unchanged.
  - Binance documents the public USD-M forceOrder stream, live subscription protocol, and one-second sampled publication semantics.
  - The canonical event contract includes source identity and source-scoped deterministic event IDs.
  - PR #250 merged to develop as 767b4f570c5cffca34e0ba0ebfa7284a95cd1da5.
  - The merged package provides a Binance parser, bounded public collector, clock probe, source catalog, focused tests, immutable evidence, and a multi-source runbook.
  - Final candidate 04cfeac6b85747ad1e2cb9bc377e6b7e6818b1cf passed AI Platform CI runs 30087228832 and 30087519876.
  - Final candidate passed zizmor runs 30087228839 and 30087519963.
  - The final implementation diff contained exactly seven intended files and no temporary workflow.
  - The only security review thread concerned a deleted diagnostic workflow and was resolved as outdated.
  - GitHub-hosted smoke run 30086906301 connected to Binance USD-M WebSocket for 35.269 seconds, received subscription acknowledgement and one liquidation event, wrote one canonical record, and recorded zero disconnects and zero parser failures.
  - The smoke generated a non-empty immutable output hash and detected no trading credential environment.
  - Clock diagnostic run 30087047452 observed HTTP 451 from the public Binance futures server-time endpoint on a United States-hosted runner.
  - The failed clock gate is preserved in machine-readable evidence and was not removed or weakened after observation.
derived:
  - Binance provides a useful second venue observation but cannot be treated as a complete liquidation-volume feed.
  - Cross-exchange events must not be deduplicated because they are venue-specific observations.
  - Bybit and Binance collectors must retain separate immutable files and summaries.
  - The Binance WebSocket parser and canonical write path work, while authoritative clock evidence must be obtained on the intended non-restricted staging host.
unknown:
  - Public endpoint smoke result from the intended non-restricted host.
  - Source-specific multi-source 24-hour operational evidence.
conflicts: []
first_failure:
  marker: binance-rest-us-451
  evidence: GitHub Actions run 30087047452 received HTTP 451 from https://fapi.binance.com/fapi/v1/time while the public liquidation WebSocket remained reachable and delivered an event.
rejected_hypotheses:
  - Treat Binance forceOrder as a complete all-liquidation stream.
  - Sum Bybit and Binance notional values without source labels or declared normalization.
  - Modify the frozen Bybit data-only-staging-policy-v1 after observing evidence.
  - Remove or weaken clock synchronization after the United States-hosted failure.
  - Enable strategy execution, DCA, leverage, or live capital in this source-adapter package.
changed_paths:
  - ai_platform/research/liquidations/binance.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/research/liquidations/evidence/binance-smoke-github-us-20260724-v1.json
  - ai_platform/scripts/liquidation_binance_collector.py
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - docs/ai_platform/LIQUIDATION_MULTI_SOURCE.md
  - docs/agents/tasks/FTAI-20260724-liquidation-binance-source-v1.md
validation:
  - command: AI Platform CI run 30087228832
    result: PASS
    evidence: Compile, all AI-platform tests, Ruff, formatting, codespell, and JSON validation passed on the final candidate.
  - command: AI Platform CI run 30087519876
    result: PASS
    evidence: Independent validation of the same final candidate passed.
  - command: GitHub Actions Security Analysis runs 30087228839 and 30087519963
    result: PASS
    evidence: Zizmor completed successfully for the exact final candidate.
  - command: Binance public smoke run 30086906301
    result: BLOCKED
    evidence: WebSocket transport and one real canonical event passed; only the mandatory clock check remained unknown.
  - command: Binance clock diagnostic run 30087047452
    result: BLOCKED
    evidence: The United States-hosted runner received HTTP 451 from the public Binance futures clock endpoint.
blockers:
  - The unchanged Binance smoke has not passed on the intended non-restricted staging host.
  - No source-specific multi-source 24-hour accepted run exists yet.
next_action: Run the unchanged Binance smoke and a separately declared multi-source acceptance run on the intended non-restricted always-on staging host.
```
