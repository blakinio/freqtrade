---
task_id: FTAI-20260730-wickhunter-postmerge-ruff-repair
status: in_progress
branch: agent/wickhunter-postmerge-ruff-repair
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
dependencies:
  - PR #753 merged
  - AI Platform CI run 30531046030 failure reproduced on Gate 0 exact head
owned_paths:
  - docs/agents/tasks/FTAI-20260730-wickhunter-postmerge-ruff-repair.md
  - ai_platform/wickhunter/production_market_evidence_daemon.py
  - ai_platform/wickhunter/production_market_evidence_service.py
  - ai_platform/wickhunter/production_market_evidence_wh01.py
  - .github/workflows/wickhunter-postmerge-ruff-repair.yml
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

## Deliverables

- format the two reported import blocks;
- wrap the reported long exception line;
- replace two successive-pair `zip` loops with `itertools.pairwise`;
- narrow the reported complexity/noqa annotations;
- run Ruff, focused WickHunter tests and normal repository CI in one focused PR.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T11:55:00+02:00
head: 0208666d98849386e2f2d9acf534b13891e4afa2
branch: agent/wickhunter-postmerge-ruff-repair
pr: null
status: in_progress
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-wickhunter-postmerge-ruff-repair.md
  - ai_platform/wickhunter/production_market_evidence_daemon.py
  - ai_platform/wickhunter/production_market_evidence_service.py
  - ai_platform/wickhunter/production_market_evidence_wh01.py
  - .github/workflows/wickhunter-postmerge-ruff-repair.yml
proven:
  - AI Platform CI run 30531046030 passed 976 tests and failed Ruff with ten findings only in the three declared WickHunter files.
derived:
  - A separate focused repair PR preserves Gate 0 documentation ownership and allows normal synchronization after merge.
unknown:
  - Exact repair commit and focused CI conclusions.
conflicts: []
first_failure:
  marker: WICKHUNTER_POSTMERGE_RUFF
  evidence: Ruff reports E501, I001, C901, B905, RUF007 and RUF100 findings in the three declared files.
rejected_hypotheses:
  - Put unrelated WickHunter implementation edits into PR #767.
  - Bypass or ignore AI Platform CI.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-wickhunter-postmerge-ruff-repair.md
validation:
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-wickhunter-postmerge-ruff-repair.md --require-checkpoint
    result: PASS
    evidence: The repair checkpoint satisfies governance contract v1 before implementation.
blockers: []
next_action: Apply only the ten reported Ruff repairs, run focused validation, and open one focused PR to develop.
```
