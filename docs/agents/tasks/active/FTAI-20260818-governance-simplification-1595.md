---
task_id: FTAI-20260818-governance-simplification-1595
repository: blakinio/freqtrade
issue: 1595
status: validating
base_branch: develop
base_head: 782f0c8cdb5f24e83a2bc9ad9660df1474a470ab
branch: docs/1595-governance-simplification
pr: 1600
prompt: docs/agents/prompts/FTAI_GOVERNANCE_SIMPLIFICATION.md
evidence: docs/agents/evidence/FTAI-20260818-governance-simplification-analysis.md
prompt_eval: docs/agents/evidence/FTAI-20260818-governance-prompt-eval.md
workflow_ledger: docs/agents/evidence/FTAI-20260818-governance-workflow-ledger.md
---

# FTAI-20260818 — Risk-based governance simplification

## Objective

Implement Issue `#1595`: align repository-wide execution governance with ADR-023 so ordinary Developer Quant work uses the minimum sufficient process, while higher-risk work automatically retains controls required by the actual risk surface.

The change is **ceremony-based -> risk-based**, not **strict -> weak**.

## Required outcome

1. Establish a canonical risk classifier / risk-based execution contract for repository tasks.
2. Keep a small universal Git/validation baseline and compose stronger gates only from actual risk flags.
3. Simplify `BRANCH_POLICY.md` around Git/integration semantics and defer physical `main` migration absent a newly proven release-cadence need.
4. Align global prompting/handover/closeout/execution contracts so audit, E2E, persistence, security, deployment and destructive-operation gates are conditional on scope/risk.
5. Preserve durable coordination for long-running/multi-agent work, exact-head merge safety, research integrity, trust boundaries, secret boundaries, deliberate model activation and persistent Synology safety.
6. Produce an exact legacy-workflow ledger from inspected triggers/callers/dependencies/current risk; do not mutate workflows from filename semantics alone.
7. Add deterministic regression coverage for low-risk routing, high-risk composition and fail-closed real-capital behavior.

## Non-goals

- no product feature implementation;
- no exchange order execution, credentials or withdrawals;
- no live capital;
- no automatic model activation;
- no Synology runtime/deployment mutation;
- no destructive cleanup;
- no physical `main` creation/migration;
- no incomplete workflow retirement outside its registry/catalog lifecycle.

## Authority freeze

Execution began under trusted-base governance at `develop@782f0c8cdb5f24e83a2bc9ad9660df1474a470ab` after preparation PR `#1599` was merged.

This task may not use its own unmerged simplification to relax its own closeout. Because it changes CI architecture, canonical governance routing and `tools/ci/change_classifier.py`, `ci_architecture => full` is intentionally preserved and PR `#1600` must complete under trusted-base full validation plus fresh audit.

Owner permission for direct Codex Spark use in this task was explicitly granted on 2026-08-18. PR `#1600` has label `spark-review`; the standing central Spark controller in root `AGENTS.md` remains a separate bounded exception. Spark is advisory unless an actual controller result exists, and the task must not fabricate one or block solely on absent Spark output once non-Spark required gates pass.

## Context checkpoint

