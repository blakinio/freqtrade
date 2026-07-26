---
task_id: FTAI-20260726-portal-pi06-identity-decision
status: done
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: 331
owned_paths:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
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
updated_at: 2026-07-26T09:45:00+02:00
head: bff49117b6572a065527ba75127c9aa938bf3119
branch: develop
pr: 331
status: done
context_routes:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
owned_paths:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-identity-decision.md
proven:
  - develop HEAD at task declaration was fa4158db5073bcdab34d3a41eb0b9af196821513.
  - Open PR 323 initially owned ARCHITECTURE_DECISIONS.md, README.md and UI_DELIVERY_STATUS.md but not the selected decision, plan or task paths.
  - PR 323 later merged as a86c955a1138e7fad1393a38f6a4406e6701f868; the decision branch was rebuilt on that exact develop head with no path conflict.
  - PI06_IDENTITY_AND_SESSION_DECISION.md accepts authentik as the product IdP, portal-owned tenant membership and authorization, BFF OIDC Authorization Code plus PKCE, opaque server-side sessions, MFA and step-up policy, recovery and revocation behavior, and supplemental Cloudflare Access.
  - Exact final PR head 90966789b305ce56b40155ca82e1f8637042df36 passed AI Platform CI 1346, Freqtrade CI 1627, GitHub Actions Security Analysis 1494, pre-commit and documentation build.
  - PR 331 squash-merged as bff49117b6572a065527ba75127c9aa938bf3119.
derived:
  - The PI-06 owner/product decision gate is resolved, but PI-06 implementation and real authentik/Cloudflare provisioning remain separate work.
unknown: []
conflicts: []
first_failure: null
rejected_hypotheses:
  - Use Cloudflare Access as the only product identity or tenant authorization source.
  - Store tenant membership authoritatively in browser claims, IdP groups or email-domain rules.
  - Store IdP access, ID or refresh tokens in browser-readable storage.
  - Start PI-07, PI-08, P11 acceptance or live capital as part of the identity decision.
changed_paths:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-identity-decision.md
validation:
  - final PR head 90966789b305ce56b40155ca82e1f8637042df36: AI Platform CI 1346 success.
  - final PR head 90966789b305ce56b40155ca82e1f8637042df36: Freqtrade CI 1627 success, including pre-commit and documentation build.
  - final PR head 90966789b305ce56b40155ca82e1f8637042df36: GitHub Actions Security Analysis 1494 success.
  - merge commit: bff49117b6572a065527ba75127c9aa938bf3119.
blockers: []
next_action: Declare the separate FTAI-YYYYMMDD-portal-pi06-product-identity-lifecycle implementation task after a fresh develop/open-PR/path-ownership preflight and implement only the versioned identity, session, membership, OIDC, CSRF, MFA, recovery and revocation scope defined in PI06_IDENTITY_AND_SESSION_DECISION.md.
```
