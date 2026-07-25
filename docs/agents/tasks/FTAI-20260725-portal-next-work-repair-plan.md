---
task_id: FTAI-20260725-portal-next-work-repair-plan
status: done
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
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
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
- implementing PI-05, PI-06, PI-07 or PI-08;
- provisioning Cloudflare or protected GitHub staging;
- enabling private order submission or live capital.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T00:50:00+02:00
head: b1d71a161c3200ae22d6e4595dfe79b30ce1270b
branch: develop
pr: 310
status: done
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
owned_paths:
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260725-portal-next-work-repair-plan.md
proven:
  - P0-P10 are complete only for their declared bounded acceptance; P11 is blocked, P12 simulation-first is done, P13 is deferred and P14 is blocked.
  - PI-01, PI-02, PI-03 and PI-04 are complete for their declared repository-side acceptance.
  - PI-02 task FTAI-20260724-portal-pi02-authoritative-valuation is done and PR 267 merged as 0c8fdfe6fb50ff635403ae963484bf4e6883e1e1.
  - The control-plane API already exposes immutable revision and desired-state mutation endpoints for bots.
  - Current web bot surfaces do not expose the complete bot-scoped operations and lifecycle workflow.
  - NEXT_WORK_AND_REPAIR_PLAN.md now defines one concrete Bot Operations completion package with entry gates, deliverables, acceptance criteria, non-goals, dependency order and stop conditions.
  - PR 310 changed exactly the five declared documentation paths, passed required exact-head CI on c0d08f17c635704205d1c4caa41633ae150845cd and squash-merged as b1d71a161c3200ae22d6e4595dfe79b30ce1270b.
derived:
  - The next safe autonomous portal product package is Bot Operations convergence over existing canonical APIs, not PI-08 execution submission.
  - PI-05 through PI-08, P11, P13 and P14 must stay behind their existing provider, security, infrastructure, measured-need and owner gates.
unknown:
  - Exact Bot Operations owned paths must be declared after a fresh preflight because Liquid20 and other portal work may change web files.
conflicts:
  - Some older summary sentences in POST_P12_INTEGRATION_BACKLOG.md and the post-P12 paragraph in DELIVERY_ROADMAP.md still describe the historical PI-01/PI-02 routing. NEXT_WORK_AND_REPAIR_PLAN.md and merged task evidence are the current continuation source until a future owning package edits those large canonical files.
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
  - command: AI Platform CI on final PR 310 head c0d08f17c635704205d1c4caa41633ae150845cd
    result: PASS
    evidence: Workflow run 30177863964 completed successfully.
  - command: GitHub Actions Security Analysis with zizmor on final PR 310 head c0d08f17c635704205d1c4caa41633ae150845cd
    result: PASS
    evidence: Workflow run 30177863959 completed successfully.
  - command: Freqtrade CI on final PR 310 head c0d08f17c635704205d1c4caa41633ae150845cd
    result: PASS
    evidence: Workflow run 30177864162 completed successfully, including pre-commit, documentation build and CI Gate.
  - command: verify PR 310 merge
    result: PASS
    evidence: PR 310 merged at 2026-07-25T22:37:37Z as b1d71a161c3200ae22d6e4595dfe79b30ce1270b.
blockers: []
next_action: Declare a separate FTAI-YYYYMMDD-portal-bot-operations-completion task after a fresh develop/open-PR/path-ownership preflight, then implement only the bot-scoped operational convergence defined in NEXT_WORK_AND_REPAIR_PLAN.md.
```
