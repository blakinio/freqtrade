---
task_id: FTAI-20260802-portal-pi08-runtime-composition-closure
status: ready
branch: unassigned
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
parent_task: FTAI-20260802-portal-end-to-end-completeness-audit
owned_paths:
  - ai_platform/portal/control_plane/
  - ai_platform/portal/execution/
  - ai_platform/portal/execution_submission/
  - ai_platform/portal/risk/
  - tests/ai_platform/portal/execution_submission/
  - tests/ai_platform/portal/risk/
  - tests/ai_platform_integration/
  - docs/agents/tasks/FTAI-20260802-portal-pi08-runtime-composition-closure.md
---

# Portal PI-08 trusted runtime composition closure

## Proven gap

The repository contains and tests:

- `PrivateDryRunApprovedIntentSubmitter`;
- `PrivateSubmissionExecutionAdapter`;
- private dry-run submission persistence, transport and reconciliation contracts.

A repository-wide exact-head search found no product runtime construction of either component and no `execution_submitter=` injection outside focused tests. The default `ExecutionAdapter.submit_approved_intent()` and `TerminalService` submitter therefore remain fail-closed with `ORDER_SUBMISSION_NOT_IMPLEMENTED` when the canonical app is assembled without explicit overrides.

This means PI-08 is implemented as reusable backend components but not proven as a complete product runtime vertical slice.

## Objective

Add one canonical, fail-closed, server-side composition root that assembles risk snapshots, credentials, private dry-run transport, durable submission reservation, reconciliation and terminal/execution services without exposing a private Freqtrade route to the browser.

## Required scope

- define one runtime configuration contract for the private dry-run target and approved credential reference;
- construct the existing private execution adapter, PI-08 submitter and risk snapshot provider in a trusted server process;
- inject the assembled submitter into `TerminalService` and the composed execution adapter used by bot operations;
- refuse startup or return explicit unavailable states when credentials, TLS identity, target health or bindings are absent;
- preserve durable reservation before network I/O, idempotent replay protection and acknowledgement-versus-execution separation;
- connect reconciliation evidence back to orders, positions, dashboard, execution activity and audit views;
- keep the browser limited to same-origin BFF/control-plane contracts;
- retain simulation/dry-run only and zero live-capital authority.

## Acceptance inventory

- production-like runtime factory and configuration validation;
- exact tenant/bot/config/runtime/intent binding;
- healthy, unavailable, denied, stale, timeout, rejected, duplicate and reconciliation-pending states;
- focused unit and integration tests for the assembled runtime, not only isolated components;
- API-mode terminal submission test proving the PI-08 implementation is actually selected;
- restart/idempotency and reconciliation tests;
- Chromium proof that the terminal uses the same-origin BFF and never calls Freqtrade directly;
- target acceptance remains separate and requires real private Freqtrade/TLS/Vault evidence;
- no withdrawals, production deployment or live-capital authorization.

## Handover

```yaml
checkpoint_version: 3
status: ready
proven:
  - PI-08 component implementations and focused tests exist
  - no trusted product runtime assembly was found
  - canonical defaults remain intentionally fail-closed
  - browser architecture correctly prevents direct private runtime access
next_action: claim the task and implement one explicit runtime composition root plus API-mode/reconciliation evidence
blockers:
  - real target acceptance remains externally dependent after repository composition is complete
```

```text
secret_values_recorded=false
live_capital_authorized=false
```
