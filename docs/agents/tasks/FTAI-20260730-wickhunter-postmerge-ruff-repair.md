---
task_id: FTAI-20260730-wickhunter-postmerge-ruff-repair
status: validating
branch: agent/wickhunter-postmerge-ruff-repair
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: 771
dependencies:
  - PR #753 merged
  - AI Platform CI run 30531046030 failure reproduced on Gate 0 exact head
owned_paths:
  - docs/agents/tasks/FTAI-20260730-wickhunter-postmerge-ruff-repair.md
  - ai_platform/wickhunter/production_market_evidence_daemon.py
  - ai_platform/wickhunter/production_market_evidence_service.py
  - ai_platform/wickhunter/production_market_evidence_wh01.py
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
search_first:
  - exact AI Platform CI Ruff output
  - current develop and active ownership for the three failed files
---

# WickHunter post-merge Ruff repair

## Goal

Repair only the ten Ruff regressions exposed after PR #753 merged, without changing WickHunter behavior or Gate 0 documentation scope.

## Delivered

- wrapped the one reported long exception line;
- organized the two reported import blocks;
- added only the two reported complexity annotations;
- replaced two successive-pair `zip` loops with `itertools.pairwise`;
- removed the one unused `noqa` selector;
- applied exact Ruff 0.15.21 formatting to the three declared files;
- removed both temporary branch-local repair workflows after they produced their commits.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T12:05:00+02:00
head: d8bf248e9be05e3f615047011176edfc64a6c456
branch: agent/wickhunter-postmerge-ruff-repair
pr: 771
status: validating
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-wickhunter-postmerge-ruff-repair.md
  - ai_platform/wickhunter/production_market_evidence_daemon.py
  - ai_platform/wickhunter/production_market_evidence_service.py
  - ai_platform/wickhunter/production_market_evidence_wh01.py
proven:
  - AI Platform CI run 30531046030 passed 976 tests and failed Ruff with ten findings only in the three declared WickHunter files.
  - The first repair commit passed Ruff check; AI Platform CI then proved that two files still required exact Ruff formatting.
  - The second branch-local repair run passed Ruff check and Ruff format check before committing the formatted files and deleting its helper workflow.
  - PR #771 contains only the three declared WickHunter files and this task record.
derived:
  - The repair preserves WickHunter behavior while restoring both lint and formatting gates required by Gate 0.
unknown:
  - Exact-head PR #771 CI conclusions and unresolved review-thread state after this checkpoint commit.
conflicts: []
first_failure:
  marker: EXACT_HEAD_VALIDATION_PENDING
  evidence: The lint and formatting repair is committed, but normal exact-head repository CI and review verification are still required before merge.
rejected_hypotheses:
  - Put unrelated WickHunter implementation edits into PR #767.
  - Bypass or ignore AI Platform CI.
  - Broaden the repair beyond the reported Ruff and formatting findings.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-wickhunter-postmerge-ruff-repair.md
  - ai_platform/wickhunter/production_market_evidence_daemon.py
  - ai_platform/wickhunter/production_market_evidence_service.py
  - ai_platform/wickhunter/production_market_evidence_wh01.py
validation:
  - command: ruff check <three-declared-WickHunter-files>
    result: PASS
    evidence: Ruff 0.15.21 accepted all three repaired files after the bounded changes.
  - command: ruff format --check <three-declared-WickHunter-files>
    result: PASS
    evidence: The branch-local formatting workflow committed only after exact Ruff formatting passed.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-wickhunter-postmerge-ruff-repair.md --require-checkpoint
    result: PASS
    evidence: The checkpoint satisfies governance contract v1.
blockers:
  - Exact-head required CI and review-thread verification are pending.
next_action: Verify PR #771 exact-head CI and review threads, repair only evidenced failures, synchronize normally if needed, and merge when green.
```
