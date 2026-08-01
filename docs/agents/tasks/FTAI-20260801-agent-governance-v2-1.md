---
task_id: FTAI-20260801-agent-governance-v2-1
status: validating
branch: docs/agent-governance-v2-1-20260801
base_branch: develop
created: 2026-08-01
updated: 2026-08-02
related_pr: "#985"
required_reads:
  - AGENTS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
search_first:
  - prompt eval
  - trust boundary
  - vertical slice
  - task closeout audit e2e
---

# FTAI-20260801 — Agent governance v2.1

## Objective

Extend v2 with eval-driven prompting, trust/context boundaries, outcome verification, complete vertical slices, and mandatory PR hygiene, fresh audit, E2E, final CI, task closure, and autonomous continuation.

## Scope

Documentation and agent governance only. Protected holdout, credentials, orders, live capital, strategy runtime, deployment, workflow, upstream-core and application boundaries remain unchanged.

## Acceptance criteria

- [x] Prompt changes use versioned regression evals, balanced cases, and repeated trials where needed.
- [x] Environment outcome overrides worker completion claims.
- [x] Retrieved content remains untrusted data and cannot redefine authority.
- [x] User-facing features require applicable backend/frontend integration and observable user-journey acceptance.
- [x] Closeout requires fresh audit, real E2E, exact-head final CI, review resolution, terminal related PRs, task closure, and released ownership.
- [x] WickHunter and other autonomous programmes continue through archived tasks until a real stop.
- [ ] Exact-head required CI passes.
- [ ] This task reaches terminal status after merge.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-02T00:10:00+02:00
head: 1ad86190e9019023c28ebebeb01396d6f686419e
branch: docs/agent-governance-v2-1-20260801
pr: "#985"
status: validating
phase: audit_and_ci
session_id: chat-20260801-governance-v2-1
session_role: coordinator
execution_mode: chat
run_scope: autonomous_program
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
context_routes:
  - agent-governance
owned_paths:
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/PROMPT_EVAL_STANDARD.md
  - docs/agents/TRUST_AND_CONTEXT_BOUNDARIES.md
  - docs/agents/END_TO_END_FEATURE_COMPLETENESS.md
  - docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md
  - docs/agents/tasks/FTAI-20260801-agent-governance-v2-1.md
proven:
  - The branch changes exactly seven normative governance files plus this task and no trading/runtime/workflow code.
  - All v2.1 cross-references exist and preserve protected-holdout, credential, order, live-capital and deployment boundaries.
  - Prompt eval, trust boundaries, complete vertical slices, outcome verification, fresh audit, real E2E, final CI, PR hygiene and archive-and-continue rules are normative.
  - Proportionate documentation audit found no material contradiction or missing contract.
  - Runtime E2E is NOT_APPLICABLE_WITH_REASON because only governance documentation changes; CI and lifecycle validation remain required.
derived:
  - The standard directly prevents backend-only complete-feature claims and stale PR accumulation.
unknown:
  - Exact-head CI/security results after this checkpoint commit.
  - Whether the advanced develop base requires restack before the merge gate.
  - Fresh final diff and review-thread state.
conflicts: []
first_failure:
  marker: none
  evidence: no exact-head failure classified yet
rejected_hypotheses:
  - encode durable rules only in chat
  - weaken protected or live-trading boundaries
  - treat implementation merge as task completion
changed_paths:
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/END_TO_END_FEATURE_COMPLETENESS.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPT_EVAL_STANDARD.md
  - docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md
  - docs/agents/TRUST_AND_CONTEXT_BOUNDARIES.md
  - docs/agents/tasks/FTAI-20260801-agent-governance-v2-1.md
validation:
  - command: compare develop...docs/agent-governance-v2-1-20260801
    result: PASS_SCOPE
    evidence: exactly eight authorized governance/task paths; develop advanced independently and will be checked at merge gate
  - command: cross-reference and contradiction audit
    result: PASS
    evidence: all normative paths exist and entry points route consistently
  - command: runtime E2E applicability review
    result: NOT_APPLICABLE_WITH_REASON
    evidence: no executable product behavior changed
blockers: []
next_action: verify exact-head required checks, mergeability against current develop, and fresh PR review for PR 985
```
