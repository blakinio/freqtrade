---
task_id: FTAI-20260725-portal-next-work-repair-plan
status: implementing
branch: docs/portal-next-work-repair-sync-20260725
base_branch: develop
created: 2026-07-25
updated: 2026-07-25
related_pr: null
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
updated_at: 2026-07-25T23:20:00+02:00
head: 2fc4c7617454a1daffaf1908d7b0ef55532af70a
branch: docs/portal-next-work-repair-sync-20260725
pr: null
status: implementing
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
  - Open portal PR 307 currently owns only docs/agents/tasks/FTAI-20260725-portal-liquidations-read-model.md; PR 304 owns the Liquid20 prompt and pre-commit config, so this task has disjoint paths.
derived:
  - The next safe autonomous portal product package is Bot Operations convergence over existing canonical APIs, not PI-08 execution submission.
  - A dedicated continuation document is needed because status-bearing portal documents have drifted at different times.
unknown:
  - Exact final Bot Operations owned paths must be declared after a fresh preflight because concurrent portal work may change web files.
conflicts:
  - POST_P12_INTEGRATION_BACKLOG.md and older program/roadmap routing still describe PI-02 as active or PI-01 as next despite merged completion evidence.
first_failure:
  marker: NONE
  evidence: Documentation-only task; no validation failure observed yet.
rejected_hypotheses:
  - Treat bounded P6 completion as proof that the full target Bot Operations workflow exists.
  - Treat simulator execution as proof that private Freqtrade order submission exists.
  - Start PI-06, PI-05 or PI-07 without owner/provider/security decisions.
changed_paths:
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260725-portal-next-work-repair-plan.md
validation: []
blockers: []
next_action: Update portal README, UI status and program routing on this branch, then open a documentation PR and validate its exact head.
```
