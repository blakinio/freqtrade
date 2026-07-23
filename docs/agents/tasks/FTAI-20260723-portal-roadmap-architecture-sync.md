---
task_id: FTAI-20260723-portal-roadmap-architecture-sync
status: active
branch: docs/portal-roadmap-architecture-sync-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: null
owned_paths:
  - docs/agents/tasks/FTAI-20260723-portal-roadmap-architecture-sync.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md
  - docs/ai_platform/portal/QUALITY_AND_AUTONOMOUS_E2E.md
search_first:
  - current develop HEAD and portal PR/CI state
  - active portal task ownership and overlapping owned paths
  - P10-P13 durable task records
  - current execution adapter and terminal submission behavior
optional_reads:
  - docs/ai_platform/portal/EXECUTION_ADAPTER.md
  - docs/ai_platform/portal/TRADING_TERMINAL_FOUNDATION.md
---

# AI Trading Portal — Roadmap and Architecture Sync

## Goal

Synchronize the canonical AI Trading Portal program and delivery roadmap with live repository evidence, while preserving the distinction between repository-side implementation, real production-like staging acceptance, measured scale need and explicit live-capital authorization.

## Non-negotiable boundaries

- Do not change frozen thresholds `0.006/-0.009`.
- Do not access or iteratively use protected final holdout `20260801-20260930`.
- Do not reopen completed Phase 6 or change authoritative `selected_model = null`.
- Do not reinterpret PyTorch/RL evidence as production approval.
- Do not enable live capital, withdrawals, public Freqtrade access or production exchange-secret access.
- Do not claim real P11 Cloudflare acceptance from repository, CI or simulated evidence.

## Acceptance criteria

1. P0-P14 statuses in the canonical portal roadmap match merged implementation/task evidence.
2. P11 clearly separates repository-side foundation from real Cloudflare/protected GitHub External E2E acceptance.
3. P12 simulation-first completion is not presented as P11 acceptance.
4. P13 records the measured-need NO-GO/deferred decision without requiring service extraction.
5. Current execution reality documents that `submit_approved_intent` remains fail-closed with `ORDER_SUBMISSION_NOT_IMPLEMENTED` and no real Freqtrade order-submission path exists.
6. Program next action points to exactly one real next step and does not authorize P14/live capital.
7. Modified documentation passes applicable repository CI and task/checkpoint governance validation available in the execution environment.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-23T20:45:00+02:00
head: d3e29ac9ceb7bd55aa0cc53ac515a5b184e685ba
branch: docs/portal-roadmap-architecture-sync-20260723
pr: null
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
owned_paths:
  - docs/agents/tasks/FTAI-20260723-portal-roadmap-architecture-sync.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
proven:
  - develop HEAD is d3e29ac9ceb7bd55aa0cc53ac515a5b184e685ba.
  - The only open user PR is #109 and it does not own canonical portal roadmap/program paths.
  - P10 is done; P11 repository-side foundation is merged but real External E2E remains blocked/deferred; P12 simulation-first acceptance is done; P13 assessment ended in measured-need NO-GO.
  - FreqtradeExecutionAdapter.submit_approved_intent and the default terminal submitter both fail closed with ORDER_SUBMISSION_NOT_IMPLEMENTED.
  - ExecutionMode contains only simulated and dry_run; P3 accepts only dry_run and P10 provides deterministic simulated execution.
  - Current develop-tip source PR #225 passed Freqtrade CI and zizmor; Pre-commit Types was skipped.
derived:
  - Canonical DELIVERY_ROADMAP statuses P0-P10 and P13 are stale relative to repository evidence.
  - Production-like staging is not complete because real P11 Cloudflare/protected GitHub External E2E evidence does not exist.
  - Real trading is not implemented and remains outside this documentation-sync scope.
unknown:
  - Whether owner-approved real Cloudflare staging resources and protected GitHub staging variables/secrets currently exist outside the accessible repository state.
conflicts: []
first_failure:
  marker: canonical-roadmap-status-drift
  evidence: DELIVERY_ROADMAP still marks P0 active and P1-P10 planned despite merged implementation and closeout evidence through P12, while P13 assessment is not represented.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-portal-roadmap-architecture-sync.md
validation: []
blockers: []
next_action: Update the canonical portal roadmap/program to match live implementation evidence and document the fail-closed execution/P11/P13 boundaries without enabling live capital.
```
