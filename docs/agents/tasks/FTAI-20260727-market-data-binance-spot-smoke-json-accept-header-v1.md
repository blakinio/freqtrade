---
task_id: FTAI-20260727-market-data-binance-spot-smoke-json-accept-header-v1
status: ready
branch: fix/binance-smoke-json-accept-header-v1
base_branch: develop
created: 2026-07-27
updated: 2026-07-27
related_pr: "#453"
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
updated_at: 2026-07-27T12:30:00+02:00
head: 38a03178dbd5ef368a05a2e519a59d91b3b9e7af
base_develop: 435e58037dd6ca992e4e3f834fc9a07a534c6630
branch: fix/binance-smoke-json-accept-header-v1
pr: "#453"
status: ready
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
  - The focused test captures the actual Request passed to the injected opener and asserts Accept application/json without network access.
  - PR 453 contains exactly the runtime literal correction, the focused regression test and this checkpoint.
  - Head 38a03178dbd5ef368a05a2e519a59d91b3b9e7af passed AI Platform CI 30257259211 and zizmor 30257259204.
  - Head 38a03178dbd5ef368a05a2e519a59d91b3b9e7af passed Freqtrade CI 30257259225 including pre-commit, documentation, Python 3.11 through 3.14, coverage, distribution build and CI Gate.
  - No endpoint, timeout, retry, redirect, credential, proxy, evidence, source-acceptance or execution boundary changes.
derived:
  - The fix is safe to validate without network access because the opener is injected and returns a bounded local JSON response.
  - A successful test proves header construction only; it does not prove Binance reachability or source acceptance.
unknown:
  - Final exact-head repository CI and review result after this ready-checkpoint-only update.
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
  - command: AI Platform CI
    result: PASS
    evidence: Run 30257259211 succeeded at 38a03178dbd5ef368a05a2e519a59d91b3b9e7af.
  - command: zizmor
    result: PASS
    evidence: Run 30257259204 succeeded at 38a03178dbd5ef368a05a2e519a59d91b3b9e7af.
  - command: Freqtrade CI
    result: PASS
    evidence: Run 30257259225 succeeded through coverage, distribution build and CI Gate at 38a03178dbd5ef368a05a2e519a59d91b3b9e7af.
  - command: ready-checkpoint exact-head repository CI
    result: NOT_RUN
    evidence: This checkpoint-only update must receive final exact-head CI before merge.
blockers: []
next_action: Run final exact-head repository CI, verify the three-file scope, current develop and review state, then guarded-squash merge PR 453.
```
