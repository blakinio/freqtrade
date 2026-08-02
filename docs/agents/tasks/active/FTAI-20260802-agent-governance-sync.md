---
task_id: FTAI-20260802-agent-governance-sync
status: validating
branch: docs/FTAI-20260802-agent-governance-sync
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
related_pr: "1037"
owned_paths:
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md
  - docs/agents/GITHUB_ONLY_EXECUTION.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/TASK_TEMPLATE.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
search_first: []
optional_reads: []
---

# Synchronize shared agent governance

## Goal

Apply the shared governance correction without changing trading logic, deployment or live-capital controls.

## Acceptance criteria

- [x] Shared status, task-budget, exact-head, audit and authority rules are consistent.
- [x] Checkpoint validation accepts waiting/completed and NOT_APPLICABLE.
- [x] The change cannot authorize live-capital or production operations.
- [ ] Governance checks pass on the final PR head.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-02T13:08:00Z
head: 99ed3e9556bc08a7255e906153470412ca455338
branch: docs/FTAI-20260802-agent-governance-sync
pr: 1037
status: validating
context_routes:
  - agent-governance
owned_paths:
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md
  - docs/agents/GITHUB_ONLY_EXECUTION.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/TASK_TEMPLATE.md
proven:
  - The portable contract accepts waiting, completed and NOT_APPLICABLE.
  - Task status is separated from terminal invocation result.
  - Repository changes remain distinct from live-capital and production operations.
derived:
  - The shared contradictions are repaired without weakening dry-run, exchange-credential, promotion or capital boundaries.
unknown:
  - Exact-head Agent Governance workflow result for PR 1037.
conflicts: []
first_failure:
  marker: none
  evidence: none
rejected_hypotheses: []
changed_paths:
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/ANTI_STALL_AND_EXECUTION_BUDGET.md
  - docs/agents/AUTONOMOUS_PROGRAM_CONTINUATION.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/DELIVERY_COMPLETENESS_AND_CLOSEOUT.md
  - docs/agents/GITHUB_ONLY_EXECUTION.md
  - docs/agents/GOVERNANCE_CONTRACT.json
  - docs/agents/tasks/TASK_TEMPLATE.md
  - docs/agents/tasks/active/FTAI-20260802-agent-governance-sync.md
validation:
  - command: Agent Governance workflow
    result: NOT_RUN
    evidence: draft PR 1037 opened; exact-head checks pending
blockers: []
next_action: inspect exact-head workflow results for PR 1037 and repair any governance failure
```
