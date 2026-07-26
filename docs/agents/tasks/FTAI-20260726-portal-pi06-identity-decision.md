---
task_id: FTAI-20260726-portal-pi06-identity-decision
status: active
branch: docs/portal-pi06-identity-decision-20260726
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: null
owned_paths:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-identity-decision.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
---

# PI-06 Product Identity Decision

## Goal

Select and durably record the product identity provider, tenant-membership source, session, MFA, recovery and revocation policies required to unblock a separate PI-06 implementation task without weakening application authorization or treating Cloudflare Access as the product identity layer.

## Boundaries

- Documentation and decision evidence only; no identity runtime, login flow, user database, secret or deployment is changed.
- Cloudflare Access remains supplemental defense for privileged surfaces and is not the sole application identity or authorization boundary.
- Tenant membership and capability authorization remain server-side and fail closed.
- No PI-07, PI-08, P11 acceptance, P14 or live-capital authorization.
- Frozen research thresholds, Phase 6 evidence and protected holdout policy remain unchanged.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T09:30:00+02:00
head: fa4158db5073bcdab34d3a41eb0b9af196821513
branch: docs/portal-pi06-identity-decision-20260726
pr: null
status: active
context_routes:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
owned_paths:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-identity-decision.md
proven:
  - develop HEAD at task declaration is fa4158db5073bcdab34d3a41eb0b9af196821513.
  - Open PR 323 owns ARCHITECTURE_DECISIONS.md, README.md and UI_DELIVERY_STATUS.md but not the selected decision, plan, backlog or task paths.
  - PI-06 is planned and its explicit entry blocker is the missing IdP, membership, session, MFA, recovery and revocation decision.
  - The deployment target is Linux containers on Synology behind Cloudflare Tunnel, while application RBAC and tenant isolation remain mandatory.
derived:
  - A bounded documentation decision package can resolve the owner/product gate without starting identity implementation or external provisioning.
unknown:
  - Exact CI outcome after the decision documents are written.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Use Cloudflare Access as the only product identity or tenant authorization source.
  - Store tenant membership authoritatively in browser claims or email-domain rules.
  - Start PI-06 implementation before exact session, MFA, recovery and revocation policies are versioned.
changed_paths:
  - docs/agents/tasks/FTAI-20260726-portal-pi06-identity-decision.md
validation: []
blockers: []
next_action: Record the selected PI-06 architecture and policies, update the continuation/backlog routing, then open a documentation PR and require exact-head CI.
```
