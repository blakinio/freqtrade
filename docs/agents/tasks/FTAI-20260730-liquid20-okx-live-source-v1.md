---
task_id: FTAI-20260730-liquid20-okx-live-source-v1
status: completed
branch: docs/liquid20-okx-live-source-terminal-20260730
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 761
terminal_pr: 796
implementation_merge: 141e59a3c7da441432b3990a54903e5fcfc935c8
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

## Terminal result

- PR #761 merged normally into `develop` as `141e59a3c7da441432b3990a54903e5fcfc935c8`.
- The persistent Liquid20 runtime now consumes public Binance USD-M, Bybit Linear and OKX SWAP liquidation streams through the existing collector and Portal contracts.
- Exact-head pull-request validation passed before merge, including full Freqtrade CI, AI Platform, Portal Web, Portal Universal E2E and workflow security analysis.
- The existing `develop` push workflows deployed the Portal preview and exact Liquid20 collector image automatically; no manual workflow dispatch was used.
- The terminal operational health run verified the collector and Portal together and automatically reconciled the temporary runner-queue alert.
- The consumed terminal OKX acceptance remained immutable and was not rerun or reused.
- No OKX credentials, account endpoints, order path, replay, model work or live-capital authority were introduced.

## Terminal evidence

- implementation head: `3e889c87aa448041dbb2419558e57f619cbe2352`;
- implementation merge: `141e59a3c7da441432b3990a54903e5fcfc935c8`;
- Freqtrade CI: `30552665100`, including 5,855 passing tests, 94% coverage, distribution build and terminal CI Gate;
- AI Platform CI: `30552665244`;
- Portal Universal E2E: `30552664977`;
- Portal Web CI: `30552665408`;
- workflow security analysis: `30552665311`;
- Portal Synology LAN preview: `30554270880`, success;
- Liquidations Live Synology exact-SHA deployment: `30554270978`, success;
- combined Liquidations health: `30554270996`, success;
- operational artifact: `8764560417`, digest `sha256:0e1a162d74ae4e013a58d49cbca22fefa2df710370a56d3944275b47c6f1b866`;
- operational alert #751: automatically closed as completed after the trusted health job succeeded.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T17:21:00+02:00
head: 141e59a3c7da441432b3990a54903e5fcfc935c8
branch: docs/liquid20-okx-live-source-terminal-20260730
pr: 761
status: completed
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260728-liquidation-okx-shadow-acceptance-python3-bootstrap-v1.md
  - deploy/synology/liquid20/LIVE_STREAM.md
  - deploy/synology/liquid20/OKX_LIVE_SOURCE.md
  - docs/ai_platform/portal/LIQUIDATIONS_LIVE_STREAM_ARCHITECTURE.md
  - ai_platform/scripts/liquidation_live_stream_okx.py
  - ai_platform/scripts/liquidation_operational_health.py
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
  - PR 761 merged normally into develop as 141e59a3c7da441432b3990a54903e5fcfc935c8 from exact implementation head 3e889c87aa448041dbb2419558e57f619cbe2352.
  - Exact-head Freqtrade CI run 30552665100 passed pre-commit, documentation, Python 3.11-3.14 tests, 94 percent coverage, distribution build and terminal CI Gate.
  - AI Platform run 30552665244, Portal E2E run 30552664977, Portal Web run 30552665408 and security run 30552665311 all passed.
  - PR 761 changed only the 25 declared Liquid20, OKX, Portal, Synology, test and task-record paths and had zero submitted reviews or unresolved review threads.
  - Automatic Portal Synology run 30554270880 deployed and verified the LAN preview successfully.
  - Automatic Liquidations Live Synology run 30554270978 validated and deployed exact merge SHA 141e59a3c7da441432b3990a54903e5fcfc935c8 successfully.
  - Deployment artifact 8764560417 records all three sources configured and connected with advancing heartbeats, dynamic subscriptions and production file growth.
  - Production observation recorded 9 Binance, 5 Bybit and 6 OKX events with zero parser, source or reconnect errors during the bounded window.
  - Historical acceptance evidence digest remained unchanged at 4b539c67dc11d263cb8b27ef19b15445cd6d3248d37db0b8ea4ca1b2859b16a3.
  - Combined health run 30554270996 passed collector and Portal verification and published final healthy status.
  - Operational alert 751 was automatically closed as completed after the trusted health check succeeded.
  - Terminal OKX acceptance was not rerun, no credentials were present and trading_authorized remained false.
derived:
  - The repository, deployment and operational verification obligations for this bounded OKX Liquid20 live-source task are complete.
  - Future runtime incidents belong to the existing automated health and alert mechanism rather than this completed implementation task.
unknown: []
conflicts: []
first_failure:
  marker: NONE
  evidence: All implementation, exact-head CI, review, merge, automatic deployment and terminal operational health gates passed.
rejected_hypotheses:
  - Rerun or reuse the consumed terminal OKX acceptance workflow or request identity.
  - Add OKX credentials, account endpoints, order submission, replay, model training or live-capital authority.
  - Connect the browser directly to OKX, the collector or Synology.
  - Manually dispatch production deployment instead of observing the existing develop-triggered workflow.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-liquid20-okx-live-source-v1.md
validation:
  - command: PR 761 exact-head required workflows
    result: PASS
    evidence: Runs 30552665100, 30552665244, 30552664977, 30552665408 and 30552665311 completed successfully on head 3e889c87aa448041dbb2419558e57f619cbe2352.
  - command: PR 761 review-thread and changed-path inspection
    result: PASS
    evidence: Zero reviews, zero unresolved threads and exactly 25 declared scoped paths before merge.
  - command: normal protected merge of PR 761
    result: PASS
    evidence: GitHub merged PR 761 into develop as 141e59a3c7da441432b3990a54903e5fcfc935c8.
  - command: Portal Synology LAN preview run 30554270880
    result: PASS
    evidence: Build, deployment, LAN Liquid20 surface verification and final status all succeeded.
  - command: Liquidations Live Synology run 30554270978
    result: PASS
    evidence: Exact-SHA candidate validation, production replacement, final status and operational artifact upload all succeeded.
  - command: deployment artifact 8764560417 inspection
    result: PASS
    evidence: Three sources connected, heartbeats advanced, all source files grew, errors remained zero, historical digest was unchanged and trading_authorized was false.
  - command: combined Liquidations health run 30554270996
    result: PASS
    evidence: Collector and Portal health reconciliation, final health publication and healthy-result enforcement succeeded; alert 751 closed automatically.
blockers: []
next_action: Continue normal automated Liquid20 health monitoring and open a new bounded task only if a future alert or product requirement provides new evidence.
```
