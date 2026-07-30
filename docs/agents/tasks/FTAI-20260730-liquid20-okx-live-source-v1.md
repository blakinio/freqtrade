---
task_id: FTAI-20260730-liquid20-okx-live-source-v1
status: awaiting_final_ci
branch: feat/liquid20-okx-live-source-20260730
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 761
owned_paths:
  - .github/workflows/liquidations-live-synology.yml
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/scripts/liquidation_live_stream_okx.py
  - ai_platform/scripts/liquidation_operational_health.py
  - ai_platform/portal/web/lib/liquidations/contracts.ts
  - ai_platform/portal/web/lib/liquidations/reader.ts
  - ai_platform/portal/web/lib/liquidations/live-reader.ts
  - ai_platform/portal/web/components/liquidations-live-dashboard.tsx
  - ai_platform/portal/web/e2e/liquidation-live-read-model.spec.ts
  - ai_platform/portal/web/e2e/liquidation-okx-live-read-model.spec.ts
  - ai_platform/portal/web/e2e/specs/market/liquidations.spec.ts
  - deploy/synology/liquid20/LIVE_STREAM.md
  - deploy/synology/liquid20/OKX_LIVE_SOURCE.md
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/live-entrypoint.sh
  - deploy/synology/liquid20/verify-okx-live.sh
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - tests/ai_platform_integration/test_liquidation_okx_deploy_contract.py
  - tests/ai_platform_integration/test_liquidation_okx_live_safety.py
  - tests/ai_platform_integration/test_liquidation_okx_live_source.py
  - tests/ai_platform_integration/test_liquidation_okx_operational_health.py
  - tests/ai_platform_integration/test_liquidation_okx_source.py
  - tests/ai_platform_integration/test_liquidation_okx_startup_gate.py
  - docs/agents/tasks/FTAI-20260730-liquid20-okx-live-source-v1.md
---

# Promote accepted OKX public liquidations into Liquid20 live and Portal

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T11:54:00+02:00
head_before_checkpoint: a64feab001bd8e7a0c9d28afdf83a10369457cd1
branch: feat/liquid20-okx-live-source-20260730
pr: 761
status: awaiting_final_ci
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260728-liquidation-okx-shadow-acceptance-python3-bootstrap-v1.md
  - deploy/synology/liquid20/LIVE_STREAM.md
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
  - ai_platform/scripts/liquidation_live_stream.py
  - ai_platform/scripts/liquidation_live_stream_okx.py
  - ai_platform/research/liquidations/okx.py
  - ai_platform/scripts/liquidation_okx_collector.py
  - ai_platform/portal/web/lib/liquidations/contracts.ts
  - ai_platform/portal/web/lib/liquidations/reader.ts
  - ai_platform/portal/web/lib/liquidations/live-reader.ts
  - ai_platform/portal/web/components/liquidations-live-dashboard.tsx
  - deploy/synology/liquid20/deploy-live.sh
  - ai_platform/scripts/liquidation_live_health.py
  - ai_platform/scripts/liquidation_portal_health.py
owned_paths:
  - .github/workflows/liquidations-live-synology.yml
  - ai_platform/research/liquidations/source-catalog-v1.json
  - ai_platform/scripts/liquidation_live_stream_okx.py
  - ai_platform/scripts/liquidation_operational_health.py
  - ai_platform/portal/web/lib/liquidations/contracts.ts
  - ai_platform/portal/web/lib/liquidations/reader.ts
  - ai_platform/portal/web/lib/liquidations/live-reader.ts
  - ai_platform/portal/web/components/liquidations-live-dashboard.tsx
  - ai_platform/portal/web/e2e/liquidation-live-read-model.spec.ts
  - ai_platform/portal/web/e2e/liquidation-okx-live-read-model.spec.ts
  - ai_platform/portal/web/e2e/specs/market/liquidations.spec.ts
  - deploy/synology/liquid20/LIVE_STREAM.md
  - deploy/synology/liquid20/OKX_LIVE_SOURCE.md
  - deploy/synology/liquid20/deploy-live.sh
  - deploy/synology/liquid20/live-entrypoint.sh
  - deploy/synology/liquid20/verify-okx-live.sh
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
  - tests/ai_platform_integration/test_liquidation_binance_source.py
  - tests/ai_platform_integration/test_liquidation_okx_deploy_contract.py
  - tests/ai_platform_integration/test_liquidation_okx_live_safety.py
  - tests/ai_platform_integration/test_liquidation_okx_live_source.py
  - tests/ai_platform_integration/test_liquidation_okx_operational_health.py
  - tests/ai_platform_integration/test_liquidation_okx_source.py
  - tests/ai_platform_integration/test_liquidation_okx_startup_gate.py
  - docs/agents/tasks/FTAI-20260730-liquid20-okx-live-source-v1.md
