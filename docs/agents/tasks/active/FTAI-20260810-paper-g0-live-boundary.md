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
trusted_base_sha: 960610f4607c4a27d402f5be5f12a211991f2fd7
delivery_branch: feat/paper-g0-live-boundary-20260810
delivery_pr: 1452
paper_gate: G0
live_capital_authorized: false
protected_production_deployment_authorized: false
repair_cycles_for_current_gate: 1
```

## Objective

Close PAPER G0 work item 6 by enforcing a fail-closed LIVE boundary across canonical authored bot create/revise operations, API persistence, config-revision promotion, managed-runtime resolution, dry-run runtime configuration, negative UI authority and model-promotion contracts. Keep the task durably active until audit, exact-head CI, review hygiene and merge are actually terminal.

## Acceptance

- reserved `LIVE_BLOCKED` remains readable only for historical/defensive state and cannot be authored through canonical create/revise operations;
- public API attempts cannot persist a LIVE bot or create generation/rollout side effects;
- historical LIVE revisions cannot cross config-revision promotion;
- permission and tenant-scope checks retain precedence over mode-specific rejection;
- runtime resolver rejects LIVE with `LIVE_CAPITAL_NOT_AUTHORIZED`;
- `ExecutionMode` has no LIVE value and managed Freqtrade configuration remains `dry_run: true`, credential-free and with control surfaces disabled;
- Bot Builder exposes no LIVE/managed-mode input and authors `execution_mode: dry_run`;
- model-promotion contracts carry no execution/live-capital authority;
- fresh independent exact-head audit has zero material findings before merge;
- exact-final-head required CI passes before merge;
- task remains active/nonterminal until those gates and PR merge are real;
- PAPER remains the only currently authorized operational trading mode and LIVE remains unreachable/fail-closed.

## Evidence

- Original implementation head `7af2daf45f0d30b160e69ebd9718013aaad19ed5` passed its routed Freqtrade CI and Risk-aware component CI and received an independent Codex review with no major issues.
- The branch was synchronized with current `develop@960610f4607c4a27d402f5be5f12a211991f2fd7`; the intervening base changes did not overlap the four product/test paths.
- Fresh review on candidate `33062db9f33c00ab8f364dc0d732999be95bff9b` found P1 `PRRT_kwDOTdDTU86Y...` / review `4904384496`: archiving the task with `status: completed` before audit/CI/merge made durable state falsely terminal.
- Candidate archive was removed on `11abc9e5dcef4e3892d5fcabe52bb6676ea6708b`; this active record restores truthful ownership until real closeout.
- No runtime deployment, protected environment, production secret, exchange credential, real order, withdrawal, model/strategy automatic promotion or live capital is authorized.

## Changed paths

- `ai_platform/portal/contracts/bots.py`
- `ai_platform/portal/control_plane/service.py`
- `tests/ai_platform/portal/control_plane/test_managed_runtime_mode_semantics.py`
- `tests/ai_platform/portal/test_live_fail_closed_boundaries.py`
- `docs/agents/tasks/active/FTAI-20260810-paper-g0-live-boundary.md`

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T08:39:30Z
head: 11abc9e5dcef4e3892d5fcabe52bb6676ea6708b
branch: feat/paper-g0-live-boundary-20260810
pr: 1452
status: validating
invocation_started_at: 2026-08-11T08:11:00Z
last_progress_at: 2026-08-11T08:39:30Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
review_checks_for_current_head: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - PAPER G0 LIVE fail-closed boundary
  - authored API and promotion authority
owned_paths:
  - ai_platform/portal/contracts/bots.py
  - ai_platform/portal/control_plane/service.py
  - tests/ai_platform/portal/control_plane/test_managed_runtime_mode_semantics.py
  - tests/ai_platform/portal/test_live_fail_closed_boundaries.py
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-live-boundary.md
proven:
  - LIVE_BLOCKED is rejected by managed-runtime resolution and the new authored-operation/promotion guards.
  - The synchronized branch is based on develop@960610f4607c4a27d402f5be5f12a211991f2fd7 with no product-path overlap from intervening base commits.
  - The premature candidate archive was a real P1 closeout defect and has been removed.
  - PAPER remains the only authorized operational trading mode and LIVE remains unreachable/fail-closed.
derived:
  - The product implementation remains frozen unless fresh exact-head evidence identifies a directly scoped defect.
unknown:
  - Fresh audit disposition and exact-head CI result for the successor containing this restored active record.
conflicts: []
first_failure:
  marker: task was archived completed before final gates were terminal
  evidence: Codex review 4904384496 on 33062db9f33c00ab8f364dc0d732999be95bff9b
rejected_hypotheses:
  - Keep a conditional completed record under archive before merge; rejected because fresh review proved it creates false terminal durable state.
  - Create a replacement PR; rejected because PR 1452 remains the authoritative reusable delivery path.
changed_paths:
  - docs/agents/tasks/active/FTAI-20260810-paper-g0-live-boundary.md
validation:
  - command: synchronized branch compare against develop@960610f4607c4a27d402f5be5f12a211991f2fd7
    result: PASS
    evidence: branch was zero commits behind before this closeout repair and intervening base changes did not overlap owned product/test paths
  - command: independent Codex review of 33062db9f33c00ab8f364dc0d732999be95bff9b
    result: FAIL
    evidence: P1 identified premature archival; product logic had no separate material finding
  - command: runtime/browser deployment E2E
    result: NOT_APPLICABLE
    evidence: fail-closed safety guardrail over API/service/promotion and static negative UI/runtime-contract boundaries; no runtime deployment or user-facing capability is added
blockers: []
next_action: Resolve the successor containing this restored active record, request fresh exact-head Codex review, and collect fresh required CI; repair only evidence-backed material findings.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: paper-20260811-1011-g0-live-boundary
  session_started_at: 2026-08-11T08:11:00Z
  checkpointed_at: 2026-08-11T08:39:30Z
  last_progress_at: 2026-08-11T08:39:30Z
  phase: restore_truthful_active_closeout_state
  exact_head: 11abc9e5dcef4e3892d5fcabe52bb6676ea6708b
  pull_request: 1452
  active_operation: materialize restored active task record before new external validation
  external_run_ids: []
  operation_started_at: 2026-08-11T08:39:30Z
  wait_deadline_at: null
  check_generation: restored_active_pre_validation
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: restored active task record exists on PR 1452
  next_action: Resolve the containing PR head, then begin a fresh bounded exact-head audit and CI cycle.
```
