# FTAI-CA-1114B Authenticated Portal cache policy repair

```yaml
task_id: FTAI-CA-1114B-authenticated-cache-policy
programme_id: FTAI-20260803-portal-remediation
repository: blakinio/freqtrade
parent_issue: 1114
issue: 1304
lane: freqtrade-portal
phase: validating
status: validating
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
user_communication: terminal_only
base_branch: develop
base_head: 61be1d0d106283aacdf4f5d4cfe4b241006d3cac
branch: repair/1304-authenticated-cache-policy
pull_request: 1308
claim_id: ftaica-1304-20260807T075247Z-gpt56sol
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
  - ai_platform/portal/web/next.config.ts
  - ai_platform/portal/web/proxy.ts
  - ai_platform/portal/web/lib/response-cache-policy.ts
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/components/bfcache-revalidation.tsx
  - ai_platform/portal/web/e2e/market-evidence-production-auth.test.mjs
  - ai_platform/portal/web/e2e/response-cache-production.test.mjs
  - ai_platform/portal/web/e2e/specs/security/cache-boundary.spec.ts
  - ai_platform/portal/web/package.json
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
  - portal-next-response-headers
  - portal-bff-cache-policy
  - portal-browser-history
  - portal-status-ledger
dependencies:
  - issue:1303
  - merge:094f3751d1109d82cc7254f4b5957cf808641c91
  - issue:1309
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
- HSTS and public-edge acceptance remain #1305 and require separate owner authorization.
- CI lifecycle repair #1309 is a separate workflow-owned task; this task does not modify `.github/workflows/**`.

## Implemented repository boundary

- `lib/response-cache-policy.ts` defines one exact policy: `Cache-Control: private, no-store`.
- Direct responses created by `proxy.ts` apply the policy together with CSP and invariant headers.
- Next.js response configuration is the final authority for responses that continue through page or route rendering, because route rendering can replace a header placed on `NextResponse.next()`.
- Dynamic HTML, redirects and BFF/API responses are covered; immutable framework assets retain Next.js-owned immutable caching.
- Direct-origin runtime coverage requires the exact normalized policy and exercises actual 200, redirect, 401, 403, 404, 409 and validation/failure responses.
- Logout, tenant-change and browser-history coverage proves protected content is not restored.
- Chromium BFCache restoration is explicitly revalidated through the real Proxy by the shell-level `BfcacheRevalidation` component; normal navigation is unaffected.

## Acceptance inventory

- [x] One reviewed helper defines the downstream authenticated response cache policy.
- [x] Next.js final rendered responses and direct Proxy responses both enforce the policy in the implemented boundary.
- [x] Representative success, 401, 403, 404, conflict and failure paths have actual route evidence in development/browser coverage.
- [x] Login, callback, session, logout and security-sensitive redirects are in scope.
- [x] Upstream fetch caching is not treated as downstream response policy.
- [x] Logout, tenant-change and BFCache/history regressions are covered.
- [x] Immutable framework assets are not assigned the private policy.
- [x] CSP/nonces and invariant headers are preserved.
- [ ] Focused lint, typecheck, production build, production cache probe and affected Chromium journeys pass on the current remediation head.
- [ ] Required exact-head CI, CodeQL, zizmor and affected Portal/WickHunter evidence pass.
- [ ] Fresh independent final audit reports zero material findings.
- [ ] Shared completeness ledger is reconciled only from terminal evidence.
- [ ] Task is archived, PR is terminal and ownership is released.

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
    finding: 409 and 5xx evidence exercised only synthetic Response objects
    remediation: execute real conflict and malformed-input fail-closed paths through live route handlers
    remediation_head: 9177b5340f90d8ec974248d9d0218575eb8c4d88
  - id: FTAI-1304-AUD-003
    severity: high
    status: fixed_pending_final_audit
    finding: Next.js route rendering replaced Cache-Control placed on NextResponse.next() with no-cache, must-revalidate
    evidence: universal Chromium run 31114335378, job 92662683883
    remediation: make Next.js final response configuration authoritative while retaining the helper for direct Proxy responses
  - id: FTAI-1304-AUD-004
    severity: medium
    status: remediation_implemented_pending_final_audit
    finding: durable task ownership and checkpoint did not match the expanded BFCache/history and production-evidence diff
    remediation: reconcile the task path inventory, claim, phase and checkpoint against the exact current PR scope without expanding the product objective
  - id: FTAI-1304-AUD-005
    severity: high
    status: fixed
    finding: production redirect probe was invalid because fixture bootstrap implicitly authenticated the request
    evidence: WickHunter Market Evidence CI run 31157993042, job 92801679330
    remediation: disable fixture identity bootstrap for the production cache probe so anonymous redirect and 401 cases exercise the real Proxy boundary
    remediation_head: bec8320de3f6b547dcbe261649b6c1e7ddad0630
  - id: FTAI-1304-AUD-006
    severity: high
    status: remediation_implemented_pending_validation
    finding: with fixture identity disabled, the protected 404 probe had no session and was intercepted as 401 by the Proxy before Next route dispatch
    evidence: WickHunter Market Evidence CI run 31158413555, job 92802982133, exact failure 401 != 404
    remediation: preserve anonymous redirect and 401 probes, but provide deterministic non-secret session-cookie presence only for the protected nonexistent API request so it traverses the real Proxy and reaches Next's 404
findings_open_material: 2
```

## Context checkpoint

```yaml
checkpoint_version: 6
updated_at: 2026-08-07T07:54:00Z
status: validating
branch: repair/1304-authenticated-cache-policy
pull_request: 1308
candidate_parent_head: bec8320de3f6b547dcbe261649b6c1e7ddad0630
claim_id: ftaica-1304-20260807T075247Z-gpt56sol
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 1
context_reconstruction_attempts: 1
stall_warnings: 0
changed_paths:
  - ai_platform/portal/web/next.config.ts
  - ai_platform/portal/web/proxy.ts
  - ai_platform/portal/web/lib/response-cache-policy.ts
  - ai_platform/portal/web/components/app-shell.tsx
  - ai_platform/portal/web/components/bfcache-revalidation.tsx
  - ai_platform/portal/web/e2e/market-evidence-production-auth.test.mjs
  - ai_platform/portal/web/e2e/response-cache-production.test.mjs
  - ai_platform/portal/web/e2e/specs/security/cache-boundary.spec.ts
  - ai_platform/portal/web/package.json
  - docs/agents/tasks/active/FTAI-CA-1114B-authenticated-cache-policy.md
  - docs/ai_platform/portal/BROWSER_SECURITY_HEADER_POLICY.md
proven:
  - Proxy-only Cache-Control is insufficient for final rendered responses
  - Next response configuration preserves the canonical private/no-store boundary for dynamic responses while framework assets retain immutable caching
  - BFCache restoration requires explicit browser-history revalidation for the protected Portal shell
  - the production 404 test must enter the Proxy with session presence to reach a nonexistent protected route
  - exact head bec8320de3f6b547dcbe261649b6c1e7ddad0630 failed exactly 401 != 404 as predicted by AUD-006
unknown:
  - whether the current remediation commit passes the exact production cache probe and all affected Chromium journeys
  - final exact-head audit and required CI result after task/ledger/archive closeout
blockers: []
next_action: validate the current remediation head with the production cache probe and affected Chromium journeys; if green, run a fresh independent final-diff audit, reconcile the completeness ledger, archive the task, and run final exact-head required CI before squash merge.
```
