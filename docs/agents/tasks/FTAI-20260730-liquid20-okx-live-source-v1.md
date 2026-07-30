---
task_id: FTAI-20260730-liquid20-okx-live-source-v1
status: in_progress
branch: feat/liquid20-okx-live-source-20260730
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
owned_paths:
  - ai_platform/scripts/liquidation_live_stream_okx.py
  - ai_platform/scripts/liquidation_operational_health.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/portal/web/lib/liquidations/okx-live-reader.ts
  - ai_platform/portal/web/lib/liquidations/index.ts
  - ai_platform/portal/web/app/api/market/liquidations/_shared.ts
  - ai_platform/portal/web/app/market/liquidations/page.tsx
  - ai_platform/portal/web/components/liquidations-live-dashboard-okx.tsx
  - deploy/synology/liquid20/live-entrypoint.sh
  - deploy/synology/liquid20/verify-okx-live.sh
  - deploy/synology/liquid20/OKX_LIVE_SOURCE.md
  - tests/ai_platform_integration/test_liquidation_okx_source.py
  - tests/ai_platform_integration/test_liquidation_okx_live_source.py
  - docs/agents/tasks/FTAI-20260730-liquid20-okx-live-source-v1.md
---

# Promote accepted OKX public liquidations into Liquid20 live and Portal

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T09:45:00+02:00
head: b956b332d56be522841f0db40d2354410f01bbc4
branch: feat/liquid20-okx-live-source-20260730
pr: null
status: implementing
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260728-liquidation-okx-shadow-acceptance-python3-bootstrap-v1.md
  - deploy/synology/liquid20/LIVE_STREAM.md
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
  - ai_platform/scripts/liquidation_live_stream.py
  - ai_platform/research/liquidations/okx.py
  - ai_platform/scripts/liquidation_okx_collector.py
  - ai_platform/portal/web/lib/liquidations/live-reader.ts
  - ai_platform/portal/web/app/api/market/liquidations/_shared.ts
  - ai_platform/portal/web/components/liquidations-live-dashboard.tsx
  - deploy/synology/liquid20/deploy-live.sh
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_portal_health.py
owned_paths:
  - ai_platform/scripts/liquidation_live_stream_okx.py
  - ai_platform/scripts/liquidation_operational_health.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/portal/web/lib/liquidations/okx-live-reader.ts
  - ai_platform/portal/web/lib/liquidations/index.ts
  - ai_platform/portal/web/app/api/market/liquidations/_shared.ts
  - ai_platform/portal/web/app/market/liquidations/page.tsx
  - ai_platform/portal/web/components/liquidations-live-dashboard-okx.tsx
  - deploy/synology/liquid20/live-entrypoint.sh
  - deploy/synology/liquid20/verify-okx-live.sh
  - deploy/synology/liquid20/OKX_LIVE_SOURCE.md
  - tests/ai_platform_integration/test_liquidation_okx_source.py
  - tests/ai_platform_integration/test_liquidation_okx_live_source.py
  - docs/agents/tasks/FTAI-20260730-liquid20-okx-live-source-v1.md
proven:
  - Work started from exact develop SHA 7240762e134d8db42b83030491ae52ec0d02cad6.
  - Open pull-request search found no competing OKX Liquid20 or Portal implementation; WickHunter PR 753 explicitly excludes active Liquid20 collector and Portal changes.
  - Existing OKX implementation from PR 339 provides the public WebSocket channel, public instrument snapshot, parser, ctVal conversion, side normalization, heartbeat/reconnect and data-only safeguards.
  - Terminal acceptance used exact trigger head 2a6accbf6b6c21233d897c4ab419debd0aec72a6 in workflow 30358400049 job 90271896559 and completed accepted after approximately 86400 seconds with 1352 events, zero parse failures and zero failed gates.
  - Terminal evidence artifact 8723546610 and checkpoint were merged by PR 714 as commit 436d2934e120dacf64c81d594059e37667eebcac.
  - The active implementation reuses the accepted OKX parser and public ctVal contract, writes a separate okx-swap NDJSON and snapshot, and exposes source-isolated state without changing Binance or Bybit parsers.
  - The live state and OKX summary serialize execution_enabled=false, trading_authorized=false, trading_credentials_present=false and orders_submitted=0.
  - Portal browser code continues to call only same-origin liquidation BFF endpoints and contains no OKX WebSocket or public instruments endpoint.
  - The existing health and issue mechanism is extended rather than replaced.
derived:
  - The minimal complete runtime boundary is a dedicated live adapter around the accepted parser plus the existing BFF/read-only mount, not a duplicate parser or alternate API.
  - A previous live state with okx-swap configured=false is completed on restart and replaced by a new append-only run with OKX configured=true; accepted historical runs are not modified.
unknown:
  - Exact required CI outcome for the final branch head until the pull request is opened and checks complete.
  - Exact Synology production runtime outcome until the reviewed implementation is merged and the separate controlled deployment step is executed.
conflicts: []
first_failure:
  marker: LOCAL_GIT_CLONE_DNS_UNAVAILABLE
  evidence: The sandbox could not resolve github.com, so repository reads and writes use the connected GitHub API; local validation is limited to reconstructed changed files and deterministic syntax/contract checks.
rejected_hypotheses:
  - Rerun or reuse OKX terminal acceptance workflow, request ID or run ID.
  - Add OKX credentials, account endpoints, order routes, replay, model training, strategy research or live-capital authority.
  - Modify accepted OKX archives or Binance acceptance workflows.
  - Connect the browser directly to OKX, the collector or Synology.
changed_paths:
  - ai_platform/scripts/liquidation_live_stream_okx.py
  - ai_platform/scripts/liquidation_operational_health.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/portal/web/lib/liquidations/okx-live-reader.ts
  - ai_platform/portal/web/lib/liquidations/index.ts
  - ai_platform/portal/web/app/api/market/liquidations/_shared.ts
  - ai_platform/portal/web/app/market/liquidations/page.tsx
  - ai_platform/portal/web/components/liquidations-live-dashboard-okx.tsx
  - deploy/synology/liquid20/live-entrypoint.sh
  - deploy/synology/liquid20/verify-okx-live.sh
  - deploy/synology/liquid20/OKX_LIVE_SOURCE.md
  - tests/ai_platform_integration/test_liquidation_okx_source.py
  - tests/ai_platform_integration/test_liquidation_okx_live_source.py
  - docs/agents/tasks/FTAI-20260730-liquid20-okx-live-source-v1.md
validation:
  - command: python py_compile on changed Python runtime, health and tests
    result: PASS
    evidence: Reconstructed branch files compiled without syntax errors in the sandbox.
  - command: bash/sh syntax checks for live entrypoint and bounded OKX verification
    result: PASS
    evidence: Shell parsers accepted both scripts.
  - command: JSON validation for source-catalog-v1.json
    result: PASS
    evidence: Python json.tool parsed the updated catalog.
  - command: isolated TypeScript strict check for okx-live-reader.ts with bounded local stubs
    result: PASS
    evidence: The new read model passed the isolated strict TypeScript check.
  - command: real exchange connections
    result: NOT_RUN
    evidence: Tests are intentionally network-free and terminal OKX acceptance is not rerun.
  - command: repository CI
    result: PENDING
    evidence: PR not opened yet.
blockers: []
next_action: Complete deployment preflight and Portal API/UI test coverage, update stale Liquid20 documentation, validate the full branch diff, then open a pull request to develop and inspect CI without dispatching production workflows.
```
