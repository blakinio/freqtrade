---
task_id: FTAI-20260811-portal-repository-truth-1468
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: validating
task_kind: ci_governance
priority: high
repository: blakinio/freqtrade
base_branch: develop
branch: docs/portal-repository-truth-1468
related_pr: 1469
issue: 1468
created: 2026-08-11
updated: 2026-08-11
live_capital_authorized: false
production_deployment_authorized: false
---

# Portal repository truth and CODEOWNERS drift guard

## Objective

Make `ai_platform/portal/README.md` and `.github/CODEOWNERS` reflect the exact current Portal implementation boundary without turning target architecture into implementation claims, and add a deterministic CI guard against the verified drift.

## Feature scope

```yaml
feature_scope:
  type: documentation
  user_facing: false
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: false
  completion_claim: internal_only
```

Runtime/browser E2E is `NOT_APPLICABLE`: no product/runtime/deployment behavior changes. Repository documentation build, `tests/ci`, exact-head required CI and independent review remain required.

## Acceptance

- stale `future/unimplemented` Portal wording is absent;
- README points current implementation claims to `tools/portal_audit/ledger/index.json` and architecture claims to `ARCHITECTURE_REGISTRY.yaml` / canonical Portal docs;
- README explicitly preserves PAPER-only / fail-closed LIVE authority;
- CODEOWNERS explicitly covers current control-plane, execution, execution-submission, bot-operations, identity, security, credentials, database, risk, contracts, web and Synology deployment roots;
- a network-free `tests/ci` guard detects recurrence;
- exact-final-head required CI and documentation build pass;
- independent review has zero open material findings before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T09:24:00Z
head: 980a731ea7f9c40ef1d2aa8de10645de05b1a24a
branch: docs/portal-repository-truth-1468
pr: 1469
status: validating
invocation_started_at: 2026-08-11T08:57:00Z
last_progress_at: 2026-08-11T09:24:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 0
stall_warnings: 0
context_routes:
  - Portal repository truth
  - CI governance
owned_paths:
  - ai_platform/portal/README.md
  - .github/CODEOWNERS
  - tests/ci/test_portal_repository_truth.py
  - docs/agents/tasks/active/FTAI-20260811-portal-repository-truth-1468.md
proven:
  - develop@816aac5018b785f750ab9eaffd5de9033f988999 contains a living exact-head Portal completeness ledger.
  - the prior Portal README falsely described implemented Portal surfaces as future/unimplemented.
  - CODEOWNERS retained historical Portal backend/infra path-specific entries instead of current sensitive roots.
  - execution_submission and bot_operations are existing execution-sensitive Portal packages on develop.
  - fresh Codex review on ebc42b945af8609e1cb35a7d4be70b03057faf1e found one material P2: explicit ownership omitted execution_submission and bot_operations.
  - the P2 was remediated in CODEOWNERS and REQUIRED_CODEOWNER_PATTERNS on head 980a731ea7f9c40ef1d2aa8de10645de05b1a24a.
  - PAPER remains the only currently authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - documentation truth must defer implementation completeness to exact-head evidence rather than package presence.
unknown:
  - terminal exact-head CI result and fresh post-remediation Codex review disposition for the final PR head.
conflicts: []
first_failure:
  marker: explicit CODEOWNERS coverage omitted execution-sensitive Portal roots
  evidence: Codex P2 review comment 3756671117 on ebc42b945af8609e1cb35a7d4be70b03057faf1e
rejected_hypotheses:
  - treat stale README as harmless because architecture registry is canonical; rejected because root AGENTS routes Portal workers through this README.
  - rely on generic CODEOWNERS fallback for execution_submission and bot_operations; rejected because explicit sensitive-root ownership is the intended durable boundary.
changed_paths:
  - ai_platform/portal/README.md
  - .github/CODEOWNERS
  - tests/ci/test_portal_repository_truth.py
  - docs/agents/tasks/active/FTAI-20260811-portal-repository-truth-1468.md
validation:
  - command: exact file/state inspection on develop@816aac5018b785f750ab9eaffd5de9033f988999
    result: PASS
    evidence: verified stale README, living ledger and CODEOWNERS mismatch before mutation
  - command: existence inspection for ai_platform/portal/execution_submission and ai_platform/portal/bot_operations
    result: PASS
    evidence: both current execution-sensitive roots exist on develop with submission/transport and activation/order/position surfaces
  - command: independent Codex review of ebc42b945af8609e1cb35a7d4be70b03057faf1e
    result: FAIL
    evidence: P2 3756671117 identified omitted explicit ownership roots; repair applied
  - command: runtime/browser product E2E
    result: NOT_APPLICABLE
    evidence: documentation and network-free CI-governance repair only
blockers: []
next_action: Request fresh independent Codex review on the current exact head and collect exact-head required CI; repair any material finding/failure or merge only if all gates are green and review hygiene is terminal.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 2
  session_id: portal-truth-20260811-1120
  session_started_at: 2026-08-11T09:20:00Z
  checkpointed_at: 2026-08-11T09:24:00Z
  last_progress_at: 2026-08-11T09:24:00Z
  phase: post_review_repair_validation
  exact_head: 980a731ea7f9c40ef1d2aa8de10645de05b1a24a
  pull_request: 1469
  active_operation: material review remediation and exact-head validation
  external_run_ids: []
  operation_started_at: 2026-08-11T09:24:00Z
  wait_deadline_at: null
  check_generation: post-p2-remediation
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: current exact head remains unchanged
  next_action: Request fresh independent Codex review on the current exact head and collect exact-head required CI; repair any material finding/failure or merge only if all gates are green and review hygiene is terminal.
```

## Safety boundary

Documentation/CI-governance only. No deployment, protected environment, private exchange credentials, real order, withdrawal, model/strategy promotion or LIVE/live-capital authority is introduced.
