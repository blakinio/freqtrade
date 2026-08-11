---
task_id: FTAI-20260811-portal-repository-truth-1468
programme_id: FTAI-PROGRAM-AI-TRADING-PORTAL
project_lane: freqtrade-portal
status: blocked
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

Runtime/browser E2E is `NOT_APPLICABLE`: no product/runtime/deployment behavior changes.

## Acceptance

- stale `future/unimplemented` Portal wording is absent;
- README points current implementation claims to `tools/portal_audit/ledger/index.json` and architecture claims to `ARCHITECTURE_REGISTRY.yaml` / canonical Portal docs;
- README explicitly preserves PAPER-only / fail-closed LIVE authority;
- CODEOWNERS contains an explicit `/ai_platform/portal/` ownership umbrella plus current sensitive-path overrides;
- explicit sensitive coverage includes current control-plane, execution, execution-submission, bot-operations, exchange-connections, signal-control, identity, security, credentials, database, risk, Portal deploy, contracts, web and Synology deployment roots;
- the CI guard validates effective CODEOWNERS semantics rather than pattern-token presence only;
- exact-final-head required CI and documentation build pass;
- independent review has zero open material findings before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T10:00:00Z
head: 2b9c3f378dad5ecc68e48c9c51e7771f05264d15
branch: docs/portal-repository-truth-1468
pr: 1469
status: blocked
invocation_started_at: 2026-08-11T08:57:00Z
last_progress_at: 2026-08-11T10:00:00Z
ci_checks_for_current_head: 2
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
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
  - develop contains a living exact-head Portal completeness ledger and implemented Portal surfaces that made the old README false.
  - all review-identified sensitive Portal roots are explicitly covered and a Portal-wide CODEOWNERS umbrella is present.
  - earlier material review threads for missing roots and owner/order validation were repaired and resolved.
  - the branch was synchronized with develop@6577ae896ed5910f82f9e736fe4a007b6dc10e6e and retained exactly the four Issue #1468 paths before the terminal review.
  - final Codex review of exact head 2b9c3f378dad5ecc68e48c9c51e7771f05264d15 found a new material P2: the custom effective-owner matcher does not implement CODEOWNERS glob semantics and could miss a later overriding glob such as `/ai_platform/portal/** @other`.
  - PAPER remains the only currently authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - the finding is valid because the guard claims effective ownership validation but its matcher recognizes only `*`, directory prefixes and exact patterns.
unknown:
  - remediation result for full CODEOWNERS pattern semantics or an approved fail-closed rejection of unsupported patterns.
conflicts: []
first_failure:
  marker: effective CODEOWNERS guard does not interpret or reject supported glob patterns
  evidence: unresolved Codex P2 thread PRRT_kwDOTdDTU86YLqoN on exact head 2b9c3f378dad5ecc68e48c9c51e7771f05264d15
rejected_hypotheses:
  - ignore the glob finding because current CODEOWNERS has no such rule; rejected because the guard exists specifically to prevent future ownership regression.
  - perform a fourth same-gate repair cycle; forbidden by `ANTI_STALL_AND_EXECUTION_BUDGET.md` after three repair cycles.
changed_paths:
  - ai_platform/portal/README.md
  - .github/CODEOWNERS
  - tests/ci/test_portal_repository_truth.py
  - docs/agents/tasks/active/FTAI-20260811-portal-repository-truth-1468.md
validation:
  - command: independent Codex review of exact head 2b9c3f378dad5ecc68e48c9c51e7771f05264d15
    result: FAIL
    evidence: P2 PRRT_kwDOTdDTU86YLqoN identifies incomplete CODEOWNERS glob semantics in the effective-owner guard
  - command: prior exact-head CI observation
    result: NOT_RUN
    evidence: required workflows were still queued/pending/in-progress; CI cannot override an open material audit finding
  - command: runtime/browser product E2E
    result: NOT_APPLICABLE
    evidence: documentation and network-free CI-governance repair only
blockers:
  - repair-cycle budget for the CODEOWNERS validation gate is exhausted at 3 and a fresh isolation repair task/session is required before another implementation attempt
next_action: Start a fresh bounded isolation repair for PR 1469 that either implements the supported CODEOWNERS glob language needed for effective matching or fail-closed rejects unsupported patterns, then request fresh exact-head audit and CI before merge.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 6
  session_id: portal-truth-20260811-1142
  session_started_at: 2026-08-11T09:42:00Z
  checkpointed_at: 2026-08-11T10:00:00Z
  last_progress_at: 2026-08-11T10:00:00Z
  phase: repair_budget_exhausted
  exact_head: 2b9c3f378dad5ecc68e48c9c51e7771f05264d15
  pull_request: 1469
  active_operation: none
  external_run_ids:
    - 31479809612
    - 31479809286
    - 31479809289
    - 31479809375
    - 31479809268
    - 31479809327
    - 31479809294
  operation_started_at: null
  wait_deadline_at: null
  check_generation: effective-codeowners-glob-finding
  checks_used: 2
  status: blocked
  safe_to_resume: true
  resume_condition: fresh isolation repair authority/session resumes from unresolved P2 PRRT_kwDOTdDTU86YLqoN without resetting the recorded three repair cycles
  next_action: Start a fresh bounded isolation repair for PR 1469 that either implements the supported CODEOWNERS glob language needed for effective matching or fail-closed rejects unsupported patterns, then request fresh exact-head audit and CI before merge.
```

## Safety boundary

Documentation/CI-governance only. No deployment, protected environment, private exchange credentials, real order, withdrawal, model/strategy promotion or LIVE/live-capital authority is introduced.
