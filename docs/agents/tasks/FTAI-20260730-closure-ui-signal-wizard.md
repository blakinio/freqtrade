---
task_id: FTAI-20260730-closure-ui-signal-wizard
status: ready
dispatch_state: READY
branch: agent/closure-ui-signal-wizard-v2
base_branch: develop
created: 2026-07-30
updated: 2026-07-31
related_pr: 818
terminal_pr: 820
unblock_pr: 830
correlation_blocker_pr: 832
context_repair_pr: 846
context_repair_merge: 367a51b610d2a34ee5841bc0b86622bd64fc6858
semantic_hardening_task: FTAI-20260731-closure-signal-wizard-context-hardening
semantic_hardening_pr: 858
semantic_hardening_head: 6604dbbfa41ed52b29b33697f4b56c890bc30435
semantic_hardening_merge: da86b55310a3c3575ad3168743cd1062f1387d6d
semantic_hardening_workflows:
  ai_platform_ci: 30616727960
  freqtrade_ci: 30616729952
  security_analysis: 30616727733
implementation_pr: 855
backend_task: FTAI-20260730-closure-signal-wizard-backend
backend_pr: 825
backend_merge: 0bc35521debd33312820dfad9f010e22aa651610
dependencies:
  - FTAI-20260730-closure-contracts merged as 6e489f7e10199120424cbcd01b3e125711630243
  - FTAI-20260730-closure-signal-wizard-backend merged as 0bc35521debd33312820dfad9f010e22aa651610
  - FTAI-20260731-signal-wizard-context-repair merged as 367a51b610d2a34ee5841bc0b86622bd64fc6858
  - FTAI-20260731-closure-signal-wizard-context-hardening merged as da86b55310a3c3575ad3168743cd1062f1387d6d
owned_paths:
  - docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md
  - ai_platform/portal/web/app/ai/signal-wizard/page.tsx
  - ai_platform/portal/web/app/ai/signal-wizard/signal-wizard-client.tsx
  - ai_platform/portal/web/app/api/ai/signal-wizard/preview/route.ts
  - ai_platform/portal/web/app/api/ai/signal-wizard/submit/route.ts
  - ai_platform/portal/web/lib/signal-wizard-api.ts
  - ai_platform/portal/web/lib/signal-wizard-contracts.ts
  - ai_platform/portal/web/e2e/signal-wizard-closure.spec.ts
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
  - ai_strategy_engine/TASKS.md
---

# Closure Signal Wizard UI

## Goal

Build the complete research-only Signal Wizard against the frozen typed DSL and canonical identity-enabled Signal Wizard backend/API.

## READY gate

The focused backend semantic/persistence hardening PR #858 merged normally into `develop` as `da86b55310a3c3575ad3168743cd1062f1387d6d`.

Its exact implementation head `6604dbbfa41ed52b29b33697f4b56c890bc30435` passed all required workflows:

- AI Platform CI: `30616727960`;
- Freqtrade CI: `30616729952`;
- GitHub Actions Security Analysis with zizmor: `30616727733`.

The PR has zero unresolved review threads. The backend dependency is therefore complete and this frontend task is `READY`.

## Safety

Submit remains research-only and grants no deployment, execution, promotion, protected-holdout or live-capital authority. Browser-direct access to Freqtrade, exchange or Vault endpoints remains prohibited.

## Next action

Resume PR #855 from current `develop`, verify exact-head frontend CI and zero unresolved review threads, then merge normally.
