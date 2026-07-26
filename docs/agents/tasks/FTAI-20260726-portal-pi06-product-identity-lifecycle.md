---
task_id: FTAI-20260726-portal-pi06-product-identity-lifecycle
status: implementing
branch: feat/portal-pi06-product-identity-lifecycle
base_branch: develop
created: 2026-07-26
updated: 2026-07-26
related_pr: null
owned_paths:
  - ai_platform/portal/identity/
  - ai_platform/portal/control_plane/database.py
  - tests/ai_platform/portal/identity/
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-product-identity-lifecycle.md
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/SECURITY_ARCHITECTURE.md
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
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
updated_at: 2026-07-26T10:10:00+02:00
head: d1e728690fb74b346f1ffe61265281feab810e6b
branch: feat/portal-pi06-product-identity-lifecycle
pr: null
status: implementing
context_routes:
  - docs/ai_platform/portal/PI06_IDENTITY_AND_SESSION_DECISION.md
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md
  - docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md
owned_paths:
  - ai_platform/portal/identity/
  - ai_platform/portal/control_plane/database.py
  - tests/ai_platform/portal/identity/
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-product-identity-lifecycle.md
proven:
  - develop head at task declaration is d1e728690fb74b346f1ffe61265281feab810e6b.
  - Open PR 322 owns isolated RL-v2 files and open PR 109 owns only an inert design reference; neither overlaps this task.
  - PR 335 merged before declaration and owns only Liquidations AI-bot planning paths.
  - The accepted PI-06 decision selects authentik, portal-owned memberships, BFF OIDC plus PKCE, opaque local sessions, CSRF, MFA, five-minute step-up and synchronous revocation.
  - Existing control-plane create_app fails closed without an explicitly supplied trusted identity provider.
  - A local focused harness passes 12 identity lifecycle, OIDC and migration tests.
derived:
  - The first reviewable implementation package can deliver the Python identity backend without combining Next.js BFF work or external authentik provisioning.
unknown:
  - Exact repository CI outcome after files are committed.
  - Exact integration adjustments required by the full repository rather than the focused local harness.
conflicts: []
first_failure: null
rejected_hypotheses:
  - Replace product authorization with Cloudflare Access or IdP groups.
  - Store IdP tokens or raw portal session identifiers in the database.
  - Combine external Authentik deployment secrets with this repository backend package.
changed_paths:
  - ai_platform/portal/identity/__init__.py
  - ai_platform/portal/identity/crypto.py
  - ai_platform/portal/identity/http.py
  - ai_platform/portal/identity/models.py
  - ai_platform/portal/identity/oidc.py
  - ai_platform/portal/identity/repository.py
  - ai_platform/portal/identity/runtime.py
  - ai_platform/portal/identity/schema.py
  - ai_platform/portal/identity/service.py
  - ai_platform/portal/identity/migrations/0001_identity_lifecycle.sql
  - ai_platform/portal/control_plane/database.py
  - tests/ai_platform/portal/identity/test_identity_lifecycle.py
  - tests/ai_platform/portal/identity/test_migration.py
  - tests/ai_platform/portal/identity/test_oidc.py
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-product-identity-lifecycle.md
validation:
  - command: focused local pytest identity harness
    result: PASS
    evidence: 12 tests passed for OIDC, sessions, CSRF, MFA, revocation and migration behavior.
  - command: python py_compile and AST parse
    result: PASS
    evidence: all new Python files and tests parse and compile.
blockers: []
next_action: Commit the bounded implementation, open a PR, run exact-head repository CI and repair the first deterministic failure without expanding into BFF or deployment scope.
```
