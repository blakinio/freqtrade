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

Runtime/browser E2E is `NOT_APPLICABLE`: no product/runtime/deployment behavior changes.

## Acceptance

- stale `future/unimplemented` Portal wording is absent;
- README points implementation truth to `tools/portal_audit/ledger/index.json` and architecture authority to `ARCHITECTURE_REGISTRY.yaml` / canonical Portal docs;
- README preserves PAPER-only / fail-closed LIVE authority;
- CODEOWNERS contains an explicit `/ai_platform/portal/` umbrella and current sensitive-root overrides;
- the Portal ownership block is terminal in CODEOWNERS so no later rule of any syntax can override Portal ownership;
- all rules in that terminal block carry the intended owner and missing, duplicate, extra or later rules fail the deterministic guard;
- exact-final-head required CI passes;
- independent final review has zero open material findings before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T10:28:00Z
head: 4e6cda5ce3fff55e29054b225a63a7613e303c36
branch: docs/portal-repository-truth-1468
pr: 1469
status: validating
invocation_started_at: 2026-08-11T08:57:00Z
last_progress_at: 2026-08-11T10:28:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
fresh_isolation_repairs: 2
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
  - all review-identified sensitive Portal roots are explicitly covered under a Portal-wide umbrella.
  - the parent same-gate repair budget remained capped at three; later semantic defects were handled only through fresh isolation PRs.
  - isolation PR #1471 repaired broad/child glob handling and passed fresh Codex review on `de01d8174b4ee2821b301fff7113d913f6f2e827` before merge as `9777009ab4fdaa0351949decc309264af13ec90a`.
  - subsequent parent review found slashless-directory semantics still made custom pattern emulation fragile.
  - isolation PR #1472 removed custom pattern emulation entirely: the Portal umbrella and explicit overrides are now the final CODEOWNERS block; the guard verifies the complete terminal block and intended owners and rejects any appended rule.
  - isolation PR #1472 exact head `79263e7226bc972120c971fdacc4dc5a524bc5cc` received a clean Codex review and was squash-merged into this branch as `4e6cda5ce3fff55e29054b225a63a7613e303c36`.
  - parent review threads for the glob and slashless findings were resolved only after those isolation merges.
  - the branch was synchronized with `develop@2e7a99f6693469c0f8a009a2c8d00056fc817674` before the second isolation merge and had no product/runtime overlap.
  - PAPER remains the only currently authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - a terminal ownership block is simpler and more robust than reimplementing GitHub CODEOWNERS matching semantics in the CI guard.
unknown:
  - terminal exact-head CI result and final independent parent review disposition for the containing commit after this checkpoint update.
conflicts: []
first_failure:
  marker: none open; slashless-directory effective-ownership P2 was isolated and repaired in PR #1472
  evidence: PR #1472 clean Codex review comment 5251947333 and merge commit 4e6cda5ce3fff55e29054b225a63a7613e303c36
rejected_hypotheses:
  - continue extending a partial CODEOWNERS matcher; rejected because independent review exposed successive valid syntax forms and a terminal block proves the desired invariant without parsing them.
changed_paths:
  - ai_platform/portal/README.md
  - .github/CODEOWNERS
  - tests/ci/test_portal_repository_truth.py
  - docs/agents/tasks/active/FTAI-20260811-portal-repository-truth-1468.md
validation:
  - command: focused terminal-block logic reproduction
    result: PASS
    evidence: current block is complete with intended owner and appended glob, slashless, child-glob, unanchored, unrelated or wildcard rules all fail closed
  - command: independent Codex review of isolation PR #1472 head 79263e7226bc972120c971fdacc4dc5a524bc5cc
    result: PASS
    evidence: Codex Review reported no major issues
  - command: isolation review hygiene
    result: PASS
    evidence: PR #1472 had zero material review threads; parent slashless thread PRRT_kwDOTdDTU86YMDRq is resolved after merge
  - command: runtime/browser product E2E
    result: NOT_APPLICABLE
    evidence: documentation and network-free CI-governance repair only
blockers: []
next_action: Request one fresh independent Codex review and exact-head required CI on the containing parent head; if clean and green with zero unresolved threads and behind_by=0, squash-merge PR #1469 and perform lifecycle-only archive closeout.
```

## Recovery checkpoint

```yaml
recovery:
  policy_version: 1
  generation: 8
  session_id: portal-truth-20260811-1142
  session_started_at: 2026-08-11T09:42:00Z
  checkpointed_at: 2026-08-11T10:28:00Z
  last_progress_at: 2026-08-11T10:28:00Z
  phase: final_parent_validation_after_terminal_block_isolation
  exact_head: 4e6cda5ce3fff55e29054b225a63a7613e303c36
  pull_request: 1469
  active_operation: final parent audit and exact-head CI
  external_run_ids: []
  operation_started_at: 2026-08-11T10:28:00Z
  wait_deadline_at: null
  check_generation: terminal-portal-codeowners-block
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: current parent head remains unchanged or is only advanced by this checkpoint record
  next_action: Request one fresh independent Codex review and exact-head required CI on the containing parent head; if clean and green with zero unresolved threads and behind_by=0, squash-merge PR #1469 and perform lifecycle-only archive closeout.
```

## Safety boundary

Documentation/CI-governance only. No deployment, protected environment, private exchange credentials, real order, withdrawal, model/strategy promotion or LIVE/live-capital authority is introduced.
