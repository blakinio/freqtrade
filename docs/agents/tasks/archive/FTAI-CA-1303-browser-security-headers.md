# FTAI-CA-1303 — Portal browser security headers

```yaml
task_id: FTAI-CA-1303-browser-security-headers
programme_id: FTAI-20260805-platform-continuous-assurance
parent_issue: 1114
issue: 1303
status: complete_on_merge
claim_id: ftaica-1303-20260806T133600Z-gpt56a
owner: repair-worker-1303-20260806T133600Z
base_branch: develop
base_head: 6e7147c866d3b7f91545c0aad54eac924ba7fa71
branch: repair/1303-browser-security-headers
pull_request: 1306
validated_implementation_head: 15e0dc5b1194a1dfca933c4a9b3374a173d1181b
audit_remediation_head: 756463628fe7c2be939a8c4cba08fe7f7b466701
completion_claim: repository_application_boundary
external_acceptance: not_claimed_issue_1305
ownership_release: on_merge
next_dependency: issue_1304
```

## Delivered outcome

- A fresh cryptographically random nonce is generated for every request handled by the Next.js Proxy.
- The same nonce-bound CSP is forwarded to Next.js rendering and returned on document, redirect and API/error responses.
- Production CSP contains no unbounded wildcard, `unsafe-eval`, private control-plane, Vault, Freqtrade or exchange browser origin.
- Framing, MIME sniffing, referrer leakage, selected browser capabilities and cross-origin document/resource behavior are explicitly constrained.
- Static Next.js resources receive invariant security headers without an unnecessary nonce policy.
- Development-only localhost/HMR exceptions are isolated to `NODE_ENV=development`.
- The ownership contract separates repository application enforcement (#1303), authenticated cache control (#1304), and protected public-edge/HSTS acceptance (#1305).
- The canonical JSON completeness ledger records the repository application boundary as implemented while preserving external acceptance as incomplete.

## Validation evidence

```yaml
focused_and_component:
  result: PASS
  evidence:
    - TypeScript typecheck
    - ESLint
    - Next.js production build
    - production session authorization integration
    - Chromium critical regression including security-headers.spec.ts
exact_head_before_archive:
  head: 15e0dc5b1194a1dfca933c4a9b3374a173d1181b
  checks:
    Freqtrade_CI_31108512692: PASS
    Risk_aware_component_CI_31108508824: PASS
    CodeQL_31108508793: PASS
    zizmor_31108508596: PASS
e2e:
  result: PASS
  journey: direct-origin browser security boundary
  assertions:
    - independent requests receive different nonces
    - rendered Next scripts use the response CSP nonce
    - protected redirects retain required headers
    - successful route-handler API responses retain middleware security headers
    - API errors retain required headers
    - static assets retain invariant headers
    - existing critical browser journeys remain green
audit:
  objective: falsify_acceptance
  findings:
    - id: FTAI-1303-AUD-001
      severity: medium
      evidence: the initial regression asserted an API error but not a successful route-handler response
      impact: middleware-to-route response header propagation was not directly proven
      disposition: fixed
      remediation_head: 756463628fe7c2be939a8c4cba08fe7f7b466701
      verification: authenticated /api/identity/session success now asserts CSP and every invariant header
  findings_open_material: 0
  final_exact_head_review: required_after_this_archive_update
  notes:
    - authenticated downstream cache behavior remains explicitly owned by issue 1304
    - HSTS and real public-edge/direct-origin acceptance remain explicitly owned by issue 1305
```

## Closeout contract

This archive update changes the PR head after the recorded remediation commit. PR #1306 may merge only after a fresh audit of the complete final diff, zero unresolved review threads, and all required checks pass on the exact final head. Merge closes #1303 and releases the claim. It must then unblock #1304 without changing the external-acceptance block on #1305.

## Safety boundary

No protected infrastructure was mutated. No HSTS/public-edge acceptance, credential access, identity lifecycle change, dependency change, deployment promotion, trading, withdrawal, or live-capital authority is claimed.
