---
task_id: FTAI-20260726-portal-pi06-product-identity-lifecycle
status: reviewing
branch: feat/portal-pi06-product-identity-lifecycle
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
updated_at: 2026-07-26T11:08:00+02:00
head: 45b6819bd9d71985d5d64892ae00d8e97c9f98bc
branch: feat/portal-pi06-product-identity-lifecycle
pr: 341
status: reviewing
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
  - develop head at task declaration was d1e728690fb74b346f1ffe61265281feab810e6b.
  - The branch was rebuilt on RL-v2 implementation merge 3c2959545a6570d24e6bf8477a9442dbf3772bb2 and then merged cleanly with current develop 7163382aad52e59326d02114508f40585252dd01; no owned path conflicted.
  - PR 341 contains exactly the bounded Python identity backend, migration, tests, implementation documentation and required lightweight CI dependencies.
  - OIDC discovery, signed JWKS validation, issuer, audience, nonce, PKCE and one-time state are enforced server-side.
  - Portal sessions are opaque; storage contains keyed token hashes rather than browser tokens or IdP access, ID or refresh tokens.
  - Tenant and capability context is derived from a current portal-owned membership, with MFA, five-minute step-up, CSRF and synchronous membership/session revocation.
  - Focused local validation passed 12 identity lifecycle, OIDC and migration tests before PR creation.
  - Candidate head 034ee8436a45d85ddb6c7282d1314257aed4fbd0 passed AI Platform CI 1412 and GitHub Actions Security Analysis 1576; pre-commit and documentation passed in Freqtrade CI 1709 before that run was superseded by the develop merge.
derived:
  - The repository backend is independently reviewable without combining Next.js BFF work or real authentik/Cloudflare provisioning.
  - Full PI-06 remains active after this package because browser BFF integration, browser E2E and target-environment provisioning are separate evidence gates.
unknown:
  - Exact final CI outcome on the checkpoint-update head.
conflicts: []
first_failure:
  marker: AI_PLATFORM_LIGHTWEIGHT_DEPENDENCIES
  evidence: The first PR run could not collect the identity tests because the lightweight AI workflow omitted pyjwt and cryptography; after adding the existing project dependencies, the next full suite exposed a duplicate test module name, followed by deterministic Ruff/format findings. All three defects were repaired, and temporary diagnostic workflows were removed from the final diff.
rejected_hypotheses:
  - Replace product authorization with Cloudflare Access or IdP groups.
  - Store IdP tokens or raw portal session identifiers in the database.
  - Combine external Authentik deployment secrets with this repository backend package.
  - Retain a temporary diagnostic workflow in the merge candidate.
changed_paths:
  - .github/workflows/ai-platform.yml
  - ai_platform/portal/control_plane/database.py
  - ai_platform/portal/identity/__init__.py
  - ai_platform/portal/identity/crypto.py
  - ai_platform/portal/identity/http.py
  - ai_platform/portal/identity/migrations/0001_identity_lifecycle.sql
  - ai_platform/portal/identity/models.py
  - ai_platform/portal/identity/oidc.py
  - ai_platform/portal/identity/repository.py
  - ai_platform/portal/identity/runtime.py
  - ai_platform/portal/identity/schema.py
  - ai_platform/portal/identity/service.py
  - tests/ai_platform/portal/identity/test_identity_lifecycle.py
  - tests/ai_platform/portal/identity/test_identity_migration.py
  - tests/ai_platform/portal/identity/test_oidc.py
  - docs/ai_platform/portal/PI06_PRODUCT_IDENTITY_IMPLEMENTATION.md
  - docs/agents/tasks/FTAI-20260726-portal-pi06-product-identity-lifecycle.md
validation:
  - command: focused local pytest identity harness
    result: PASS
    evidence: 12 tests passed for OIDC, sessions, CSRF, MFA, revocation and migration behavior.
  - command: candidate AI Platform CI 1412
    result: PASS
    evidence: full AI tests, Ruff, Ruff format, codespell and JSON validation passed.
  - command: candidate GitHub Actions Security Analysis 1576
    result: PASS
    evidence: zizmor completed successfully and no temporary diagnostic workflow remained.
  - command: candidate Freqtrade CI 1709
    result: SUPERSEDED
    evidence: pre-commit and documentation passed; the run was superseded when current develop was merged before completion.
blockers: []
next_action: Require AI Platform, Freqtrade and security CI to pass on the exact updated PR head, then mark PR 341 ready and squash-merge without expanding into browser BFF or external deployment scope.
```
