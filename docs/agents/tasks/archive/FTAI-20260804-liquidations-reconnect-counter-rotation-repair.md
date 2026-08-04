# FTAI-20260804 Liquidations reconnect counter rotation repair

```yaml
policy_version: 2
prompting_standard_version: 2.1
task_id: FTAI-20260804-liquidations-reconnect-counter-rotation-repair
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
implementation_pull_requests: [1170, 1187]
reconnect_repair_merge: 416223a803c6eb803e09429b3368488276a112e9
watchdog_repair_head: 8926657384595072a9340582c2e4086453deb57a
watchdog_repair_merge: 004bc40ff162905ac702d97efb976807bd82d9f4
tracking_issue: 1168
incident_issues: [1167, 1179]
completed_at: 2026-08-04T18:46:43+02:00
ownership_released: true
```

## Result

Liquidations Live monitoring is healthy and the Telegram alert loop no longer depends on false reconnect-rate or runner-watchdog failures.

The completed repair:

- resets run-scoped reconnect counters with their daily measurement epoch;
- preserves concrete operational incident evidence instead of replacing it with a synthetic stale-monitor diagnosis;
- does not describe monitor freshness as proof that the Synology runner is unavailable;
- transports GitHub jobs and Issues API responses through runner-temp files rather than unbounded environment variables;
- retains bounded fail-closed behavior when the trusted Synology health job genuinely does not start.

No exchange credential, collector data, trading configuration, model state, order authority, execution authority, production secret, or live-capital setting was changed.

## Delivered paths

- `ai_platform/scripts/liquidation_alert_notifications.py`
- `ai_platform/scripts/liquidation_live_stream.py`
- `.github/workflows/liquidations-live-operational-health.yml`
- `tests/ai_platform_integration/test_liquidation_alert_notifications.py`
- `tests/ai_platform_integration/test_liquidation_okx_live_source.py`
- `tests/ai_platform_integration/test_liquidation_live_health_workflow.py`

## Root causes and remediation

1. Daily run rotation reset `collector_started_at_ms` but restored the previous run's cumulative reconnect count. The health calculation divided the old count by the new short uptime and produced a false OKX reconnect-rate alert. PR #1170 aligned the counters with the new measurement epoch.
2. Telegram allowed synthetic scheduler staleness to replace a concrete open operational diagnosis and described monitor staleness as an unavailable runner. PR #1170 preserved the authoritative incident and truthful uncertainty.
3. The runner watchdog passed complete GitHub jobs and open-Issues API responses through `JOBS_JSON` and `ISSUES_JSON`. Run `30898065128` failed with `/usr/bin/python: Argument list too long` although the real Synology health job passed. PR #1187 changed both paths to file-backed parsing and added regression coverage.

## Validation

PR #1170 exact-head validation passed before merge.

PR #1187 final exact head `8926657384595072a9340582c2e4086453deb57a` passed:

- Freqtrade CI: run `30928764167`;
- GitHub Actions Security Analysis: run `30928764721`;
- Portal Completeness Audit: run `30928764600`;
- Portal Schema Integrity: run `30928766274`;
- pre-commit, documentation build, supported Python jobs, distribution build and CI Gate;
- zero unresolved review threads.

## Independent audit

PASS with zero open material findings on the final PR #1187 head.

The audit verified that the final diff remained limited to the operational-health workflow, focused regression coverage and the existing task record; both potentially large GitHub API payloads are file-backed; the watchdog remains bounded and fail-closed; and no credential, trading, model, order, execution or live-capital boundary changed.

## Real Synology E2E

PASS on merge commit `004bc40ff162905ac702d97efb976807bd82d9f4`.

Workflow run `30930417418` proved:

- `Publish Liquidations health control status`: success;
- `Watch freqtrade-staging assignment`: success;
- `Check Synology collector and portal`: success;
- unhealthy-evidence upload was skipped because the combined health result was healthy;
- final health status and enforcement succeeded.

A repository search after the run found no open Issue titled `[liquidations-live] operational health alert`.

## Incident and PR lifecycle

- PR #1170: merged;
- PR #1187: merged;
- Issue #1167: closed after recovery;
- Issue #1168: closed by the implementation repair;
- Issue #1179: closed after monitor recovery;
- unresolved review threads: 0;
- duplicate or superseded open repair PRs: 0.

The repository connection does not prove delivery of an individual Telegram message, so no receipt claim is made. The observable monitoring state and real health path are healthy.

## Terminal state

- implementation: complete
- exact-head CI: PASS
- independent audit: PASS
- real Synology E2E: PASS
- open operational alert Issues: 0
- task archived: true
- ownership and leases: released
- next_action: none
