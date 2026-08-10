# FTAI-20260810 — PAPER G0 LIVE Boundary Contract

```yaml
task_id: FTAI-20260810-paper-g0-live-boundary
programme_id: FTAI-PAPER-PLATFORM
repository: blakinio/freqtrade
project_lane: freqtrade-portal
task_kind: safety_contract
phase: validation
status: validating
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

Implement G0 work item 6 from `PAPER_PLATFORM_IMPLEMENTATION_PLAN.md`: prove and enforce that LIVE cannot be selected or reached across authored schema/service, API, UI, Freqtrade configuration, managed runtime resolution and promotion boundaries.

## Acceptance

- reserved `LIVE_BLOCKED` may remain representable for historical/defensive reads but cannot be authored through canonical create/revise commands;
- API requests cannot persist a LIVE managed bot or revision;
- historical/reserved LIVE revisions cannot cross the config-revision promotion boundary;
- browser Bot Builder exposes no LIVE managed-mode input and continues to author `execution_mode: dry_run`;
- `ExecutionMode` has no live value and managed Freqtrade runtime config requires `dry_run=true`, disabled api_server/telegram and no credential fields;
- runtime resolver rejects `LIVE_BLOCKED` with stable `LIVE_CAPITAL_NOT_AUTHORIZED`;
- model-promotion contracts carry model/environment identity only and no execution/live-capital authority fields;
- all authority checks preserve permission/tenant validation ordering before mode-specific rejection;
- PAPER remains the only authorized operational mode; SHADOW remains optional/purpose-bound; LIVE remains unreachable/fail-closed;
- no protected deployment, exchange credential, real order, withdrawal or live capital is used by validation.

## Evidence and implementation

- `BotMode.LIVE_BLOCKED` remains in the durable enum intentionally as reserved terminology; deleting it would weaken historical/defensive representability.
- `require_authorized_authored_managed_mode()` now centralizes the reserved-LIVE authored boundary.
- canonical `ControlPlaneService.create_bot()` and `revise_bot()` enforce permission, tenant scope and then reject reserved LIVE before persistence.
- canonical `promote_revision()` enforces permission first and refuses a readable historical `LIVE_BLOCKED` revision before promotion/state-version mutation.
- runtime resolver already rejects LIVE and `RuntimeModeResolution` already requires credentials/order adapter/real execution/live capital/automatic promotion false and submitted orders zero.
- `ExecutionMode` contains only `simulated` and `dry_run`; `build_safe_dry_run_config()` requires DRY_RUN plus `dry_run is True`, a durable dry-run DB path and disabled api_server/telegram while rejecting credential fields.
- Bot Builder create form hardcodes `execution_mode: "dry_run"` and exposes no `managed_mode` or LIVE control.
- `ModelPromotionSlot` and `ModelPromotionTransition` carry no execution mode, managed mode, credential, real-execution, automatic-promotion or live-capital authority.

## Changed paths

- `ai_platform/portal/contracts/bots.py`
- `ai_platform/portal/control_plane/service.py`
- `tests/ai_platform/portal/control_plane/test_managed_runtime_mode_semantics.py`
- `tests/ai_platform/portal/test_live_fail_closed_boundaries.py`
- `docs/agents/tasks/active/FTAI-20260810-paper-g0-live-boundary.md`

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-10T21:30:00Z
head: 2a0dc09cabfeb2bd5519e29af8ebc4e61a21230c
branch: feat/paper-g0-live-boundary-20260810
pr: none
status: validating
invocation_started_at: 2026-08-10T21:07:00Z
last_progress_at: 2026-08-10T21:30:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - PAPER G0 LIVE fail-closed boundary
  - authored bot mode and API persistence
  - Freqtrade dry-run runtime config
  - UI and model-promotion authority surfaces
owned_paths:
  - ai_platform/portal/contracts/bots.py
  - ai_platform/portal/control_plane/service.py
  - tests/ai_platform/portal/control_plane/test_managed_runtime_mode_semantics.py
  - tests/ai_platform/portal/test_live_fail_closed_boundaries.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-live-boundary.md
proven:
  - Runtime mode resolver rejects LIVE_BLOCKED with LIVE_CAPITAL_NOT_AUTHORIZED.
  - ExecutionMode has no live value and Freqtrade runtime config requires dry_run=true.
  - Bot Builder exposes no LIVE/managed-mode control and authors dry_run.
  - Model promotion contract contains no execution or live-capital authority fields.
  - Canonical create/revise/promotion service now rejects reserved LIVE before mutation while preserving permission and tenant ordering.
  - LIVE_BLOCKED remains readable as reserved historical/defensive state rather than being silently deleted from contracts.
  - PAPER remains the only authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - The smallest complete G0/#6 repair is an authored-operation/promotion guard plus cross-boundary regression coverage; execution runtime itself required no redesign.
unknown:
  - Exact-head CI result for the implementation candidate.
  - Fresh independent Codex review disposition.
conflicts: []
first_failure:
  marker: reserved LIVE mode was representable and could reach authored create/revise and config-revision promotion before later runtime rejection
  evidence: pre-change ControlPlaneService inherited create/revise/promote without managed-mode guard
rejected_hypotheses:
  - Delete LIVE_BLOCKED from BotMode entirely; rejected because historical/defensive state must remain representable and fail closed.
  - Runtime-only rejection is sufficient; rejected because G0 requires earlier authored/API/UI/config/promotion barriers.
  - Reorder LIVE guard ahead of authorization; rejected because permission and tenant checks must retain precedence.
changed_paths:
  - ai_platform/portal/contracts/bots.py
  - ai_platform/portal/control_plane/service.py
  - tests/ai_platform/portal/control_plane/test_managed_runtime_mode_semantics.py
  - tests/ai_platform/portal/test_live_fail_closed_boundaries.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-live-boundary.md
validation:
  - command: existing managed-runtime mode semantics inventory
    result: PASS
    evidence: pre-existing runtime resolver and safe runtime-config tests inspected; implementation preserves them and adds earlier guards
  - command: runtime/browser E2E
    result: NOT_RUN
    evidence: exact-head CI and API integration validation pending; UI operating-mode surface is static and covered structurally
blockers: []
next_action: Open the bounded G0/#6 PR, request fresh Codex review, and collect the first aggregate exact-head CI result; repair only evidence-backed failures.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: paper-20260810-2307-live-boundary
  session_started_at: 2026-08-10T21:22:00Z
  checkpointed_at: 2026-08-10T21:30:00Z
  last_progress_at: 2026-08-10T21:30:00Z
  phase: implementation_complete_pre_pr_validation
  exact_head: 2a0dc09cabfeb2bd5519e29af8ebc4e61a21230c
  pull_request: none
  active_operation: open PR then fresh exact-head CI and independent Codex review
  external_run_ids: []
  operation_started_at: 2026-08-10T21:30:00Z
  wait_deadline_at: 2026-08-10T22:15:00Z
  check_generation: pre_pr
  checks_used: 0
  status: ready
  safe_to_resume: true
  resume_condition: delivery PR exists for current branch successor head
  next_action: Open PR from feat/paper-g0-live-boundary-20260810 to develop, request Codex review, and inspect the first aggregate exact-head CI snapshot.
```
