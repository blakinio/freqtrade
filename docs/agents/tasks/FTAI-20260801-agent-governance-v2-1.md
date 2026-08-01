---
task_id: FTAI-20260801-agent-governance-v2-1
status: validating
branch: docs/agent-governance-v2-1-restack-20260802
base_branch: develop
created: 2026-08-01
updated: 2026-08-02
related_pr: "PENDING"
required_reads:
  - AGENTS.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md
search_first:
  - prompt eval
  - trust boundary
  - vertical slice
  - task closeout audit e2e
---

# FTAI-20260801 — Agent governance v2.1

## Objective

Upgrade agent governance to v2.1 with eval-driven prompts, explicit trust/context boundaries, environment outcome verification, complete applicable vertical slices, and mandatory audit, real E2E, exact-head CI, terminal related PRs, task closure, and autonomous continuation.

## Scope

Documentation and governance only. Protected holdout, credentials, orders, live capital, strategy runtime, deployment, workflow, and upstream boundaries remain unchanged.

## Acceptance criteria

- [x] Prompt and harness changes are versioned, regression-evaluated, rollback-capable, and subject to balanced cases and repeated trials when nondeterminism matters.
- [x] Resulting environment state overrides worker completion claims.
- [x] Retrieved natural-language content remains untrusted data and cannot redefine authority.
- [x] User-facing work requires every applicable backend/frontend or producer/consumer layer and a real observable journey.
- [x] Closeout requires fresh audit, real E2E when applicable, final exact-head CI, resolved reviews, terminal related PRs, terminal task state, and released ownership.
- [x] Autonomous programmes continue through completed and archived tasks until a real stop.
- [ ] Replacement PR exact-head CI and review gates pass.
- [ ] Replacement PR merges, superseded PR #985 closes, and this task reaches terminal status.

## Context checkpoint

```yaml
checkpoint_version: 1
policy_version: 2
updated_at: 2026-08-02T00:30:00+02:00
head: aecdc4235e41ebe9dd6de24ed5828bd2da2254ff
branch: docs/agent-governance-v2-1-restack-20260802
pr: PENDING
status: validating
phase: replacement_pr
session_id: chat-20260801-governance-v2-1-restack
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
  - The seven governance contract blobs are bit-for-bit identical to the green, audited PR #985 versions.
  - The replacement commit is based directly on current develop commit 8f23bbc7e09c1c1c0906e32adc2b5af137ec07d7.
  - Only seven governance contracts plus this task are changed; no trading, strategy, workflow, credential, protected-data, order, or deployment code is modified.
  - Fresh content and cross-reference audit found no material finding.
  - Runtime E2E is NOT_APPLICABLE_WITH_REASON because only governance documentation changes; path, content, lifecycle, CI, review, and PR-state validation remain required.
derived:
  - A clean replacement PR is safer than resolving the stale-base conflict inside PR #985.
unknown:
  - Replacement PR number and its exact-head workflow results.
conflicts:
  - PR #985 cannot merge because its old branch conflicts with current develop.
first_failure:
  marker: stale-base-merge-conflict
  evidence: GitHub rejected merge of PR #985 with HTTP 409 despite green exact-head checks.
rejected_hypotheses:
  - force merge the conflicting PR
  - manually recreate the seven contract files
  - weaken develop or protected trading boundaries
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
  - command: exact blob-SHA restack on current develop
    result: PASS
    evidence: seven contract blob SHAs match the audited PR #985 branch exactly
  - command: runtime E2E applicability review
    result: PASS
    evidence: NOT_APPLICABLE_WITH_REASON — governance documentation only
blockers: []
next_action: open the replacement PR, bind its number to this task, close PR 985 as superseded, and verify exact-head checks
```
