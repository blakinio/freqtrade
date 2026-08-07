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
execution_mode: github_only
run_scope: single_task
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
  - ai_platform/portal/web/e2e/liquid20-production-auth.test.mjs
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

Make downstream browser/CDN caching explicit and fail-closed for dynamic Portal documents, protected redirects and same-origin BFF/API responses while preserving framework-owned immutable asset caching. Browser history restores must revalidate the server-owned session/tenant boundary before protected content is trusted.

## Implemented boundary

- `lib/response-cache-policy.ts` owns the canonical application value `Cache-Control: private, no-store`.
- `proxy.ts` applies it to direct Proxy responses together with CSP and invariant browser headers.
- `next.config.ts` applies the same value to final dynamic responses because Next rendering can replace headers placed only on `NextResponse.next()`.
- Application-controlled responses require the exact normalized value.
- Framework-generated terminal responses may append only stricter non-cacheable directives; they must retain `private` and `no-store` and must not add `public`, `immutable`, `s-maxage` or positive `max-age`.
- Immutable Next static/image assets remain under framework-owned public immutable caching.
- All back/forward restores are forced through exactly one network reload so the Proxy re-checks current session and tenant state; reload navigation does not recurse.
- Production auth suites for Market Evidence and Liquid20 assert the canonical downstream policy.
- The production cache probe runs with fixture identity disabled. Anonymous redirect/401 requests remain anonymous, protected 404 receives only deterministic non-secret session-cookie presence, and a real BFF 502 is produced in API mode by an intentionally unreachable localhost control-plane URL.

## Acceptance inventory

- [x] One reviewed helper defines the application-owned downstream cache policy.
- [x] Proxy and final Next response configuration enforce the dynamic response boundary.
- [x] Representative 200, redirect, 401, 403, 404, 409 and validation paths have live route evidence.
- [x] Logout, tenant change and browser back/forward restore regressions are covered.
- [x] Static Next assets are excluded from private caching.
- [x] CSP/nonces and invariant headers remain preserved.
- [ ] Real production BFF 5xx response is proven `private, no-store` on the current candidate.
- [ ] Focused production build/cache probe and affected Chromium journeys pass on the current candidate.
- [ ] Fresh independent final-head audit reports zero material findings.
- [ ] Dependency #1309 / PR #1310 is merged and current `develop` is reconciled before final CI.
- [ ] Completeness ledger is reconciled without claiming #1305 protected acceptance.
- [ ] Active task is archived and final exact-head required CI passes.
- [ ] PR is squash-merged and ownership released.

## Audit findings

```yaml
findings:
  - id: FTAI-1304-AUD-001
    severity: medium
    status: fixed
    finding: cache assertions originally accepted contradictory shared-cache directives
  - id: FTAI-1304-AUD-002
    severity: medium
    status: remediation_implemented_pending_runtime_5xx_evidence
    finding: failure evidence originally relied on synthetic Response coverage instead of an actual BFF 5xx
  - id: FTAI-1304-AUD-003
    severity: high
    status: fixed_pending_final_audit
    finding: Next rendering replaced Cache-Control placed only on NextResponse.next()
    evidence: universal Chromium run 31114335378 job 92662683883
  - id: FTAI-1304-AUD-004
    severity: medium
    status: remediation_implemented_pending_final_audit
    finding: durable ownership/checkpoint drifted from the expanded browser-history and production-evidence diff
  - id: FTAI-1304-AUD-005
    severity: high
    status: fixed
    finding: fixture bootstrap invalidated the anonymous production redirect probe
    evidence: WickHunter run 31157993042 job 92801679330
  - id: FTAI-1304-AUD-006
    severity: high
    status: fixed_pending_final_audit
    finding: protected production 404 was intercepted as 401 without session presence
    evidence:
      - WickHunter run 31158413555 job 92802982133: 401 != 404
      - WickHunter run 31159729527 job 92807095945: required 404 reached after remediation
  - id: FTAI-1304-AUD-007
    severity: medium
    status: remediation_implemented_pending_validation
    finding: framework production 404 appends safe no-cache/max-age=0/must-revalidate directives, so exact equality is not a truthful framework-response contract
    evidence: WickHunter run 31159729527 job 92807095945
  - id: FTAI-1304-AUD-008
    severity: medium
    status: remediation_implemented_pending_validation
    finding: acceptance lacked an actual 5xx route even though Issue #1304 explicitly requires 5xx cache evidence
    remediation: run the production server in API mode with PORTAL_CONTROL_PLANE_URL=http://127.0.0.1:1 and require authenticated GET /api/bots to return real BFF 502 with exact private/no-store
findings_open_material: 5
```

## Context checkpoint

```yaml
checkpoint_version: 9
updated_at: 2026-08-07T08:23:00Z
status: validating
branch: repair/1304-authenticated-cache-policy
pull_request: 1308
candidate_head: 8695a8c4914f5397ec10faac7fd169ef366990dc
claim_id: ftaica-1304-20260807T075247Z-gpt56sol
ci_checks_for_current_head: 0
unchanged_state_checks: 0
identical_failure_retries: 0
repair_cycles_for_current_gate: 3
context_reconstruction_attempts: 1
stall_warnings: 0
proven:
  - final response configuration is required in addition to Proxy mutation
  - protected framework 404 retains private/no-store while Next may append stricter non-cacheable directives
  - deterministic session presence is sufficient to traverse the Proxy and reach a protected nonexistent route
  - all browser-history restore modes require server revalidation
unknown:
  - whether the API-mode production probe passes exact 200/redirect/401/404/502 and immutable-asset assertions
  - whether affected Chromium history/cache journeys pass on the resulting candidate
  - final-head audit and exact-head CI after #1310 merge-forward and archive closeout
blockers:
  - issue:1309 must reach terminal merged state before #1304 final merge
next_action: validate the API-mode production cache probe and affected Chromium journeys; if green, wait only for #1310 merge, merge-forward current develop, run final audit, reconcile ledger/archive, then require exact-head CI and squash-merge #1308.
```
