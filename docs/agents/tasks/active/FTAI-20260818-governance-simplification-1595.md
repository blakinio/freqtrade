---
task_id: FTAI-20260818-governance-simplification-1595
repository: blakinio/freqtrade
issue: 1595
status: implementing
base_branch: develop
base_head: 782f0c8cdb5f24e83a2bc9ad9660df1474a470ab
branch: docs/1595-governance-simplification
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

The executor invocation began under trusted-base governance at `develop@782f0c8cdb5f24e83a2bc9ad9660df1474a470ab`, after preparation PR `#1599` was merged.

This task **must not use its own unmerged simplification to relax its own review/validation/closeout authority**. In particular, changes to CI routing in this task must continue to route governance/CI architecture changes through the trusted-base full validation tier. New risk-based semantics become authoritative only after merge and a later invocation based on the updated trusted base.

## Execution shape

```yaml
prompting_standard_version: 2.1
execution_policy_version: 2
task_kind: governance_refactor
context_pressure: medium
decomposition_decision: phased
execution_mode: chat_with_github_connector
codex_spark_permission: explicitly_granted_by_owner_2026-08-18
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
```

Prefer one task, one branch and one PR. Split only if live evidence proves an independently owned migration is required.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-18T10:17:00+02:00
head: 782f0c8cdb5f24e83a2bc9ad9660df1474a470ab
branch: docs/1595-governance-simplification
pr: none
status: implementing
context_routes:
  - Issue #1595
  - docs/agents/evidence/FTAI-20260818-governance-simplification-analysis.md
  - docs/agents/prompts/FTAI_GOVERNANCE_SIMPLIFICATION.md
  - docs/ai_platform/portal/ADR-023_DEVELOPER_QUANT_PORTAL.md
  - docs/agents/BRANCH_POLICY.md
  - docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md
owned_paths:
  - AGENTS.override.md
  - docs/agents/**
  - tools/agents/** governance policy only
  - tools/ci/change_classifier.py
  - tests/ci/** governance-policy and routing tests only
  - .github/workflows/** inspection only unless a tightly justified migration is proven
risk:
  persistent_data: false
  research_integrity: false
  model_activation: false
  auth_or_secrets: false
  shared_synology_mutation: false
  deployment: false
  user_workflow_change: false
  destructive_operation: false
  real_capital: false
  governance_or_ci: true
risk_gates:
  - policy_regression
  - independent_audit
  - exact_head_full_ci_under_trusted_base
authority_freeze:
  current_base_commit: 782f0c8cdb5f24e83a2bc9ad9660df1474a470ab
  note: This task self-closes under the trusted-base governance and keeps governance/CI architecture changes on the full validation tier.
proven:
  - preparation PR #1599 was squash-merged and develop was verified at 782f0c8cdb5f24e83a2bc9ad9660df1474a470ab before executor branch creation
  - Issue #1595 is open and owns the governance simplification objective
  - no parallel implementation PR or governance-simplification branch existed at executor start
  - ADR-023 requires proportionate safety for the current single-owner Developer Quant Portal
  - repository uses develop as the integration/default branch and the task does not operationalize main
  - real-capital authority remains absent
  - current change_classifier forces full CI for every ready_for_review and protected-branch push, independent of changed-path risk
  - legacy workflow names require exact trigger/dependency inspection before retirement
  - owner explicitly permitted Codex Spark for this task
derived:
  - the main remaining mismatch is execution governance rather than product architecture
  - a composable risk model can reduce ordinary-task ceremony without weakening relevant controls
  - durable coordination remains required for long-running multi-agent or failure-prone work
unknown:
  - exact current trigger and dependency status of each relevant legacy shadow paper staging production live workflow
  - whether any legacy workflow can be safely renamed or retired in this task
conflicts:
  - ADR-023 proportionate validation conflicts with universal material-task ceremony in older global contracts
  - BRANCH_POLICY mixes current Git routing with superseded Portal bot-mode and production-release semantics
first_failure:
  marker: local-checkout-unavailable
  evidence: local clone could not resolve github.com, so execution continues under the repository-approved GitHub-only path
rejected_hypotheses:
  - private single-owner product means all governance can be removed
  - legacy workflow filename alone proves the workflow is obsolete
  - main must be created merely because ADR-021 once targeted it
  - force-rebase is the preferred synchronization path for tracked task branches
changed_paths:
  - docs/agents/tasks/active/FTAI-20260818-governance-simplification-1595.md
validation:
  - command: GitHub live-state inspection of develop, Issue #1595, preparation PR #1599, branches and exact current policy files
    result: PASS
    evidence: develop@782f0c8cdb5f24e83a2bc9ad9660df1474a470ab; #1599 merged; no parallel implementation PR/branch found
blockers: []
next_action: Implement the canonical risk policy, align governance documents and CI routing, then build the exact legacy-workflow ledger and run trusted-base validation on the final PR head.
```
