# FTAI-20260803 Portal Remediation — Issue 1124

```yaml
task_id: FTAI-20260803-portal-remediation-1124
programme_id: FTAI-20260803-portal-remediation
issue: 1124
repository: blakinio/freqtrade
lane: freqtrade-portal
task_kind: implementation
phase: reproduce
status: implementing
priority: high
prompting_standard_version: 2.1
execution_policy_version: 2
context_pressure: medium
decomposition_decision: single
execution_mode: github_only
run_scope: autonomous_task
continuation_policy: continue_until_real_stop
task_completion_policy: finalize_archive_and_continue
user_communication: terminal_only
feature_scope:
  type: full_stack
  user_facing: true
  backend_required: false
  frontend_required: false
  integration_required: true
  e2e_required: true
branch: fix/portal-1124-liquid20-session-authorization
base_branch: develop
base_head: 0a82a5c93613a213989865bd9128ac7263227148
pr: none
owned_paths:
  - ai_platform/portal/web/lib/local-read-authorization.ts
  - ai_platform/portal/web/lib/market-evidence/authorization.ts
  - ai_platform/portal/web/app/api/market/liquidations/route.ts
  - ai_platform/portal/web/app/api/market/liquidations/summary/route.ts
  - ai_platform/portal/web/app/api/market/liquidations/health/route.ts
  - ai_platform/portal/web/app/api/market/liquidations/_shared.ts
  - ai_platform/portal/web/e2e/liquid20-production-auth.test.mjs
  - ai_platform/portal/web/package.json
  - .github/workflows/portal-web.yml
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1124.md
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
shared_path_leases: []
producer_dependencies:
  - existing PI-06 current-session endpoint and identity contracts
consumer_constraints:
  - do not create the #1110 shared BFF transport authority
  - do not create the #1109 canonical error-envelope authority
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Finding reproduced

On the exact base, the generic proxy/`requireBrowserSession()` checks only that a real-mode session cookie is present. The three Liquid20 handlers call the local mounted read model directly and never validate the token through `/v1/identity/session`. An arbitrary non-empty cookie can therefore pass the proxy and reach the route family without current revocation, expiry, membership, tenant or role enforcement.

The existing Market Evidence boundary provides a bounded reference implementation but is module-specific. This task may extract one narrow server-only local-read authorization helper and keep module policy wrappers, without claiming the future whole-Portal transport/error-contract producers.

## Acceptance inventory

- [ ] Missing, malformed, arbitrary, unknown, expired and revoked sessions return safe `401` for list, summary and health.
- [ ] Disabled/version-stale membership follows the identity endpoint denial and returns safe `401`/`403` without data.
- [ ] Cross-tenant session and unauthorized role return safe `403` without revealing dataset state.
- [ ] Identity timeout, connection failure, malformed body, invalid contract or unexpected status returns fail-closed `503`.
- [ ] A valid authorized current session reaches all three Liquid20 endpoints.
- [ ] Only the allowlisted Portal session cookie is forwarded to the identity backend.
- [ ] Authorization uses a finite timeout, manual redirect policy and `no-store` responses.
- [ ] Fixture identity remains available only under the existing exact test triple gate and cannot bypass production mode.
- [ ] Market Evidence continues to use the same centralized local-read authorization engine with its existing policy.
- [ ] A deterministic route inventory test covers the local Liquid20 reader family and detects a missing authorization call.
- [ ] Typecheck, lint, production-auth integration test, Portal Web workflow, repository CI and security analysis pass on the exact final head.
- [ ] Fresh exact-head audit reports no material issue in the changed paths.
- [ ] PR merges, Issue #1124 closes, task archives and ownership releases.

## Safety

- Never log or persist cookies, tokens, identity responses or tenant-private Liquid20 data.
- Cloudflare Access and cookie presence remain defense in depth only.
- No browser access to the control plane/private runtime is added.
- No trading, runtime mutation, protected deployment or live-capital effect is authorized.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-03T10:31:00Z
head: 0a82a5c93613a213989865bd9128ac7263227148
branch: fix/portal-1124-liquid20-session-authorization
pr: none
status: implementing
context_routes:
  - issue #1124
  - ai_platform/portal/web/lib/identity.ts
  - ai_platform/portal/web/lib/market-evidence/authorization.ts
  - ai_platform/portal/web/app/api/market/liquidations/_shared.ts
  - ai_platform/portal/web/app/api/market/liquidations/route.ts
  - ai_platform/portal/web/app/api/market/liquidations/summary/route.ts
  - ai_platform/portal/web/app/api/market/liquidations/health/route.ts
owned_paths:
  - ai_platform/portal/web/lib/local-read-authorization.ts
  - ai_platform/portal/web/lib/market-evidence/authorization.ts
  - ai_platform/portal/web/app/api/market/liquidations/**
  - ai_platform/portal/web/e2e/liquid20-production-auth.test.mjs
  - ai_platform/portal/web/package.json
  - .github/workflows/portal-web.yml
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1124.md
  - docs/agents/programs/FTAI_PORTAL_REMEDIATION_PROGRAM.md
proven:
  - arbitrary non-empty cookie presence is accepted by requireBrowserSession in real mode
  - Liquid20 list, summary and health handlers do not call current-session authorization
  - Liquid20 reads a local mounted read model and has no downstream FastAPI authorization
  - Market Evidence has a bounded current-session authorization reference
  - no nearer AGENTS.md exists under ai_platform or ai_platform/portal/web
  - no overlapping branch or remediation PR for issue 1124 was found
derived:
  - one extracted local-read authorization engine can remove duplicate security logic while preserving module-specific tenant/role policy
unknown:
  - no explicit dedicated Liquid20 capability exists in the current session contract; the existing local market-evidence role policy is the closest proven repository policy and must be documented in the implementation
conflicts: []
first_failure:
  marker: liquid20-arbitrary-cookie-bypass
  evidence: route family calls liquidationReadModel directly after presence-only proxy
rejected_hypotheses:
  - proxy cookie presence is current authorization; rejected
  - Cloudflare Access replaces application session validation; rejected by PI-06 architecture
  - local-file market data needs no tenant/role boundary; rejected by Issue #1124 and protected Portal architecture
changed_paths:
  - docs/agents/tasks/active/FTAI-20260803-portal-remediation-1124.md
validation:
  - command: static exact-base reproduction
    result: FAIL_EXPECTED
    evidence: no identity backend call in all three Liquid20 handlers
blockers:
  - none
next_action: Implement a server-only centralized local-read authorization helper, route-specific Liquid20 policy wrapper and exact production-mode security integration test.
```
