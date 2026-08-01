---
task_id: FTAI-20260801-agent-governance-v2-1
status: implementing
branch: docs/agent-governance-v2-1-20260801
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
related_pr: ""
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

Extend the v2 agent contracts with eval-driven prompting, trust/context boundaries, outcome verification, complete vertical slices, and mandatory PR hygiene, fresh audit, E2E, final CI, task closure, and autonomous continuation.

## Scope

Documentation and agent-governance contracts only. No strategy execution, protected-holdout access, credentials, orders, live capital, deployment, upstream-core, workflow, or application mutation is authorized.

## Acceptance criteria

- [ ] Prompt changes use versioned regression evals, balanced cases, and repeated trials where needed.
- [ ] Environment outcome overrides worker completion claims.
- [ ] Retrieved content remains untrusted data and cannot redefine authority.
- [ ] User-facing features require applicable backend/frontend integration and observable user-journey acceptance.
- [ ] Closeout requires fresh audit, real E2E, exact-head final CI, review-thread resolution, terminal related PRs, task closure, and released ownership.
- [ ] WickHunter and other autonomous programmes continue through archived tasks until a real stop.
- [ ] Exact-head required CI passes.
- [ ] This task reaches terminal status after merge.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-01T23:46:00+02:00
head: UNKNOWN
branch: docs/agent-governance-v2-1-20260801
pr: UNKNOWN
status: implementing
phase: implement
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
  - Autonomous continuation v2 is already merged on develop.
  - The owner explicitly authorized this cross-repository governance update.
derived:
  - New rules should be reusable normative contracts referenced by the existing prompting entry points.
unknown:
  - Exact PR number and workflow results until the draft PR is opened.
conflicts: []
first_failure:
  marker: none
  evidence: no exact-head failure classified yet
rejected_hypotheses:
  - encode durable rules only in chat
  - permit protected or live-trading boundaries to change
changed_paths:
  - docs/agents/tasks/FTAI-20260801-agent-governance-v2-1.md
validation: []
blockers: []
next_action: add the v2.1 normative contracts and update the prompting entry points
```
