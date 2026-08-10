# FTAI-20260810 — PAPER G0 Surface Availability

```yaml
task_id: FTAI-20260810-paper-g0-surface-availability
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: product_guardrail
phase: implementation
status: implementing
priority: high
execution_mode: github_only
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
base_branch: develop
trusted_base_sha: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
delivery_branch: feat/paper-g0-surface-availability-20260810
paper_gate: G0
live_capital_authorized: false
protected_production_deployment_authorized: false
```

## Objective

Implement G0 work item 7: stop advertising navigation entries whose current living portal ledger status is `DISCONNECTED` or `MISSING`. Keep the routes/code available for bounded development and direct test evidence, but hide them from the primary product navigation until their ledger status is intentionally upgraded.

## Acceptance

- primary navigation renders no route whose living navigation ledger final status is `DISCONNECTED` or `MISSING`;
- the hidden route set is machine-readable and version-controlled rather than duplicated ad hoc in JSX;
- deterministic regression compares hidden routes 1:1 with `tools/portal_audit/ledger/navigation.json` unavailable statuses;
- PARTIAL, COMPLETE and EXTERNAL_ACCEPTANCE_REQUIRED navigation surfaces remain visible;
- existing direct route code, BFF/API contracts and fixture/E2E paths are not deleted merely to hide unavailable navigation;
- unavailable status is a product-readiness guard, not an authorization boundary;
- PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.

## Initial evidence

The living navigation ledger currently marks 16 primary-navigation routes `DISCONNECTED` or `MISSING`, including performance/positions, terminal/orders/trades, several bot and AI surfaces, execution/runtime operations views and exchange connections. `AppShell` currently renders every declared navigation item without consulting this readiness state.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T21:46:00Z
head: 5a19ae32f1f71b112130ea66cb8d56d9a3e44049
branch: feat/paper-g0-surface-availability-20260810
pr: none
status: implementing
context_routes:
  - PAPER G0 disconnected product surfaces
  - living navigation ledger
  - primary Portal AppShell navigation
owned_paths:
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/lib/surface-availability.json
  - tests/ai_platform/portal/test_surface_availability.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-surface-availability.md
proven:
  - Living navigation ledger is machine-readable and includes a final product status per primary-navigation route.
  - AppShell currently exposes all navigation entries regardless of DISCONNECTED/MISSING state.
  - Hiding unavailable navigation is sufficient for G0 work item 7 without deleting route code or fabricating backend capability.
derived:
  - A data-driven nav filter plus ledger-drift test is the smallest complete repair.
unknown:
  - Exact-head UI build/browser regression result after implementation.
conflicts: []
first_failure:
  marker: primary AppShell advertises DISCONNECTED/MISSING routes as ordinary links
  evidence: app-shell.tsx renders navigationGroups without availability filtering while living navigation.json marks multiple entries unavailable
rejected_hypotheses:
  - Delete disconnected pages; rejected because development/test evidence and future integration work must remain possible.
  - Treat navigation hiding as authorization; rejected because server authorization remains independently enforced.
changed_paths:
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-surface-availability.md
validation:
  - command: runtime/browser E2E
    result: NOT_RUN
    evidence: implementation not yet complete
blockers: []
next_action: Add the living-ledger-derived hidden navigation set, filter AppShell links, and add a deterministic ledger-drift regression before opening the G0/#7 PR.
```