```yaml
checkpoint_version: 1
observed_at: 2026-08-18T09:10:27Z
branch: docs/1595-governance-simplification
head_before_checkpoint: 6fafbea87aeaeffa429e08d460506e282ed5f798
pr: 1600
status: validating
context_routes:
  - Issue #1595
  - PR #1600
  - docs/agents/prompts/FTAI_GOVERNANCE_SIMPLIFICATION.md
  - docs/agents/evidence/FTAI-20260818-governance-simplification-analysis.md
  - docs/agents/evidence/FTAI-20260818-governance-prompt-eval.md
  - docs/agents/evidence/FTAI-20260818-governance-workflow-ledger.md
  - docs/ai_platform/portal/ADR-023_DEVELOPER_QUANT_PORTAL.md
owned_paths:
  - AGENTS.override.md
  - docs/agents/**
  - tools/agents/risk_policy.py
  - tools/ci/change_classifier.py
  - tools/ci/change-routing.json
  - tests/ci/test_agent_risk_policy.py
  - tests/ci/test_change_classifier.py
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
  note: The unmerged risk-based policy cannot waive this task's trusted-base controls.
proven:
  - preparation PR #1599 was squash-merged before executor branch creation
  - PR #1600 is mergeable and targets develop
  - implementation introduces docs/agents/RISK_BASED_EXECUTION_POLICY.json and tools/agents/risk_policy.py
  - real_capital is a fail-closed STOP in the machine-readable policy
  - ready_for_review and ordinary push-to-develop no longer force full CI solely because of event/action
  - canonical governance behavior paths now map to ci_architecture so future governance self-changes retain full trusted-base validation
  - workflow ledger was built from inspected workflow content, not filenames alone
  - WH09 self-repair is a RETIRE candidate because its target branch is absent and Issue #1144 is closed
  - file-only WH09 retirement is unsafe/incomplete because workflow registry/catalog lifecycle tracks the file; workflow was restored exactly and physical retirement deferred
  - owner explicitly permitted Codex Spark and spark-review label is present on PR #1600
  - pre-audit-remediation exact-head Risk-aware component CI run 32119557309 completed SUCCESS on 6fafbea87aeaeffa429e08d460506e282ed5f798
unknown:
  - whether the central Spark controller will publish an advisory result for PR #1600
first_failure:
  marker: none_unresolved
  evidence: initial PR head 48db3c15d3f0ca1569dd1e8e9214d177c2ba3d30 failed only workflow registry consistency after file-only retirement; that failure was remediated. Fresh audit findings are remediated in the next candidate commit and require new exact-head CI.
rejected_hypotheses:
  - private single-owner product means governance can be removed rather than risk-scaled
  - legacy workflow filename proves capital authority or safe retirement
  - main must be operationalized because ADR-021 once targeted it
  - force-rebase is the preferred synchronization path for tracked task branches
  - WH09 workflow can be safely retired by deleting only its YAML file
changed_paths:
  - AGENTS.override.md
  - docs/agents/AGENTS.md
  - docs/agents/BRANCH_POLICY.md
  - docs/agents/EXECUTION_PROTOCOL.md
  - docs/agents/PROMPTING_HANDOVER.md
  - docs/agents/PROMPTING_STANDARD.md
  - docs/agents/RISK_BASED_EXECUTION_POLICY.json
  - docs/agents/TASK_CLOSEOUT_AUDIT_E2E.md
  - docs/agents/evidence/FTAI-20260818-governance-prompt-eval.md
  - docs/agents/evidence/FTAI-20260818-governance-workflow-ledger.md
  - docs/agents/tasks/active/FTAI-20260818-governance-simplification-1595.md
  - tests/ci/test_agent_risk_policy.py
  - tests/ci/test_change_classifier.py
  - tools/agents/risk_policy.py
  - tools/ci/change-routing.json
  - tools/ci/change_classifier.py
validation:
  - check: trusted-base live-state reconstruction
    result: PASS
    evidence: develop@782f0c8cdb5f24e83a2bc9ad9660df1474a470ab; #1599 merged; no parallel #1595 implementation branch/PR at start
  - check: initial exact-head CI diagnosis
    result: FAIL_THEN_REMEDIATED
    evidence: head 48db3c15d3f0ca1569dd1e8e9214d177c2ba3d30; tests/ci reported 120 passed, 1 skipped and one registry consistency failure for the deleted WH09 workflow
  - check: pre-audit-remediation exact-head component CI
    result: PASS_BUT_SUPERSEDED_BY_AUDIT_REMEDIATION
    evidence: Risk-aware component CI 32119557309 SUCCESS on head 6fafbea87aeaeffa429e08d460506e282ed5f798
  - check: fresh independent final-diff audit
    result: FINDINGS_REMEDIATED_PENDING_EXACT_HEAD_CI
    evidence: GOV-AUDIT-001..005 recorded in docs/agents/evidence/FTAI-20260818-governance-prompt-eval.md
audit:
  validator: fresh continuation role reading trusted-base contracts, exact diff and live PR/CI state
  result: REMEDIATED_PENDING_EXACT_HEAD_CI
  findings_open_material: 0
  findings:
    - GOV-AUDIT-001 trust/prompt-injection boundary restored
    - GOV-AUDIT-002 canonical governance routing hardened with regression test
    - GOV-AUDIT-003 direct Spark permission separated from central standing exception
    - GOV-AUDIT-004 waiting status restored to checkpoint enums
    - GOV-AUDIT-005 trusted-base prompt-evaluation evidence added with automated trials explicitly NOT_RUN
blockers: []
next_action: Require all trusted-base exact-head CI/security/lifecycle gates to reach terminal green on the audit-remediated candidate, re-inspect PR comments/reviews/threads and any actual Spark finding, then squash-merge PR #1600 and archive the task through a bounded closeout PR.
```