proven:
  - Terminal OKX acceptance remains the immutable evidence from trigger head 2a6accbf6b6c21233d897c4ab419debd0aec72a6, workflow 30358400049, job 90271896559, artifact 8723546610 and merged checkpoint 436d2934e120dacf64c81d594059e37667eebcac; it was not rerun or reused.
  - The runtime uses the accepted public OKX parser and verified ctVal instrument contract, with no duplicate parser or substitute public contract.
  - OKX uses only the public liquidation-orders WebSocket and public SWAP instrument snapshot; runtime and container entrypoint refuse OKX credentials.
  - Source-separated okx-swap NDJSON, summary and instrument snapshot files are append-only within a new live run; accepted historical archives are not rewritten.
  - Live state serializes configured, connected, event and receive timestamps, source heartbeat, ingest lag, reconnect/error/parse-error counts, observed/subscribed symbols and events written for all three sources.
  - Live state and OKX summaries require execution_enabled=false, trading_authorized=false, trading_credentials_present=false and orders_submitted=0.
  - Initial readiness requires connection of bybit-linear, binance-usdm and okx-swap; subsequent single-source failures preserve the independent state of the other two sources.
  - Portal extends the existing same-origin BFF, existing read model and existing dashboard; browser code has no direct OKX, collector or Synology network path.
  - Portal source health distinguishes connected transport from healthy data. Missing configuration, stale heartbeat or stale per-source receive time degrades the source and overall live mode.
  - A legacy live state with okx-swap configured=false cannot be reported as live or healthy and is covered for health, list and summary responses.
  - UI labels stale but connected source data as DEGRADED rather than LIVE, while retaining the factual connected transport state.
  - Operational health extends the existing alert mechanism and requires configured/connected/subscribed/fresh heartbeat for all three sources, plus write, receive freshness, parse-error, reconnect and Portal drift checks.
  - Synology retains the persistent data root, non-root runtime, read-only container root, existing restart policies, no Docker socket in Portal, exact-image rollback and accepted-evidence digest checks.
  - Baseline repair PR 766 passed exact-head AI Platform, Portal Web, Portal E2E, WickHunter, security and full Freqtrade CI and merged normally as ac545041046e618c477e0ab5d999e11d261a742e.
  - The feature branch was synchronized normally with develop through PR 772; compare status is ahead with behind_by=0 and only OKX/Liquid20/Portal paths remain in PR 761.
  - PR 761 is open, mergeable and has no submitted reviews or unresolved review threads at this checkpoint.
derived:
  - The smallest complete implementation is an OKX live adapter around accepted parser evidence plus extensions to existing Liquid20 and Portal contracts, not a parallel collector contract or alternate API.
  - Per-source healthy must be stricter than connected: configured, connected, fresh source heartbeat and fresh source receive time are all required.
  - A failure of OKX degrades the overall collector view without rewriting or falsely degrading the factual source state of Binance or Bybit.
unknown:
  - Exact required CI outcome for the checkpoint commit and any later synchronization commit until all pull-request checks complete.
  - Exact Synology production runtime outcome until PR 761 is merged and the separate controlled deployment and verification step executes.
conflicts: []
first_failure:
  marker: LOCAL_GIT_CLONE_DNS_UNAVAILABLE
  evidence: The sandbox could not resolve github.com, so authoritative repository reads, writes, PR state and CI evidence use the connected GitHub API.
rejected_hypotheses:
  - Rerun or reuse the consumed OKX acceptance workflow, request ID or run ID.
  - Add OKX credentials, account endpoints, order routes, replay, model training, strategy research or live-capital authority.
  - Modify accepted OKX archives or Binance acceptance workflows.
  - Connect the browser directly to OKX, the collector or Synology.
  - Dispatch a production or acceptance workflow from the feature branch.
validation:
  - command: baseline exact-head CI for PR 766 at dd8595fe7a2d3559340d46d9c2b43e05aabbd0e0
    result: PASS
    evidence: AI Platform CI, Portal Web CI, Portal Universal E2E, dedicated WickHunter CI, security analysis and full Freqtrade CI including CI Gate completed successfully before merge.
  - command: intermediate Portal typecheck, lint, production build and critical E2E
    result: PASS
    evidence: The in-place three-source read model and unconfigured-source fail-closed regression passed TypeScript validation and backend/Chromium E2E before the final per-source healthy extension.
  - command: structural source and deployment review
    result: PASS
    evidence: The final diff contains only 25 OKX/Liquid20/Portal paths, no WickHunter paths, no alternate API, no credentials and no production dispatch.
  - command: real exchange connections
    result: NOT_RUN
    evidence: Tests remain network-free and the terminal OKX acceptance is intentionally not rerun.
  - command: production deployment/workflow
    result: NOT_RUN
    evidence: PR 761 is not merged to develop.
  - command: repository CI for final checkpoint head
    result: PENDING
    evidence: The checkpoint commit must complete normal pull-request validation before merge.
blockers:
  - Final exact-head pull-request CI has not completed.
next_action: Inspect every exact-head PR 761 check and review thread, repair only scoped failures, and merge normally only when required CI is fully green and the branch remains synchronized with develop; do not dispatch acceptance or production workflows.
```
