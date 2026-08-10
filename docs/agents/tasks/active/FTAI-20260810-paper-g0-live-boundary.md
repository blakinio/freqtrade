# FTAI-20260810 — PAPER G0 LIVE Boundary Contract

```yaml
task_id: FTAI-20260810-paper-g0-live-boundary
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: safety_contract
phase: implementation
status: implementing
priority: critical
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
delivery_branch: feat/paper-g0-live-boundary-20260810
paper_gate: G0
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Implement G0 work item 6 from `PAPER_PLATFORM_IMPLEMENTATION_PLAN.md`: add fail-closed contract coverage proving that LIVE cannot be selected or reached across the current schema, API, UI, configuration, runtime and promotion boundaries. Repair only evidence-backed gaps found by those tests.

## Acceptance

- schema rejects a user-authored managed LIVE mode rather than allowing it to survive until a later runtime call;
- API requests cannot persist or activate a LIVE managed revision;
- browser/UI does not offer a LIVE operating-mode control or hidden value;
- generated/normalized managed runtime configuration remains Freqtrade dry-run and cannot switch to live execution;
- managed runtime resolution rejects reserved LIVE terminology with a stable fail-closed reason;
- strategy/model/config promotion never grants LIVE, live-capital, real-order, private-trading-credential or automatic-promotion authority;
- tests exercise behavior, not only documentation/source-text grep, with narrowly scoped structural checks only where browser/config surfaces are static artifacts;
- PAPER remains the only authorized operational mode; SHADOW remains optional/purpose-bound; LIVE remains unreachable/fail-closed;
- no protected deployment, exchange credential, real order, withdrawal or live capital is used by validation.

## Initial evidence

- `BotMode` contains reserved `LIVE_BLOCKED`, while `resolve_managed_runtime_mode()` rejects it with `LIVE_CAPITAL_NOT_AUTHORIZED`.
- `RuntimeModeResolution` requires all real-execution authority fields false and `orders_submitted == 0`.
- `ExecutionMode` exposes only `simulated` and `dry_run`.
- Current `BotSpec` and `BotConfigRevision` accept the generic `BotMode` enum without an explicit authored-schema rejection for `LIVE_BLOCKED`; this is the first proven gap to close.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T21:22:00Z
head: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
branch: feat/paper-g0-live-boundary-20260810
pr: none
status: implementing
context_routes:
  - PAPER G0 LIVE fail-closed boundary
  - managed runtime mode schema and activation
  - UI/config/promotion reachability
owned_paths:
  - ai_platform/portal/contracts/bots.py
  - tests/ai_platform/portal/**
  - tests/ai_platform/**
  - ai_platform/portal/web/**
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-live-boundary.md
proven:
  - ADR-022 makes LIVE reserved terminology and unreachable in every mode-setting boundary.
  - ExecutionMode has no live value.
  - Runtime mode resolver rejects LIVE_BLOCKED and produces only SHADOW or PAPER resolutions.
  - BotSpec and BotConfigRevision currently have no authored-schema LIVE_BLOCKED validator.
derived:
  - G0 requires earlier rejection at the schema/API boundary in addition to the existing runtime rejection.
unknown:
  - Exact UI operating-mode options and runtime-config generation boundary still require inventory.
  - Exact promotion surfaces still require inventory.
conflicts: []
first_failure:
  marker: authored BotSpec schema accepts reserved LIVE_BLOCKED
  evidence: ai_platform/portal/contracts/bots.py uses BotMode directly with no LIVE_BLOCKED rejection
rejected_hypotheses:
  - Runtime-only rejection is sufficient; rejected by G0 requirement to fail closed at every reachable boundary.
changed_paths:
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-live-boundary.md
validation:
  - command: runtime/browser E2E
    result: NOT_RUN
    evidence: implementation inventory in progress
blockers: []
next_action: Inventory UI, configuration and promotion boundaries, then implement the smallest complete fail-closed tests and fixes across all six required surfaces.
```
