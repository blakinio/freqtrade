# FTAI-20260803 Liquidations Live health recovery

```yaml
policy_version: 2
prompting_standard_version: 2.1
task_id: FTAI-20260803-liquidations-live-health-recovery
project_lane: freqtrade-operations
phase: closeout
status: completed
execution_mode: github
run_scope: single_task
continuation_policy: terminal
task_completion_policy: archived
user_communication: terminal_only
feature_scope:
  type: infrastructure
  user_facing: false
  backend_required: true
  frontend_required: false
  integration_required: true
  e2e_required: true
  completion_claim: internal_only
base: develop@1c7044e9699727732928dcdf71e0fe4e1a159108
implementation_branch: fix/liquidations-live-health-recovery-20260803
implementation_pull_request: 1164
implementation_head: a45c172f29eb98767a526e5e2e41fa3d004ee9fd
merge_commit: f448657dffedda14b6f8de2bb0584e2fa3cd9b1a
tracking_issue: 1162
incident_issue: 900
invocation_started_at: 2026-08-03T23:08:00+02:00
completed_at: 2026-08-04T00:12:01+02:00
ownership_released: true
```

## Result

Liquidations Live operational monitoring is healthy again. The five-minute health workflow now uses a bounded production-container probe instead of the heavyweight isolated deployment proof, cumulative reconnect counts are evaluated against collector uptime, and the Synology repair workflow can restart the existing stateless portal container once after a failed bounded probe.

No exchange credentials, collector data, trading configuration, model state, live-capital setting or production secret was changed.

## Delivered paths

- `.github/workflows/liquidations-live-operational-health.yml`
- `.github/workflows/repair-synology-autostart.yml`
- `ai_platform/scripts/liquidation_operational_health.py`
- `deploy/synology/portal/probe-liquidations-live-operational.sh`
- `tests/ai_platform_integration/test_liquidation_operational_health.py`
- `tests/ai_platform_integration/test_liquidation_portal_health.py`

## Root cause

- The recurring five-minute check invoked the heavyweight isolated portal proof. On Synology it exceeded its 240-second subprocess budget, emitted no portal report and left an orphan Docker process.
- A later successful portal proof showed that the collector, portal, disk and all three exchange sources were healthy; Issue #900 remained open because a lifetime OKX reconnect count was compared with a fixed absolute threshold.
- The Telegram watchdog state still described a stale monitor after the incident was automatically closed because delivery through Telegram cannot be independently observed through the repository connection.

## Exact-head validation

Validated implementation head: `a45c172f29eb98767a526e5e2e41fa3d004ee9fd`.

- AI Platform CI: PASS — workflow run `30855836920`.
- Freqtrade CI: PASS — workflow run `30855836620`, including pre-commit, documentation build and supported Python jobs.
- GitHub Actions Security Analysis: PASS — workflow run `30855836461`.
- Portal Completeness Audit: PASS — workflow run `30855836556`.
- Review hygiene: PASS — zero unresolved review threads at merge.
- Related PR state: PASS — PR #1164 squash-merged; no duplicate repair PR remains open.

## Independent audit

PASS with no open material findings.

- Scope remained within seven declared monitoring, repair, test and task-record paths.
- Every Docker preflight call is bounded; HTTP probes use explicit abort timeouts; the outer container execution is bounded.
- Portal checks remain fail-closed for non-root execution, read-only Liquid20 mount, absent Docker-socket mount, `restart=always`, page availability and protected health response.
- Collector, disk and exchange-source checks remain fail-closed.
- Recovery permits one portal restart only after a failed local probe and finite re-probes.
- Cumulative reconnect values are normalized by collector uptime; invalid values and rates above the configured hourly budget still alert.

## Post-merge real E2E

PASS on the actual `freqtrade-synology-staging` runner.

Workflow run `30857050533`, job `91830413449`, exact merge commit `f448657dffedda14b6f8de2bb0584e2fa3cd9b1a` proved:

- operational probe PASS;
- `alerts: []`;
- collector container healthy;
- disk healthy at approximately 26.064% used;
- portal mode `live`, page status `200`, protected health status `401` with `SESSION_MISSING`;
- portal UID `1000`, read-only data mount, no Docker socket and restart policy `always`;
- Binance USDM, Bybit Linear and OKX Swap connected and healthy;
- GitHub alert reconciliation action `closed`;
- final `liquidations-live-health` commit status `success`.

Issue #900 was automatically closed at `2026-08-03T22:03:34Z`. Tracking Issue #1162 was automatically closed by PR #1164.

## Notification reconciliation

The repository connection cannot prove receipt of a Telegram recovery message, so no delivery claim is made. After the real health E2E passed and Issue #900 closed, the persisted Telegram incident state was explicitly reconciled to `healthy` with `recovery_delivery_status: not_verified`. This prevents continued reminders for the resolved incident without fabricating a delivery receipt.

## Terminal state

- implementation: complete
- exact-head CI: PASS
- independent audit: PASS
- real Synology E2E: PASS
- incident Issue #900: closed
- tracking Issue #1162: closed
- unresolved review threads: 0
- ownership and leases: released
- next_action: none
