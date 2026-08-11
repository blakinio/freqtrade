---
task_id: FTAI-20260811-portal-repository-truth-1468
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: waiting
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
- CODEOWNERS explicitly covers current control-plane, execution, identity, security, credentials, database, risk, contracts, web and Synology deployment roots;
- a network-free `tests/ci` guard detects recurrence;
- exact-final-head required CI and documentation build pass;
- independent review has zero open material findings before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T09:10:00Z
head: d13f71214fec22665e56ab14135d519aee3ff071
branch: docs/portal-repository-truth-1468
pr: 1469
status: waiting
invocation_started_at: 2026-08-11T08:57:00Z
last_progress_at: 2026-08-11T09:10:00Z
ci_checks_for_current_head: 1
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 0
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
  - PR 1469 is the sole delivery PR for Issue 1468 and was zero commits behind develop when opened.
  - a fresh Codex review was explicitly requested on PR 1469 for exact head d13f71214fec22665e56ab14135d519aee3ff071.
  - PAPER remains the only currently authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - documentation truth must defer implementation completeness to exact-head evidence rather than package presence.
unknown:
  - terminal exact-head CI result and independent Codex review disposition for the final PR head.
conflicts: []
first_failure:
  marker: stale Portal implementation boundary documentation
  evidence: ai_platform/portal/README.md on develop@816aac5018b785f750ab9eaffd5de9033f988999
rejected_hypotheses:
  - treat stale README as harmless because architecture registry is canonical; rejected because root AGENTS routes Portal workers through this README.
changed_paths:
  - ai_platform/portal/README.md
  - .github/CODEOWNERS
  - tests/ci/test_portal_repository_truth.py
  - docs/agents/tasks/active/FTAI-20260811-portal-repository-truth-1468.md
validation:
  - command: exact file/state inspection on develop@816aac5018b785f750ab9eaffd5de9033f988999
    result: PASS
    evidence: verified stale README, living ledger and CODEOWNERS mismatch before mutation
  - command: branch compare at PR creation and before external validation
    result: PASS
    evidence: docs/portal-repository-truth-1468 remained behind_by=0 versus develop
  - command: first aggregate exact-head CI observation for d13f71214fec22665e56ab14135d519aee3ff071
    result: NOT_RUN
    evidence: required workflows were queued/pending; no failure evidence existed at the observation
  - command: runtime/browser product E2E
    result: NOT_APPLICABLE
    evidence: documentation and network-free CI-governance repair only
blockers:
  - fresh exact-head GitHub Actions and independent Codex audit are external pending gates
next_action: Resolve the current PR 1469 head, inspect the fresh Codex audit and one aggregate CI state; repair any material finding/failure or merge only if all exact-head gates are green and review hygiene is terminal.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 1
  session_id: portal-truth-20260811-1057
  session_started_at: 2026-08-11T08:57:00Z
  checkpointed_at: 2026-08-11T09:10:00Z
  last_progress_at: 2026-08-11T09:10:00Z
  phase: exact_head_ci_and_independent_audit
  exact_head: d13f71214fec22665e56ab14135d519aee3ff071
  pull_request: 1469
  active_operation: external CI and Codex review
  external_run_ids:
    - 31476385697
    - 31476385687
    - 31476385660
    - 31476385777
    - 31476385655
    - 31476386069
    - 31476385790
  operation_started_at: 2026-08-11T09:08:42Z
  wait_deadline_at: null
  check_generation: pre-terminal-validation
  checks_used: 1
  status: waiting
  safe_to_resume: true
  resume_condition: PR 1469 has fresh audit evidence and materially advanced exact-head CI state
  next_action: Resolve the current PR 1469 head, inspect the fresh Codex audit and one aggregate CI state; repair any material finding/failure or merge only if all exact-head gates are green and review hygiene is terminal.
```

## Safety boundary

Documentation/CI-governance only. No deployment, protected environment, private exchange credentials, real order, withdrawal, model/strategy promotion or LIVE/live-capital authority is introduced.
