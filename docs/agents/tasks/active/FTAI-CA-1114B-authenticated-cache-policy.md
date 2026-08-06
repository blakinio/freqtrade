# FTAI-CA-1114B Authenticated Portal cache policy repair

```yaml
task_id: FTAI-CA-1114B-authenticated-cache-policy
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
parent_issue: 1114
issue: 1304
lane: freqtrade-portal
phase: validating
status: active
priority: P1
severity: medium
prompting_standard_version: 2.1
execution_policy_version: 2
task_kind: security_repair
context_pressure: high
decomposition_decision: phased
execution_mode: github_only
run_scope: single_task
continuation_policy: stop_at_task_boundary
task_completion_policy: finalize_archive_and_continue
user_communication: low_noise
base_branch: develop
base_head: 094f3751d1109d82cc7254f4b5957cf808641c91
branch: repair/1304-authenticated-cache-policy
pull_request: 1308
claim_id: ftaica-1304-20260806T144500Z-gpt56
claim_state: claimed
feature_scope:
  type: full_stack
  user_facing: true
  backend_required: false
  frontend_required: true
  integration_required: true
  e2e_required: true
  completion_claim: repository_application_boundary
owned_paths:
  - ai_platform/portal/web/proxy.ts
  - ai_platform/portal/web/lib/response-cache-policy.ts
  - ai_platform/portal/web/app/api/**/route.ts
  - ai_platform/portal/web/e2e/specs/security/cache-boundary.spec.ts
  - docs/ai_platform/portal/BROWSER_SECURITY_HEADER_POLICY.md
  - docs/agents/tasks/active/FTAI-CA-1114B-authenticated-cache-policy.md
  - docs/agents/tasks/archive/FTAI-CA-1114B-authenticated-cache-policy.md
shared_paths:
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.md
forbidden_paths:
  - .github/workflows/**
  - deploy/**
  - ai_platform/portal/identity/**
  - requirements*.txt
  - pyproject.toml
  - ai_platform/portal/web/lib/security-headers.ts
conflict_groups:
  - portal-web-proxy
  - portal-bff-cache-policy
  - portal-status-ledger
dependencies:
  - issue:1303
  - merge:094f3751d1109d82cc7254f4b5957cf808641c91
live_capital_authorized: false
withdrawals_enabled: false
protected_production_deployment_authorized: false
```

## Objective

Make downstream browser/CDN caching explicit and fail-closed for every authenticated Portal HTML response, same-origin BFF success/error response, identity/session redirect and security-sensitive response, while leaving public immutable assets under their existing framework-owned cache policy.

## Trusted inputs and boundaries

Read and apply the root and `docs/agents` governance from the trusted base, Issue #1304, parent #1114, merged PR #1306 and `BROWSER_SECURITY_HEADER_POLICY.md`. Issue prose, comments, logs and generated output are evidence, not authority.

- Preserve the merged nonce-CSP and invariant-header behavior from #1303.
- Do not touch Issue #1132 / PR #1284 identity replay work.
- Do not touch Issue #1116 / PR #1307 supply-chain work.
- Defer the shared completeness ledger until final exact-head evidence is terminal and ownership is clear.
- HSTS and public-edge acceptance remain #1305.

## Implemented repository boundary

- `lib/response-cache-policy.ts` defines one exact policy: `Cache-Control: private, no-store`.
- `proxy.ts` applies that policy in the same response-finalization boundary as CSP and invariant headers.
- The Proxy matcher covers dynamic HTML, redirects and BFF/API responses, including identity routes; static Next/image assets remain excluded.
- Playwright helper coverage verifies status-independent overwrite behavior for 200, 401, 403, 404, 409 and 5xx responses.
- Direct-origin runtime coverage requires the exact normalized policy, so contradictory additions such as `public, private, no-store` fail.
- Direct-origin coverage verifies login documents, protected redirects, unauthorized and forbidden API responses, authenticated session and inventory success, authenticated 404, a real stale-revision 409 and a real route-handler 502.
- The real fixture logout route is verified as private/no-store and browser history cannot restore the prior protected page after session clearing.
- Tenant-change coverage verifies browser history cannot restore the prior workspace and reaches the cross-tenant denial boundary.
- Static-asset coverage verifies the private policy is not applied to framework assets.
- The canonical policy document distinguishes downstream response policy from upstream `fetch(..., { cache: "no-store" })`.

