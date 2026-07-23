---
task_id: FTAI-20260723-portal-roadmap-architecture-sync
status: done
branch: docs/portal-roadmap-architecture-sync-20260723
base_branch: develop
created: 2026-07-23
updated: 2026-07-23
related_pr: "#226"
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
updated_at: 2026-07-23T20:37:00+02:00
head: 3c30be3488f03dadc23cda5ee6ccdc856b2ced79
branch: docs/portal-roadmap-architecture-sync-20260723
pr: "#226"
status: ready
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
  - develop HEAD at task preflight was d3e29ac9ceb7bd55aa0cc53ac515a5b184e685ba and remained the PR base through the validated content head.
  - No open PR owned the canonical portal roadmap/program paths; open PR #109 is unrelated design-reference work.
  - P0-P10 are complete for their actually merged bounded acceptance scopes; P11 real external acceptance is blocked, P12 simulation-first acceptance is complete, P13 scale implementation is deferred after NO-GO assessment, and P14 remains blocked.
  - The roadmap now narrows P3, P4, P6, P8 and P9 completion claims to their actually delivered bounded scopes rather than implying undelivered later infrastructure or UI work.
  - P11 repository-side policy, verifier, workflow and runbooks are merged, but real Cloudflare/protected GitHub External E2E has not been proven and remains mandatory.
  - FreqtradeExecutionAdapter.submit_approved_intent and the default terminal submitter both fail closed with ORDER_SUBMISSION_NOT_IMPLEMENTED.
  - ExecutionMode contains only simulated and dry_run; P3 accepts only dry_run lifecycle while P10 provides deterministic simulated order submission.
  - SYSTEM_ARCHITECTURE and AGENT_EXECUTION_PLAN now use the canonical ApprovedExecutionIntent boundary and do not imply that P10 proves real Freqtrade order submission.
  - P13 assessment PR #224 found no measured bottleneck or unmet SLO that justifies service extraction or additional scale infrastructure.
  - Historical P8/P9 task frontmatter remains stale, but PR #147 and PR #158 are merged with required CI evidence; canonical status follows live merge/CI state rather than stale task frontmatter.
  - PR #226 content head 3c30be3488f03dadc23cda5ee6ccdc856b2ced79 is mergeable and passed AI Platform CI, Freqtrade CI and zizmor.
derived:
  - Production-like staging is not complete because real P11 protected external ingress evidence does not exist.
  - Real trading is not implemented; the concrete risk-approved private order-submission transport to Freqtrade plus real query/reconciliation and credential integration remain separate future work.
  - P12 simulated repair evidence cannot substitute for P11 and P13 NO-GO does not block eventual P11 execution.
unknown:
  - Whether owner-approved real Cloudflare staging resources and protected GitHub staging variables/secrets currently exist outside the accessible repository state.
conflicts: []
first_failure:
  marker: canonical-roadmap-status-drift
  evidence: The pre-task DELIVERY_ROADMAP marked P0 active, P1-P10 planned and P13 planned despite merged implementation/acceptance evidence and the P13 NO-GO assessment.
rejected_hypotheses:
  - Treat P12 simulation-first completion as proof that real P11 staging acceptance passed.
  - Mark P13 scale/service extraction implemented merely because its measured-need assessment completed.
  - Claim that P3/P7/P10 provide a real Freqtrade or exchange order-submission path.
  - Modify stale historical P8/P9 task records outside this task's declared ownership instead of using live merge and CI state.
changed_paths:
  - docs/agents/tasks/FTAI-20260723-portal-roadmap-architecture-sync.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
validation:
  - command: AI Platform CI run 30034025003
    result: PASS
    evidence: AI platform tests/lint, Ruff, Ruff format, Codespell and JSON validation passed on content head 3c30be3488f03dadc23cda5ee6ccdc856b2ced79.
  - command: Freqtrade CI run 30034028878
    result: PASS
    evidence: CI scope, pre-commit checks, documentation syntax/build and final CI Gate passed on the content head; non-applicable runtime matrices were skipped for docs-only scope.
  - command: GitHub Actions Security Analysis with zizmor run 30034024978
    result: PASS
    evidence: Workflow security analysis passed on the content head.
  - command: Pre-commit Types update run 30034025089
    result: NOT_RUN
    evidence: Workflow concluded skipped for this docs-only change and is not a failure gate.
blockers: []
next_action: After this documentation sync is merged, resume real P11 External E2E only when the owner intentionally provisions or approves the Cloudflare and protected GitHub staging infrastructure; do not start P14 or enable live capital.
```
