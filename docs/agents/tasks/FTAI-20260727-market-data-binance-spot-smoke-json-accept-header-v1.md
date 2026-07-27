---
task_id: FTAI-20260727-market-data-binance-spot-smoke-json-accept-header-v1
status: validating
branch: fix/binance-smoke-json-accept-header-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: null
owned_paths:
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - tests/ai_platform_integration/test_market_data_binance_spot_smoke_request_headers.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-json-accept-header-v1.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE.md
  - ai_platform/market_data/binance_spot_instrument_smoke.py
search_first:
  - current develop and open Binance Spot smoke ownership
optional_reads: []
---

# Binance Spot smoke JSON Accept header fix v1

## Goal

Correct the public Binance Spot smoke request header from the invalid media type `application/jsoon` to `application/json` and add a focused transport-boundary regression test.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-27T12:15:00+02:00
head: fbceaaeca2f50484758e467266e86605fff3d633
base_develop: 435e58037dd6ca992e4e3f834fc9a07a534c6630
branch: fix/binance-smoke-json-accept-header-v1
pr: null
status: validating
context_routes:
  - docs/ai_platform/market_data/BINANCE_SPOT_INSTRUMENT_SMOKE.md
  - ai_platform/market_data/binance_spot_instrument_smoke.py
owned_paths:
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - tests/ai_platform_integration/test_market_data_binance_spot_smoke_request_headers.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-json-accept-header-v1.md
proven:
  - Develop 435e58037dd6ca992e4e3f834fc9a07a534c6630 contains the merged guarded self-hosted Binance Spot smoke infrastructure.
  - The base collector constructs urllib.request.Request with Accept application/jsoon.
  - Commit 41c10761e245758d67d93ba82cd9b7eb66b045d4 changes exactly that literal to application/json.
  - Existing transport fakes did not inspect the Request object, so the invalid header had no regression coverage.
  - The new focused test captures the actual Request passed to the opener and asserts Accept application/json.
  - No endpoint, timeout, retry, redirect, credential, proxy, evidence, source-acceptance or execution boundary changes.
derived:
  - The fix is safe to validate without network access because the opener is injected and returns a bounded local JSON response.
  - A successful test proves header construction only; it does not prove Binance reachability or source acceptance.
unknown:
  - Exact-head repository CI and review result.
conflicts: []
first_failure:
  marker: invalid-json-accept-media-type
  evidence: _fetch_once used application/jsoon in the Accept header while response validation requires JSON media types.
rejected_hypotheses:
  - Change the Binance endpoint.
  - Add retries, credentials, proxy routing or a network test.
  - Fold the fix into the already merged self-hosted workflow infrastructure.
changed_paths:
  - ai_platform/market_data/binance_spot_instrument_smoke.py
  - tests/ai_platform_integration/test_market_data_binance_spot_smoke_request_headers.py
  - docs/agents/tasks/FTAI-20260727-market-data-binance-spot-smoke-json-accept-header-v1.md
validation:
  - command: commit diff inspection
    result: PASS
    evidence: Runtime diff is exactly application/jsoon to application/json.
  - command: repository exact-head CI
    result: NOT_RUN
    evidence: PR has not opened yet.
blockers: []
next_action: Open the bounded three-file PR, fix only confirmed exact-head CI or review failures, mark the checkpoint ready when green and guarded-squash merge.
```
