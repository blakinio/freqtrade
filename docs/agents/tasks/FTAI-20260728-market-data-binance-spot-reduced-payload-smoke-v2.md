---
task_id: FTAI-20260728-market-data-binance-spot-reduced-payload-smoke-v2
status: validating
branch: feat/binance-spot-reduced-payload-smoke-v2
base_branch: develop
created: 2026-07-28
updated: 2026-07-28
owned_paths:
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - ai_platform/market_data/binance-spot-instrument-smoke-policy-v2.json
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke.py
  - tests/ai_platform_integration/test_market_data_binance_spot_smoke_request_headers.py
  - tests/ai_platform_integration/test_market_data_binance_spot_instrument_smoke_selfhosted_workflow.py
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - docs/agents/tasks/FTAI-20260728-market-data-binance-spot-reduced-payload-smoke-v2.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE_SELFHOSTED.md
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - ai_platform/market_data/instrument_adapters.py
  - .github/workflows/ai-platform-binance-spot-instrument-smoke-selfhosted.yml
search_first:
  - current develop and open Binance Spot smoke ownership
optional_reads: []
---

# Binance Spot reduced-payload smoke v2

## Goal

Add a separately reviewed reduced-payload Binance Spot smoke contract that keeps the frozen 16 MiB limit and all safety boundaries, persists deterministic failure evidence, and permits one new exact-one-file self-hosted trigger only after exact-head CI and a no-request proof.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-28T13:31:00+02:00
base_develop: fda21a72ea8e4cd3f70623e2bd44bddea5b32683
branch: feat/binance-spot-reduced-payload-smoke-v2
status: validating
proven:
  - Previous v1 self-hosted workflow 30345196797 job 90229653635 executed exactly one public request on freqtrade-synology-staging.
  - The v1 request reached the canonical Binance Spot exchangeInfo endpoint and failed closed with RuntimeError response exceeds max_response_bytes.
  - No retry or rerun occurred, no normalized instrument catalog was accepted and source_acceptance remained false.
  - Binance official REST documentation defines optional showPermissionSets and states that it controls whether permissionSets is populated.
  - Binance official changelog states showPermissionSets may be used for reduced payload size.
  - The repository Binance Spot parser does not consume permissionSets; it consumes symbol, status, baseAsset, quoteAsset, PRICE_FILTER.tickSize and LOT_SIZE.stepSize.
  - Initial AI Platform functional tests and documentation build passed at 2bac9276508db2d198aa36e13eaec9e104659539; only Ruff and pre-commit formatting required repair.
  - Temporary formatter PR 612 workflow 30354894301 verified exact head 2bac9276508db2d198aa36e13eaec9e104659539, changed only the runtime module and focused smoke test, passed Ruff check and format, and fast-forwarded PR 609 to 37f92f3f0b0ddfab7feb49e8540a6df05ec0cb0b.
  - PR 612 was closed without merge and its branch was reset to current develop.
changes:
  - Preserve the v1 request and policy contract for compatibility.
  - Add policy and request contract v2 with exact URL https://api.binance.com/api/v3/exchangeInfo?showPermissionSets=false.
  - Keep timeout 20 seconds, maximum response 16 MiB, redirects false, retries zero and source_acceptance false.
  - Route the exact-one-file self-hosted trigger through the v2 policy and v2 request path.
  - Persist request, policy, failure-report and checksums on transport, header, body, decode or parser failure.
  - Record declared or observed response size when available without persisting a partial oversized payload.
validation_required:
  - Focused synthetic v1 and v2 contract tests.
  - Exact URL and Accept header test with an injected opener and no network.
  - Oversized-response failure evidence test.
  - Self-hosted workflow static safety tests.
  - Exact-head AI Platform CI, Freqtrade CI and zizmor.
  - No-request setup and request-contract proof on the approved runner after merge.
  - One fresh exact-one-file v2 trigger, then close without merge after terminal evidence.
rejected:
  - Raise max_response_bytes before testing the official reduced-payload parameter.
  - Retry or rerun workflow 30345196797.
  - Change endpoint host, use a proxy or VPN, change runner region or introduce credentials.
  - Persist an incomplete oversized body as a valid raw response.
  - Grant source acceptance, collector authority, WebSocket access, order capability or live-capital authority.
blockers:
  - Fresh exact-head CI and review are pending at the post-Ruff head.
next_action: Complete fresh exact-head CI and guarded merge, run one no-request v2 contract proof, then create exactly one canonical v2 trigger and record its terminal artifact while keeping source_acceptance false.
```
