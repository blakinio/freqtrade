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
  - ai_platform/portal/web/components/market-evidence-dashboard.tsx
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md
search_first:
  - exact AI Platform CI Ruff and codespell output
  - current develop and active ownership for the failed files
---

# WickHunter post-merge Ruff repair

## Goal

Repair only the lint, formatting and one UI-label regression exposed after PR #753 merged, without changing WickHunter behavior or Gate 0 documentation scope.

## Delivered

- repaired the ten reported Ruff findings in three WickHunter files;
- applied exact Ruff 0.15.21 formatting;
- changed the mixed-language `Symbole` label to the precise Polish `Aktywne pary` after exact-head codespell identified it;
- removed both temporary branch-local repair workflows after they produced their commits.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T12:10:00+02:00
head: 2ecf80a4aba874c37827da833276aa534b348be7
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
  - ai_platform/portal/web/components/market-evidence-dashboard.tsx
proven:
  - AI Platform CI initially passed 976 tests and exposed ten Ruff findings in three files merged by PR #753.
  - The bounded Ruff repair passed lint; exact-head CI then identified and the second repair cleared two formatting differences.
  - The next exact-head CI passed tests, Ruff and Ruff format and identified only `Symbole` in the English/Polish UI label through codespell.
  - The label now states `Aktywne pary`, which matches the displayed active-symbol count without changing behavior.
derived:
  - The repair remains a bounded post-merge quality correction and restores all known static gates required by Gate 0.
unknown:
  - Exact-head PR #771 CI conclusions and unresolved review-thread state after this checkpoint commit.
conflicts: []
first_failure:
  marker: EXACT_HEAD_VALIDATION_PENDING
  evidence: All currently evidenced issues are repaired; normal exact-head repository CI and review verification are still required before merge.
rejected_hypotheses:
  - Put unrelated WickHunter implementation edits into PR #767.
  - Bypass or ignore AI Platform CI.
  - Suppress codespell instead of correcting the mixed-language label.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-wickhunter-postmerge-ruff-repair.md
  - ai_platform/wickhunter/production_market_evidence_daemon.py
  - ai_platform/wickhunter/production_market_evidence_service.py
  - ai_platform/wickhunter/production_market_evidence_wh01.py
  - ai_platform/portal/web/components/market-evidence-dashboard.tsx
validation:
  - command: ruff check <three-declared-WickHunter-files>
    result: PASS
    evidence: Ruff 0.15.21 accepted all three repaired files.
  - command: ruff format --check <three-declared-WickHunter-files>
    result: PASS
    evidence: Exact Ruff formatting passed before the formatting commit.
  - command: codespell AGENTS.md ai_platform docs/ai_platform tests/ai_platform
    result: FAIL
    evidence: Before the label repair, exact-head CI reported only `market-evidence-dashboard.tsx:289: Symbole`.
  - command: python tools/agents/checkpoint.py docs/agents/tasks/FTAI-20260730-wickhunter-postmerge-ruff-repair.md --require-checkpoint
    result: PASS
    evidence: The checkpoint satisfies governance contract v1.
blockers:
  - Exact-head required CI and review-thread verification are pending.
next_action: Verify PR #771 exact-head CI and review threads, repair only evidenced failures, synchronize normally if needed, and merge when green.
```
