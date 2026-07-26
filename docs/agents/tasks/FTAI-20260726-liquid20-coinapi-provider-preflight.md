---
task_id: FTAI-20260726-liquid20-coinapi-provider-preflight
status: in_progress
branch: feat/liquid20-coinapi-provider-preflight
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: "#349"
owned_paths:
  - docs/ai_platform/LIQUID20_COINAPI_PROVIDER_PREFLIGHT.md
  - ai_platform/research/liquidations/historical/liquid20-coinapi-provider-preflight-v1.json
  - ai_platform/research/liquidations/historical/coinapi-provider-preflight-v1.schema.json
  - tests/ai_platform_integration/test_liquidation_historical_coinapi_preflight.py
  - docs/agents/tasks/FTAI-20260726-liquid20-coinapi-provider-preflight.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
  - docs/agents/tasks/FTAI-20260726-liquid20-historical-ai-training.md
search_first:
  - current develop HEAD, PR 349 and exact-head CI
  - current CoinAPI Metrics V1 historical and metadata contracts
optional_reads: []
---

# Liquid20 CoinAPI Provider Preflight

## Goal

Determine whether CoinAPI can replace the selected Tardis event-level liquidation history source for Bybit and Binance Futures without purchasing access, exposing credentials, weakening timestamp provenance, or changing the historical training programme.

## Result

CoinAPI is rejected as a Tardis event-level replacement because its documented historical symbol metrics are bucketed series and omit historical provider receive time and event identity. It remains a conditional aggregate-feature candidate under a separate future work package.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T09:40:00Z
head: 6f2869ab27ad0a25813778121156402211fd428b
branch: feat/liquid20-coinapi-provider-preflight
pr: "#349"
status: in_progress
context_routes:
  - docs/ai_platform/LIQUID20_COINAPI_PROVIDER_PREFLIGHT.md
  - ai_platform/research/liquidations/historical/liquid20-coinapi-provider-preflight-v1.json
  - docs/ai_platform/LIQUID20_HISTORICAL_PROVIDER_PREFLIGHT.md
owned_paths:
  - docs/ai_platform/LIQUID20_COINAPI_PROVIDER_PREFLIGHT.md
  - ai_platform/research/liquidations/historical/liquid20-coinapi-provider-preflight-v1.json
  - ai_platform/research/liquidations/historical/coinapi-provider-preflight-v1.schema.json
  - tests/ai_platform_integration/test_liquidation_historical_coinapi_preflight.py
  - docs/agents/tasks/FTAI-20260726-liquid20-coinapi-provider-preflight.md
proven:
  - CoinAPI documents liquidation metric families for BYBIT and BINANCEFTS.
  - The Metrics V1 historical symbol endpoint requires authentication, defaults to 1SEC buckets and returns first/last/min/max/count/sum bucket fields.
  - The historical response contract omits entry_time, recv_time and an event identifier; the current endpoint documents entry_time and recv_time separately.
  - Public sample placeholder probe returned HTTP 401 JSON error in workflow run 30196686123 job 89779333914 and emitted no raw records.
  - No private credential, purchase, bulk download, importer, training, backtest, live collector change or protected-holdout access occurred.
derived:
  - Separate historical metric series cannot be represented as joined liquidation events without fabricating identity or pairings.
  - Historical provider availability time cannot be reconstructed from bucket boundaries.
  - CoinAPI cannot replace Tardis for the first event-level import.
  - CoinAPI may only be evaluated later as an aggregate completed-interval feature source with separate acceptance and licensing.
unknown:
  - Exact authenticated live metric listing for all four target symbols.
  - Earliest available history for each target symbol.
  - Exact CoinAPI license, retention, redistribution and cost terms for this request.
conflicts: []
first_failure:
  marker: historical-event-provenance-contract-mismatch
  evidence: CoinAPI historical metrics are bucketed and omit provider receive time and event identity required by Liquid20 event replay.
rejected_hypotheses:
  - Treat separate price, quantity, side, symbol and time metric buckets as one event stream.
  - Populate provider_captured_at_ms from time_period_start, time_open or time_close.
  - Use the documented public sample placeholder as an active API key.
  - Buy CoinAPI before proving that an aggregate-feature work package is needed.
changed_paths:
  - docs/ai_platform/LIQUID20_COINAPI_PROVIDER_PREFLIGHT.md
  - ai_platform/research/liquidations/historical/liquid20-coinapi-provider-preflight-v1.json
  - ai_platform/research/liquidations/historical/coinapi-provider-preflight-v1.schema.json
  - tests/ai_platform_integration/test_liquidation_historical_coinapi_preflight.py
  - docs/agents/tasks/FTAI-20260726-liquid20-coinapi-provider-preflight.md
validation:
  - command: GitHub Actions CoinAPI public sample probe
    result: PASS
    evidence: Run 30196686123 job 89779333914 returned HTTP 401 with a JSON error object and no raw market records.
  - command: Draft 2020-12 schema construction and contract validation
    result: PASS
    evidence: The CoinAPI preflight contract validates against coinapi-provider-preflight-v1.schema.json.
blockers: []
next_action: Remove the temporary diagnostic workflow, run exact-head repository validation, and merge PR 349 if CI and review are clean.
```
