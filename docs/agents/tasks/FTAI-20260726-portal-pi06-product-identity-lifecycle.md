---
task_id: FTAI-20260726-portal-pi06-product-identity-lifecycle
status: done
branch: develop
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: 341
owned_paths:
  - ai_platform/portal/identity/
  - ai_platform/portal/control_plane/database.py
  - tests/ai_platform/portal/identity/
  - .github/workflows/ai-platform.yml
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-product-identity-lifecycle.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
---

# PI-06 Product Identity Lifecycle

## Goal

Implement the bounded repository backend for real product identity: OIDC Authorization Code plus PKCE, opaque local sessions, portal-owned tenant memberships and capabilities, CSRF, MFA and step-up enforcement, logout/revocation/back-channel logout, migrations and deterministic security tests.

## Boundaries

- No committed IdP endpoint, client secret, cookie key, user credential or production identity data.
- No authentik or Cloudflare provisioning; target deployment and real acceptance remain separate.
- No browser-readable access, ID or refresh token.
- No IdP group, email or browser tenant field becomes product membership authority.
- No PI-07, PI-08, P11 acceptance, P14 or live-capital behavior.
- Existing risk, audit, Phase 6, thresholds and protected holdout contracts remain unchanged.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-26T11:25:00+02:00
head: 41834d18f3a05b0dfa44dc5af9b97942e685d2a1
branch: develop
pr: 341
status: done
context_routes:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
owned_paths:
  - ai_platform/portal/identity/
  - ai_platform/portal/control_plane/database.py
  - tests/ai_platform/portal/identity/
  - .github/workflows/ai-platform.yml
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-product-identity-lifecycle.md
proven:
  - PR 341 delivered the bounded Python identity backend, migration, tests, implementation documentation and required lightweight CI dependencies.
  - OIDC discovery, signed JWKS validation, issuer, audience, nonce, PKCE and one-time state are enforced server-side.
  - Portal sessions are opaque; storage contains keyed token hashes rather than browser tokens or IdP access, ID or refresh tokens.
  - Tenant and capability context is derived from a current portal-owned membership, with MFA, five-minute step-up, CSRF and synchronous membership/session revocation.
  - Exact final PR head c258567cabd1c9ddf3d90c63f36319be99463978 passed AI Platform CI 1415, Freqtrade CI 1713 and GitHub Actions Security Analysis 1580.
  - Freqtrade CI 1713 passed pre-commit, documentation, Python 3.11, 3.12 coverage, 3.13, 3.14, distribution build and the final CI gate.
  - PR 341 squash-merged as 41834d18f3a05b0dfa44dc5af9b97942e685d2a1.
derived:
  - The repository backend is complete as a bounded package without combining Next.js BFF work or real authentik/Cloudflare provisioning.
  - Full PI-06 remains active because browser BFF integration, browser E2E, recovery verification and target-environment provisioning are separate evidence gates.
unknown: []
conflicts: []
first_failure:
  marker: AI_PLATFORM_LIGHTWEIGHT_DEPENDENCIES
  evidence: The first PR run could not collect the identity tests because the lightweight AI workflow omitted pyjwt and cryptography; after adding the existing project dependencies, the next full suite exposed a duplicate test module name, followed by deterministic Ruff/format findings. All defects were repaired, and temporary diagnostic workflows were removed from the final diff.
rejected_hypotheses:
  - Replace product authorization with Cloudflare Access or IdP groups.
  - Store IdP tokens or raw portal session identifiers in the database.
  - Combine external Authentik deployment secrets with this repository backend package.
  - Retain a temporary diagnostic workflow in the merge candidate.
changed_paths:
  - .github/workflows/ai-platform.yml
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/identity/
  - tests/ai_platform/portal/identity/
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-product-identity-lifecycle.md
validation:
  - command: focused local pytest identity harness
    result: PASS
    evidence: 12 tests passed for OIDC, sessions, CSRF, MFA, revocation and migration behavior.
  - command: final AI Platform CI 1415
    result: PASS
    evidence: full AI tests, Ruff, Ruff format, codespell and JSON validation passed.
  - command: final Freqtrade CI 1713
    result: PASS
    evidence: pre-commit, documentation, Python 3.11-3.14, coverage, mypy, build and CI gate passed.
  - command: final GitHub Actions Security Analysis 1580
    result: PASS
    evidence: zizmor completed successfully and no temporary diagnostic workflow remained.
  - command: squash merge
    result: PASS
    evidence: PR 341 merged as 41834d18f3a05b0dfa44dc5af9b97942e685d2a1.
blockers: []
next_action: Declare the bounded PI-06 same-origin BFF and browser-session integration package, connect the Next.js portal to the merged identity backend, and prove denied, expired, revoked, CSRF, MFA/step-up and cross-tenant states with deterministic browser E2E before any real authentik or Cloudflare provisioning.
```
