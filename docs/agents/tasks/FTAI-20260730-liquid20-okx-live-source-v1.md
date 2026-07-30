---
task_id: FTAI-20260730-liquid20-okx-live-source-v1
status: awaiting_ci
branch: feat/liquid20-okx-live-source-20260730
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 761
owned_paths:
  - .github/workflows/liquidations-live-synology.yml
  - ai_platform/scripts/liquidation_live_stream_okx.py
  - ai_platform/scripts/liquidation_operational_health.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/portal/web/lib/liquidations/okx-live-reader.ts
  - ai_platform/portal/web/lib/liquidations/index.ts
  - ai_platform/portal/web/app/api/market/liquidations/_shared.ts
  - ai_platform/portal/web/components/liquidations-live-dashboard.tsx
  - ai_platform/portal/web/e2e/liquidation-okx-live-read-model.spec.ts
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/live-entrypoint.sh
  - deploy/synology/liquid20/verify-okx-live.sh
  - deploy/synology/liquid20/OKX_LIVE_SOURCE.md
  - tests/ai_platform_integration/test_liquidation_okx_source.py
  - tests/ai_platform_integration/test_liquidation_okx_live_source.py
  - tests/ai_platform_integration/test_liquidation_okx_live_safety.py
  - tests/ai_platform_integration/test_liquidation_okx_startup_gate.py
  - tests/ai_platform_integration/test_liquidation_okx_operational_health.py
  - tests/ai_platform_integration/test_liquidation_okx_deploy_contract.py
  - docs/agents/tasks/FTAI-20260730-liquid20-okx-live-source-v1.md
---

# Promote accepted OKX public liquidations into Liquid20 live and Portal

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T11:15:00+02:00
head_before_checkpoint: 6b746073b3066700180ce049b6f33dae651faf90
branch: feat/liquid20-okx-live-source-20260730
pr: 761
status: awaiting_ci
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
  - ai_platform/portal/web/lib/liquidations/reader.ts
  - ai_platform/portal/web/app/api/market/liquidations/_shared.ts
  - ai_platform/portal/web/components/liquidations-live-dashboard.tsx
  - deploy/synology/liquid20/deploy-live.sh
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_portal_health.py
owned_paths:
  - .github/workflows/liquidations-live-synology.yml
  - ai_platform/scripts/liquidation_live_stream_okx.py
  - ai_platform/scripts/liquidation_operational_health.py
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/portal/web/lib/liquidations/okx-live-reader.ts
  - ai_platform/portal/web/lib/liquidations/index.ts
  - ai_platform/portal/web/app/api/market/liquidations/_shared.ts
  - ai_platform/portal/web/components/liquidations-live-dashboard.tsx
  - ai_platform/portal/web/e2e/liquidation-okx-live-read-model.spec.ts
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/live-entrypoint.sh
  - deploy/synology/liquid20/verify-okx-live.sh
  - deploy/synology/liquid20/OKX_LIVE_SOURCE.md
  - tests/ai_platform_integration/test_liquidation_okx_source.py
  - tests/ai_platform_integration/test_liquidation_okx_live_source.py
  - tests/ai_platform_integration/test_liquidation_okx_live_safety.py
  - tests/ai_platform_integration/test_liquidation_okx_startup_gate.py
  - tests/ai_platform_integration/test_liquidation_okx_operational_health.py
  - tests/ai_platform_integration/test_liquidation_okx_deploy_contract.py
  - docs/agents/tasks/FTAI-20260730-liquid20-okx-live-source-v1.md