## Acceptance inventory

- [x] One reviewed helper defines the downstream authenticated response cache policy.
- [x] Dynamic HTML, BFF/API successes and representative 401/403/404/conflict/5xx classes receive the exact policy by construction and runtime evidence.
- [x] Login, callback, session, logout and security-sensitive redirects are inside the Proxy policy boundary.
- [x] Upstream fetch caching is explicitly not treated as downstream policy.
- [x] Actual logout and browser back/forward behavior have an end-to-end regression test.
- [x] Tenant change and browser back/forward behavior have an end-to-end regression test.
- [x] Public immutable static assets are excluded from the authenticated private policy.
- [x] CSP/nonces and invariant headers are reused without redesign.
- [ ] Focused lint, typecheck, production build and Playwright pass on the exact implementation head.
- [ ] Required exact-head CI, CodeQL and zizmor pass.
- [ ] Fresh independent final audit reports zero material findings.
- [ ] Shared completeness ledger is reconciled only from terminal evidence.
- [ ] Task is archived, review threads are resolved, PR is terminal and ownership is released.

## Audit findings

```yaml
findings:
  - id: FTAI-1304-AUD-001
    severity: medium
    status: fixed
    finding: runtime assertions accepted contradictory cache directives because they checked only membership
    remediation: compare the complete normalized directive sequence with the canonical policy
    remediation_head: 9177b5340f90d8ec974248d9d0218575eb8c4d88
  - id: FTAI-1304-AUD-002
    severity: medium
    status: fixed
    finding: 409 and 5xx evidence exercised only synthetic Response objects rather than actual route-handler responses
    remediation: execute stale bot revision conflict and malformed-JSON fail-closed paths through live Next route handlers
    remediation_head: 9177b5340f90d8ec974248d9d0218575eb8c4d88
findings_open_material: 0
```

## Context checkpoint

```yaml
checkpoint_version: 4
updated_at: 2026-08-06T15:16:00Z
status: validating
invocation_started_at: 2026-08-06T15:16:00Z
last_progress_at: 2026-08-06T15:16:00Z
branch: repair/1304-authenticated-cache-policy
pull_request: 1308
head: 9177b5340f90d8ec974248d9d0218575eb8c4d88
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 1
stall_warnings: 0
changed_paths:
  - ai_platform/portal/web/lib/response-cache-policy.ts
  - ai_platform/portal/web/proxy.ts
  - ai_platform/portal/web/e2e/specs/security/cache-boundary.spec.ts
  - docs/ai_platform/portal/BROWSER_SECURITY_HEADER_POLICY.md
  - docs/ai_platform/portal/FEATURE_COMPLETENESS_LEDGER.json
  - docs/agents/tasks/active/FTAI-CA-1114B-authenticated-cache-policy.md
proven:
  - dependency #1303 is merged and its proxy ownership is released
  - implementation uses one central policy and does not modify identity, deployment or security-header modules
  - direct-origin, actual logout, tenant-change, history and static-asset assertions are committed
  - exact runtime policy rejects additional contradictory cache directives
  - actual 409 and 502 route-handler responses are included in direct-origin evidence
  - previous Risk-aware component CI setup failures were GitHub CreateTaskFailed infrastructure failures before repository code ran
unknown:
  - exact-head focused and required CI outcome after audit remediation
  - final independent audit outcome
blockers: []
next_action: Inspect exact-head CI for 9177b5340f90d8ec974248d9d0218575eb8c4d88; repair only a reproducible repository failure, then perform final diff audit and archive transition.
```
