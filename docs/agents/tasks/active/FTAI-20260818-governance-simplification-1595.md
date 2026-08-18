---
task_id: FTAI-20260818-governance-simplification-1595
repository: blakinio/freqtrade
issue: 1595
status: ready
base_branch: develop
base_head: 73037e14ac48c43ca25e2b40e1a7ecaf8c5b1369
branch: docs/FTAI-20260818-governance-simplification-1595
prompt: docs/agents/prompts/FTAI_GOVERNANCE_SIMPLIFICATION.md
evidence: docs/agents/evidence/FTAI-20260818-governance-simplification-analysis.md
---

# FTAI-20260818 — Risk-based governance simplification

## Objective

Implement Issue `#1595`: align repository-wide execution governance with ADR-023 so ordinary Developer Quant work uses the minimum sufficient process, while higher-risk work automatically retains the controls required by the actual risk surface.

The desired change is **ceremony-based -> risk-based**, not **strict -> weak**.

## Governing product authority

Read and preserve:

- `AGENTS.md`
- `AGENTS.override.md`
- `docs/agents/AGENTS.md`
- `docs/agents/PROMPTING_STANDARD.md`
- `docs/agents/PROMPTING_HANDOVER.md`
- `docs/agents/BRANCH_POLICY.md`
- `docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md`
- `docs/agents/EXECUTION_PROTOCOL.md`
- `docs/ai_platform/portal/ADR-023_DEVELOPER_QUANT_PORTAL.md`
- `docs/ai_platform/portal/DEVELOPER_QUANT_PORTAL_ARCHITECTURE.md`
- `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`
- `docs/agents/evidence/FTAI-20260818-governance-simplification-analysis.md`
- Issue `#1595` and live GitHub state.

## Required outcome

1. Establish a canonical risk classifier / risk-based execution contract for repository tasks.
2. Keep a small universal Git/validation baseline and compose stronger gates only from actual risk flags.
3. Simplify `BRANCH_POLICY.md` around Git/integration semantics and defer the physical `main` migration absent a newly proven release-cadence need.
4. Align global prompting/handover/closeout contracts so audit, E2E, persistence, security, deployment and destructive-operation gates are conditional on scope/risk.
5. Preserve durable coordination for long-running/multi-agent work, exact-head merge safety, research integrity, secret boundaries, deliberate model activation and persistent Synology safety.
6. Produce an exact workflow inventory/ledger classifying relevant legacy workflows `KEEP | SIMPLIFY | RENAME | MERGE | RETIRE` from triggers/callers/dependencies/current risk; do not delete from filename semantics alone.
7. Add deterministic regression coverage for the new governance behavior.

## Non-goals

- no product feature implementation;
- no real exchange orders;
- no private trading credentials or withdrawals;
- no live capital;
- no automatic model activation;
- no destructive Synology cleanup;
- no physical `main` creation/migration in this task;
- no blind deletion of legacy workflows.

## Authority-freeze rule

This task began under the current trusted-base governance at `develop@73037e14ac48c43ca25e2b40e1a7ecaf8c5b1369`.

The task **must not use its own unmerged simplification to relax its own current review/validation/closeout authority**. Finish this task under the trusted-base rules. New risk-based semantics become authoritative only after merge and a later invocation based on the updated trusted base.

## Execution shape

```yaml
prompting_standard_version: 2.1
execution_policy_version: 2
task_kind: governance_refactor
context_pressure: medium
decomposition_decision: phased
execution_mode: codex_or_chat_with_github
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
```

Prefer one task, one branch and one PR. Split only if live evidence proves an independently owned migration is required.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-18T10:03:54+02:00
head: LIVE_BRANCH_HEAD_REQUIRED
branch: docs/FTAI-20260818-governance-simplification-1595
pr: none
status: ready
context_routes:
  - Issue #1595
  - docs/agents/evidence/FTAI-20260818-governance-simplification-analysis.md
  - docs/agents/prompts/FTAI_GOVERNANCE_SIMPLIFICATION.md
  - docs/ai_platform/portal/ADR-023_DEVELOPER_QUANT_PORTAL.md
  - docs/agents/BRANCH_POLICY.md
  - docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md
owned_paths:
  - docs/agents/**
  - tests/** governance-policy tests only when needed
  - .github/workflows/** classification or tightly justified governance migration only
proven:
  - develop base was 73037e14ac48c43ca25e2b40e1a7ecaf8c5b1369 at task creation
  - Issue #1595 exists and owns the governance simplification objective
  - ADR-023 requires proportionate safety for the current single-owner Developer Quant Portal
  - main was not an operational branch at task creation
  - repository used develop as default with squash merge and delete-branch-on-merge enabled
  - current branch was created specifically for Issue #1595
  - durable analysis was recorded on this branch
  - this task remains governed by trusted-base authority until merged
  - real-capital authority remains absent
  - legacy workflow names require exact trigger/dependency inspection before retirement
derived:
  - the main remaining mismatch is execution governance rather than product architecture
  - a risk-composition model can reduce ordinary-task ceremony without weakening relevant controls
  - multi-agent coordination controls remain useful despite the product being single-owner
  - a separate main release branch should remain deferred absent a real release-cadence need
unknown:
  - exact current trigger and dependency status of every legacy shadow paper staging production live workflow
  - exact minimal file set needed to implement the risk classifier without duplicating policy
  - whether any current required check still depends on a legacy workflow targeted for rename or retirement
conflicts:
  - ADR-023 proportionate validation conflicts in spirit with universal material-task ceremony in older global contracts
  - BRANCH_POLICY mixes current Git routing with superseded Portal bot-mode and production-release semantics
first_failure:
  marker: none-preexecution
  evidence: no implementation failure has occurred; task is READY from verified analysis
rejected_hypotheses:
  - private single-owner product means all governance can be removed
  - legacy workflow filename alone proves the workflow is obsolete
  - main must be created merely because ADR-021 once targeted it
  - force-rebase is the preferred synchronization path for tracked task branches
changed_paths:
  - docs/agents/evidence/FTAI-20260818-governance-simplification-analysis.md
  - docs/agents/tasks/active/FTAI-20260818-governance-simplification-1595.md
validation:
  - command: GitHub live-state inspection for develop repository settings issues branches policies and workflow inventory
    result: PASS
    evidence: Issue #1595 and dedicated branch created from exact develop base; findings recorded in durable analysis
  - command: python tools/agents/checkpoint.py docs/agents/tasks/active/FTAI-20260818-governance-simplification-1595.md --require-checkpoint
    result: NOT_RUN
    evidence: GitHub-only preparation path; executor must run the validator before merge
blockers: []
next_action: Execute docs/agents/prompts/FTAI_GOVERNANCE_SIMPLIFICATION.md against Issue #1595 from current live repository state and carry the task through trusted-base validation and merge-ready closeout.
```
