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
- README points current implementation claims to `tools/portal_audit/ledger/index.json` and architecture claims to `ARCHITECTURE_REGISTRY.yaml` / canonical Portal docs;
- README explicitly preserves PAPER-only / fail-closed LIVE authority;
- CODEOWNERS contains an explicit `/ai_platform/portal/` ownership umbrella plus current sensitive-path overrides;
- explicit sensitive coverage includes current control-plane, execution, execution-submission, bot-operations, exchange-connections, signal-control, identity, security, credentials, database, risk, Portal deploy, contracts, web and Synology deployment roots;
- the CI guard validates owner fields and effective ownership, and fails closed on unsupported unanchored/glob rules capable of affecting a protected root;
- exact-final-head required CI and documentation build pass;
- independent review has zero open material findings before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-11T10:14:00Z
head: 39b093a32dcd74b00cb4f39c88144c9dc5ab000a
branch: docs/portal-repository-truth-1468
pr: 1469
status: validating
invocation_started_at: 2026-08-11T08:57:00Z
last_progress_at: 2026-08-11T10:14:00Z
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
fresh_isolation_repairs: 1
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
  - the original three same-gate repair cycles were exhausted after the effective-owner glob finding on parent head 2b9c3f378dad5ecc68e48c9c51e7771f05264d15.
  - fresh isolation PR #1471 repaired glob handling without resetting those counters: unsupported unanchored/glob rules that can affect a protected root fail closed, including broad `/ai_platform/portal/**` and child `/ai_platform/portal/control_plane/api*` cases.
  - PR #1471 exact head de01d8174b4ee2821b301fff7113d913f6f2e827 received fresh Codex review with no material issues and was squash-merged into this task branch as 9777009ab4fdaa0351949decc309264af13ec90a.
  - the task branch was then synchronized with current develop@2e7a99f6693469c0f8a009a2c8d00056fc817674 through merge commit 39b093a32dcd74b00cb4f39c88144c9dc5ab000a using the exact current develop tree plus the four task-owned files.
  - PAPER remains the only currently authorized operational mode and LIVE remains unreachable/fail-closed.
derived:
  - documentation truth must defer implementation completeness to exact-head evidence rather than package presence.
  - the Portal-wide umbrella plus fail-closed effective-rule validation covers the regression classes found by independent audit without claiming a full CODEOWNERS parser.
unknown:
  - terminal exact-head CI result and final parent Codex review disposition after the isolation merge and develop synchronization.
conflicts: []
first_failure:
  marker: none open; prior glob-semantics P2 was isolated and repaired in PR #1471
  evidence: PR #1471 merged after clean review of de01d8174b4ee2821b301fff7113d913f6f2e827
rejected_hypotheses:
  - ignore the glob finding because current CODEOWNERS has no such rule; rejected because the guard exists specifically to prevent future ownership regression.
  - perform a fourth same-gate parent repair cycle; rejected by anti-stall policy; a separate isolation branch/PR was used instead.
  - implement a partial CODEOWNERS glob matcher and claim complete semantics; rejected in favor of explicit fail-closed behavior for unsupported patterns that can affect protected roots.
changed_paths:
  - ai_platform/portal/README.md
  - .github/CODEOWNERS
  - tests/ci/test_portal_repository_truth.py
  - docs/agents/tasks/active/FTAI-20260811-portal-repository-truth-1468.md
validation:
  - command: focused isolation logic reproduction
    result: PASS
    evidence: current rules resolve protected roots to @blakinio; broad and child overriding glob fixtures fail closed
  - command: independent Codex review of isolation PR #1471 head de01d8174b4ee2821b301fff7113d913f6f2e827
    result: PASS
    evidence: Codex Review reported no major issues after the child-glob repair
  - command: isolation review-thread reconciliation
    result: PASS
    evidence: P1 thread PRRT_kwDOTdDTU86YLzTo resolved after repair
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
  generation: 7
  session_id: portal-truth-20260811-1142
  session_started_at: 2026-08-11T09:42:00Z
  checkpointed_at: 2026-08-11T10:14:00Z
  last_progress_at: 2026-08-11T10:14:00Z
  phase: final_parent_validation_after_isolation
  exact_head: 39b093a32dcd74b00cb4f39c88144c9dc5ab000a
  pull_request: 1469
  active_operation: final parent audit and exact-head CI
  external_run_ids: []
  operation_started_at: 2026-08-11T10:14:00Z
  wait_deadline_at: null
  check_generation: post-isolation-parent-final
  checks_used: 0
  status: active
  safe_to_resume: true
  resume_condition: current parent head remains unchanged or is only advanced by this checkpoint record
  next_action: Request one fresh independent Codex review and exact-head required CI on the containing parent head; if clean and green with zero unresolved threads and behind_by=0, squash-merge PR #1469 and perform lifecycle-only archive closeout.
```

## Safety boundary

Documentation/CI-governance only. No deployment, protected environment, private exchange credentials, real order, withdrawal, model/strategy promotion or LIVE/live-capital authority is introduced.
