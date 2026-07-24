---
task_id: FTAI-20260724-portal-post-p12-integration-backlog
status: active
branch: docs/portal-post-p12-integration-backlog-20260724
base_branch: develop
created: 2026-07-24
updated: 2026-07-24
related_pr: null
owned_paths:
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/ai_platform/portal/README.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
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
updated_at: 2026-07-24T07:00:00+02:00
head: 0e4e104407b74ddcfe219d6cd1881804b371aa35
branch: docs/portal-post-p12-integration-backlog-20260724
pr: null
status: active
context_routes:
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/DELIVERY_ROADMAP.md
  - docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md
  - docs/ai_platform/portal/UI_DELIVERY_STATUS.md
proven:
  - PR #232 merged the remaining software-addressable portal product capabilities into develop as 0e4e104407b74ddcfe219d6cd1881804b371aa35.
  - develop equals that merge commit at task declaration.
  - P11 is blocked on real owner-approved Cloudflare/protected GitHub staging infrastructure and External E2E.
  - P13 is deferred after a measured-need NO-GO decision.
  - P14 is blocked and the portal program does not authorize live capital.
  - Remaining partial states are authoritative-source/private-integration gaps rather than missing presentation shells.
derived:
  - A cross-cutting integration backlog should use package IDs separate from P0-P14 to avoid changing established roadmap semantics.
  - Private runtime reads and private approved-intent submission require separate packages because their security and capital risks differ materially.
unknown: []
conflicts: []
first_failure:
  marker: none
  evidence: Documentation task declared after live develop/open-PR preflight; no validation has run yet.
changed_paths:
  - docs/agents/tasks/FTAI-20260724-portal-post-p12-integration-backlog.md
validation: []
blockers: []
next_action: Create the canonical post-P12 integration backlog and link it from the portal roadmap, architecture, program, agent plan and UI delivery status.
```
