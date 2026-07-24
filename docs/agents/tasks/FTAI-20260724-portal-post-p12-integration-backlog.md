---
task_id: FTAI-20260724-portal-post-p12-integration-backlog
status: done
branch: docs/portal-post-p12-integration-backlog-20260724
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: "#233"
owned_paths:
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-post-p12-integration-backlog.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/DATA_AND_OBSERVABILITY_ARCHITECTURE.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
---

# AI Trading Portal — Post-P12 Integration Backlog

## Goal

Create one canonical, dependency-ordered backlog for the remaining hard external/private integration boundaries after completion of the software-addressable portal surfaces, without renumbering P0-P14, activating live capital or weakening fail-closed execution and research boundaries.

## Deliverables

- canonical post-P12 integration backlog with stable work-package IDs;
- entry gates, dependencies, acceptance criteria and non-goals for every remaining integration;
- explicit separation between software packages, owner/external infrastructure gates, measured-need work and live-capital readiness;
- roadmap, architecture, program and UI-status cross-links;
- one recommended next software package without silently activating implementation.

## Non-negotiable boundaries

- No runtime implementation, infrastructure provisioning, Cloudflare mutation, secret handling or deployment.
- No real order submission, live-capital authorization or P14 activation.
- No protected final-holdout access, Phase 6 mutation, threshold change or model promotion.
- P11 remains blocked until real owner-approved external infrastructure and External E2E evidence exist.
- P13 remains deferred until measured bottleneck/SLO evidence exists.
- Every implementation package declared from this backlog requires a separate task, branch, ownership and CI evidence.

## Acceptance criteria

1. Every remaining hard boundary in `UI_DELIVERY_STATUS.md` maps to exactly one primary future work package or governed stage.
2. Read-only runtime integration and approved-intent submission are separate packages with different risk gates.
3. Dependencies prevent unrealized PNL, drift, logs, identity and notification claims without authoritative sources.
4. P11, P13 and P14 retain their existing blocked/deferred semantics.
5. Architecture, roadmap, program and agent execution documentation point to the same canonical backlog.
6. Documentation validation and required repository CI pass before merge.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-24T07:30:00+02:00
head: b17a3bc7637590cf6dbb6d211b345fa501855d74
branch: docs/portal-post-p12-integration-backlog-20260724
pr: "#233"
status: ready
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
proven:
  - PR #232 merged the remaining software-addressable portal product capabilities into develop as 0e4e104407b74ddcfe219d6cd1881804b371aa35.
  - develop equals that merge commit at task declaration and the documentation branch is behind_by=0.
  - P11 is blocked on real owner-approved Cloudflare/protected GitHub staging infrastructure and External E2E.
  - P13 is deferred after a measured-need NO-GO decision.
  - P14 is blocked and the portal program does not authorize live capital.
  - Remaining partial states are authoritative-source/private-integration gaps rather than missing presentation shells.
  - POST_P12_INTEGRATION_BACKLOG.md defines PI-01 through PI-08 with entry gates, dependencies, deliverables, acceptance criteria and non-goals.
  - UI delivery boundaries map to exactly one PI package or the existing P11 gate.
  - ADR-016 preserves P0-P14 semantics and separates runtime reads, credential brokering and approved-intent submission.
  - Delivery roadmap, portal index, program record and agent execution plan route future work to the same backlog.
  - AI Platform CI run 30069018717 passed on the final content head.
  - Freqtrade CI run 30069018719 passed scope classification, pre-commit and documentation build; runtime matrices were correctly skipped for docs-only changes.
  - zizmor run 30069018757 passed on the final content head.
derived:
  - PI-01 Private Runtime Read and Reconciliation is the lowest-risk next software package and a prerequisite for valuation and reconciled dry-run submission.
  - PI-03, PI-04 and PI-06 may proceed in parallel only after ownership and shared-contract checks.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: No documentation or repository validation failure was observed.
changed_paths:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/agents/tasks/FTAI-20260724-portal-post-p12-integration-backlog.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
validation:
  - command: AI Platform CI 30069018717
    result: PASS
  - command: Freqtrade CI 30069018719
    result: PASS
  - command: GitHub Actions Security Analysis with zizmor 30069018757
    result: PASS
blockers: []
next_action: Merge PR #233 into develop, then use PI-01 as the next separately declared software package unless the owner intentionally starts the existing P11 external infrastructure gate first.
```
