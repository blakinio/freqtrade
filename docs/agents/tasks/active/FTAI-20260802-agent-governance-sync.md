---
task_id: FTAI-20260802-agent-governance-sync
status: waiting
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
- [x] Freqtrade CI and workflow security analysis passed on verified head `e375159f86543217ef5769753845f509e8cadecf`.
- [ ] Coordinated Canary dependency is terminal and this PR is revalidated on its final metadata head.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-02T13:53:00Z
head: e375159f86543217ef5769753845f509e8cadecf
branch: docs/FTAI-20260802-agent-governance-sync
pr: 1037
status: waiting
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
  - Freqtrade CI run 30749985122 passed on head e375159f86543217ef5769753845f509e8cadecf.
  - GitHub Actions security analysis run 30749985106 passed on the verified head.
  - PR 1037 has zero unresolved review threads and changes only governance and task-record paths.
derived:
  - The shared contradictions are repaired without weakening dry-run, exchange-credential, promotion or capital boundaries.
unknown:
  - Exact-head workflow conclusions after this durable checkpoint update.
conflicts: []
first_failure:
  marker: coordinated Canary dependency
  evidence: Canary PR 1063 is blocked until isolation PR 1064 completes through normal branch protection
rejected_hypotheses:
  - Strategy, model, exchange or live-capital validation is required; this PR changes governance records only.
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
  - command: Freqtrade CI run 30749985122
    result: PASS
    evidence: exact verified head e375159f86543217ef5769753845f509e8cadecf
  - command: GitHub Actions security analysis run 30749985106
    result: PASS
    evidence: exact verified head e375159f86543217ef5769753845f509e8cadecf
  - command: review-thread audit
    result: PASS
    evidence: zero unresolved threads on PR 1037
blockers:
  - Canary PR 1063 must complete after lifecycle isolation PR 1064.
next_action: after Canary PR 1063 is terminal, verify all required workflows on the current PR 1037 head and merge through normal protections
```
