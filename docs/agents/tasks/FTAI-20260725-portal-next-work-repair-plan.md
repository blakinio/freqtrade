---
task_id: FTAI-20260725-portal-next-work-repair-plan
status: ready
branch: docs/portal-next-work-repair-sync-20260725
base_branch: develop
created: 2026-07-25
updated: 2026-07-26
related_pr: 310
owned_paths:
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260725-portal-next-work-repair-plan.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
---

# Portal Next Work and Repair Plan

## Goal

Create a durable, repository-grounded continuation route that corrects stale portal status claims, distinguishes bounded stage completion from product/infrastructure completion and gives the next agent one concrete software package with entry gates, deliverables, acceptance and non-goals.

## Scope

- add `NEXT_WORK_AND_REPAIR_PLAN.md` as the current continuation ledger;
- record PI-02 as completed from merged PR #267;
- document the Bot Operations product gap and route it as the recommended next autonomous portal package;
- update portal README, UI status and program routing to point future agents to the plan;
- preserve all P11, P13, P14, Phase 6, protected-holdout, credential and live-capital boundaries.

## Non-goals

- implementing Bot Operations in this documentation task;
- changing application runtime or tests;
- modifying Liquid20 work owned by open PRs #304 or #307;
- implementing PI-05, PI-06, PI-07 or PI-08;
- provisioning Cloudflare or protected GitHub staging;
- enabling private order submission or live capital.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T00:40:00+02:00
head: 9dd77cd0729069a432aa26a888987c0afe1d0766
branch: docs/portal-next-work-repair-sync-20260725
pr: 310
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
owned_paths:
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260725-portal-next-work-repair-plan.md
proven:
  - P0-P10 are complete only for their declared bounded acceptance; P11 is blocked, P12 simulation-first is done, P13 is deferred and P14 is blocked.
  - PI-01, PI-03 and PI-04 are complete according to current portal records.
  - PI-02 task FTAI-20260724-portal-pi02-authoritative-valuation is done and PR 267 merged as 0c8fdfe6fb50ff635403ae963484bf4e6883e1e1.
  - The control-plane API already exposes immutable revision and desired-state mutation endpoints for bots.
  - Current web bot surfaces do not expose the complete bot-scoped operations and lifecycle workflow.
  - PR 310 contains exactly the five declared documentation paths and is based on develop cb001ac2c13bcefc8c979b89113d92d87657e6e8.
  - Exact-head validation on 9dd77cd0729069a432aa26a888987c0afe1d0766 passed AI Platform CI, zizmor and Freqtrade CI including pre-commit, documentation build and CI Gate.
derived:
  - The next safe autonomous portal product package is Bot Operations convergence over existing canonical APIs, not PI-08 execution submission.
  - A dedicated continuation document is needed because status-bearing portal documents have drifted at different times.
unknown:
  - Exact final Bot Operations owned paths must be declared after a fresh preflight because concurrent portal work may change web files.
conflicts:
  - POST_P12_INTEGRATION_BACKLOG.md and the older post-P12 paragraph in DELIVERY_ROADMAP.md still contain stale PI-02/PI-01 routing sentences; NEXT_WORK_AND_REPAIR_PLAN.md is the current continuation ledger until those large canonical files are updated by their next owning package.
first_failure:
  marker: precommit-end-of-file-fixer-missing-newline
  evidence: Freqtrade CI run 30176794971, Pre-commit checks job 89726818422 failed on PR head 688f2cb385a08b6be24c0ff65c53f439a38fb1ca; the PR patch showed NEXT_WORK_AND_REPAIR_PLAN.md with no newline at end of file. Commit edb2899e0276adcb9538609368e42af5de63e838 restored the required final newline.
rejected_hypotheses:
  - Treat bounded P6 completion as proof that the full target Bot Operations workflow exists.
  - Treat simulator execution as proof that private Freqtrade order submission exists.
  - Start PI-06, PI-05 or PI-07 without owner/provider/security decisions.
  - Treat the first Freqtrade CI failure as transient or merge despite a deterministic pre-commit defect.
changed_paths:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260725-portal-next-work-repair-plan.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
validation:
  - command: compare develop...docs/portal-next-work-repair-sync-20260725
    result: PASS
    evidence: The branch changed exactly the five declared documentation paths before validation repair.
  - command: AI Platform CI on PR head 9dd77cd0729069a432aa26a888987c0afe1d0766
    result: PASS
    evidence: Workflow run 30177790660 completed successfully.
  - command: GitHub Actions Security Analysis with zizmor on PR head 9dd77cd0729069a432aa26a888987c0afe1d0766
    result: PASS
    evidence: Workflow run 30177790656 completed successfully.
  - command: Freqtrade CI on PR head 9dd77cd0729069a432aa26a888987c0afe1d0766
    result: PASS
    evidence: Workflow run 30177790706 completed successfully; Pre-commit checks job 89729340016, Documentation build job 89729373188 and CI Gate job 89729406459 all passed.
  - command: required GitHub Actions on final checkpoint-only PR head
    result: PENDING
    evidence: This checkpoint update creates one final exact head that must pass required workflows before merge.
blockers: []
next_action: Verify all required workflows on the exact final PR 310 head; if they pass and the PR remains mergeable and path-disjoint, squash-merge with expected_head_sha, verify develop, and leave Bot Operations for a separate dated implementation task.
```