proven:
  - Work started from exact develop SHA 7240762e134d8db42b83030491ae52ec0d02cad6; the branch is not behind develop.
  - Open pull-request searches found no competing OKX Liquid20 or Portal implementation; WickHunter PR 753 explicitly excludes active Liquid20 collector and Portal changes.
  - Existing OKX implementation from PR 339 provides the public WebSocket channel, public instrument snapshot, parser, ctVal conversion, side normalization, heartbeat/reconnect and data-only safeguards.
  - Terminal acceptance used exact trigger head 2a6accbf6b6c21233d897c4ab419debd0aec72a6 in workflow 30358400049 job 90271896559 and completed accepted after approximately 86400 seconds with 1352 events, zero parse failures and zero failed gates.
  - Terminal evidence artifact 8723546610 and checkpoint were merged by PR 714 as commit 436d2934e120dacf64c81d594059e37667eebcac.
  - The active implementation reuses the accepted OKX parser and public ctVal contract, writes separate okx-swap NDJSON, summary and instrument snapshot files, and exposes source-isolated state without changing Binance or Bybit parsers.
  - The live state and OKX summary serialize execution_enabled=false, trading_authorized=false, trading_credentials_present=false and orders_submitted=0.
  - Direct runtime and container entrypoint refuse OKX credentials.
  - Portal browser code calls only same-origin liquidation BFF endpoints and contains no OKX WebSocket or public instruments endpoint.
  - The existing liquidation dashboard is extended in place; the temporary duplicate UI component was removed.
  - The existing health and GitHub issue mechanism is extended rather than replaced.
  - Synology candidate and production readiness now explicitly require configured, connected, non-empty subscriptions for bybit-linear, binance-usdm and okx-swap.
  - The deploy script observes all three NDJSON files and retains exact-image rollback, accepted-evidence digest verification, non-root runtime, read-only root filesystem, existing restart policy and no Docker socket.
  - PR 761 is open, mergeable and has no review submissions or unresolved review threads.
derived:
  - The minimal complete runtime boundary is a dedicated live adapter around the accepted parser plus the existing BFF/read-only mount, not a duplicate parser or alternate browser API.
  - A previous live state with okx-swap configured=false is completed on restart and replaced by a new append-only run with OKX configured=true; accepted historical runs are not modified.
  - A single-source failure degrades the overall live mode while preserving the independent Binance and Bybit source state.
unknown:
  - Exact required CI outcome for the final branch head until pull-request checks run.
  - Exact Synology production runtime outcome until the reviewed implementation is merged and the separate controlled deployment step executes.
conflicts: []
first_failure:
  marker: LOCAL_GIT_CLONE_DNS_UNAVAILABLE
  evidence: The sandbox could not resolve github.com, so repository reads and writes use the connected GitHub API; local validation is limited to reconstructed changed files and deterministic syntax/contract checks.
rejected_hypotheses:
  - Rerun or reuse OKX terminal acceptance workflow, request ID or run ID.
  - Add OKX credentials, account endpoints, order routes, replay, model training, strategy research or live-capital authority.
  - Modify accepted OKX archives or Binance acceptance workflows.
  - Connect the browser directly to OKX, the collector or Synology.
  - Dispatch the develop-only Synology workflow from the feature branch.
validation:
  - command: python py_compile on reconstructed changed Python runtime, health and tests
    result: PASS
    evidence: Reconstructed branch files compiled without syntax errors in the sandbox before the final health-test additions.
  - command: bash/sh syntax checks for live entrypoint and bounded OKX verification
    result: PASS
    evidence: Shell parsers accepted both scripts; the deploy-live.sh PR patch contains only three bounded tuple extensions for OKX.
  - command: JSON validation for source-catalog-v1.json
    result: PASS
    evidence: Python json.tool parsed the updated catalog.
  - command: isolated TypeScript strict check for okx-live-reader.ts with bounded local stubs
    result: PASS
    evidence: The new BFF read model passed the isolated strict TypeScript check before final UI test updates.
  - command: real exchange connections
    result: NOT_RUN
    evidence: Tests are intentionally network-free and terminal OKX acceptance is not rerun.
  - command: production deployment/workflow
    result: NOT_RUN
    evidence: The exact implementation is not merged to develop.
  - command: repository CI
    result: PENDING
    evidence: PR 761 remains draft until the implementation checkpoint is complete.
blockers:
  - Repository CI has not run for the final head.
next_action: Mark PR 761 ready for review to trigger normal pull-request checks, inspect every job and review thread, fix failures without dispatching acceptance or production workflows, and leave the PR unmerged unless all required checks are green.
```
