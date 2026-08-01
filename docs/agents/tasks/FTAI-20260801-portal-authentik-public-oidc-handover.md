---
task_id: FTAI-20260801-portal-authentik-public-oidc-handover
status: in_progress
branch: feat/portal-authentik-public-oidc-20260801
base_branch: develop
created: 2026-08-01
updated: 2026-08-01
parent_task: FTAI-20260731-portal-local-authentik-oidc-integration
related_pr: 903
supersedes_pr: 876
owned_paths:
  - .github/workflows/portal-oidc-public-deploy.yml
  - ai_platform/portal/identity/bootstrap_membership.py
  - ai_platform/portal/identity/local_test_runtime.py
  - ai_platform/portal/identity/oidc.py
  - ai_platform/portal/identity/public_runtime.py
  - ai_platform/portal/identity/runtime.py
  - ai_platform/portal/web/lib/identity.ts
  - deploy/synology/portal/Dockerfile
  - deploy/synology/portal-oidc/
  - tests/ai_platform/portal/identity/test_oidc.py
  - tests/ai_platform/portal/deployment/test_portal_oidc_public_deploy.py
  - docs/agents/tasks/FTAI-20260801-portal-authentik-public-oidc-handover.md
required_reads:
  - docs/ai_platform/portal/ARCHITECTURE_DECISIONS.md
  - docs/agents/tasks/FTAI-20260731-portal-local-authentik-oidc-integration.md from PR 876
---

# Portal Authentik public OIDC handover

## Goal

Complete real Portal authentication through the existing Synology Authentik deployment using public Cloudflare Tunnel HTTPS origins, Portal-owned sessions and OIDC Authorization Code plus PKCE.

Required browser flow:

```text
https://quant.molehill.cloud
  -> https://auth.molehill.cloud
  -> password plus Authentik TOTP/MFA
  -> https://quant.molehill.cloud/api/identity/callback
  -> authenticated Portal session
```

## Frozen public contract

```text
Portal origin: https://quant.molehill.cloud
Authentik origin: https://auth.molehill.cloud
Portal callback: https://quant.molehill.cloud/api/identity/callback
Scopes: openid profile email
External principal identity: exact OIDC iss + sub
```

The retired `auth.quant.molehill.cloud` hostname is forbidden.

## Infrastructure evidence inherited by this task

- Authentik 2026.5.5 server, worker and PostgreSQL were deployed on Synology.
- Runtime secrets are target-owned in a persistent mode-`0600` environment file.
- PostgreSQL has no host-published port.
- Authentik readiness repair PR 862 merged as `6ac747a069455ddfbfa00d861008dd81fbf509cf`.
- Request-only rerun PR 865 was consumed and closed without merge.
- Deployment run `30625762233` produced artifact `portal-authentik-local-test-deploy-865` with healthy Authentik services, no privileged/host-network containers, no Docker socket and `live_capital_authorized=false`.
- The artifact did not prove that an OIDC provider/application had been created.
- The owner completed `akadmin` password and TOTP setup and verified the Authentik flow over `https://auth.molehill.cloud`.
- Cloudflare routes are recorded as:

```text
https://quant.molehill.cloud -> http://192.168.1.2:3031
https://auth.molehill.cloud  -> http://192.168.1.2:9000
```

## Repository preflight

Frozen before mutation:

```text
develop: 55b63820f50976e3fcf605f1cea0810183d2b842
PR 876 head: 23bf942330af0f6ce3c09c4526905058a8161449
PR 876 merge base: 1060dec433a7e9d72e53ccddb6d76fe93842b187
PR 876 divergence: 18 ahead, 34 behind develop
review threads: 0
```

The 13 implementation paths from PR 876 did not overlap any path changed between its merge base and current `develop`.

Exact PR 876 failures were mechanical:

- AI Platform CI run `30648432349`: 1035 tests passed and 71 skipped before Ruff `I001` stopped the job.
- Freqtrade CI run `30648432361`: import ordering, Ruff modernization/security/path rules and Ruff formatting in the LAN deployer.
- Portal Web CI `30648432355`, Portal Universal E2E `30648432447` and security `30648432363` passed.

## Replacement branch decision

A replacement branch was created from PR 876 head and refreshed through normal merge PR 901 from exact `develop` head `55b63820f50976e3fcf605f1cea0810183d2b842`.

PR 901 merged into the replacement branch as:

```text
a5c02b8c492023f0e42695ae73611c12f08de5e8
```

The resulting feature diff is based on current `develop` and does not revert newer Portal work.

## Implemented public HTTPS changes

PR 903 adds:

- public Authentik application slug `freqtrade-portal` and provider `Freqtrade Portal Public OIDC`;
- confidential client with strict callback `https://quant.molehill.cloud/api/identity/callback`;
- scopes `openid`, `profile` and `email`;
- no client secret in the repository blueprint;
- public identity runtime requiring `PORTAL_ENVIRONMENT=production|staging` and transport `https`;
- Secure, SameSite=Lax, Path=/ `__Host-portal_session` and `__Host-portal_csrf` cookies;
- no automatic first membership or email/domain/group promotion;
- explicit one-time exact-principal bootstrap command keyed by exact deployed issuer plus subject;
- an immutable audit event `identity.membership_bootstrapped`;
- subject hashing rather than subject disclosure in bootstrap output;
- target secret preservation and rotation refusal;
- discovery and JWKS probes from inside the Portal identity container;
- a public Portal redirect probe through `https://quant.molehill.cloud`;
- an internal-only Python control plane and one LAN-published Next.js BFF;
- no Docker socket, privileged mode or host networking;
- a request-only trusted-runner workflow that accepts exactly one frozen request file;
- a secret-free always-uploaded report;
- fixture identity disabled in the public runtime;
- explicit `live_capital_authorized=false`.

The old LAN-only workflow and blueprint were removed from the replacement diff.

## Provider slug evidence rule

The repository contract declares application slug `freqtrade-portal`. Deployment must not merely trust the filename or constant. The target deployer:

1. applies the blueprint;
2. queries the deployed provider and associated application from Authentik;
3. reads the actual deployed application slug;
4. derives `https://auth.molehill.cloud/application/o/<deployed-slug>/`;
5. requires that value to equal the frozen issuer;
6. fetches discovery and JWKS from inside the identity container;
7. fails closed on any mismatch.

The deployed provider and public discovery document are not yet proven because the implementation PR has not merged and no deployment request has run.

## Safety boundary

This task does not authorize live capital, production trading, real exchange orders, withdrawals, exchange credentials in GitHub, destructive restore, database host publication, Docker socket access, privileged containers, host networking or an unauthenticated public Portal terminal state.

Any Freqtrade runtime remains dry-run and receives no order authority.

## Remaining gates

1. Repair every exact-head CI failure on PR 903.
2. Require all applicable workflows green and zero unresolved review threads.
3. Merge PR 903 with `expected_head_sha`.
4. Close superseded PR 876 without merge only after equivalent functionality is green and merged.
5. Create one separate request-only PR containing exactly:

```text
deploy/synology/portal-oidc/run-requests/public-oidc-20260801-v1.json
```

6. Run deployment only through environment `synology-staging` and runner `freqtrade-staging`.
7. Capture the secret-free deployment artifact and close the request PR without merge.
8. Owner completes password plus TOTP login.
9. Confirm missing membership fails closed.
10. Obtain the exact target principal subject without recording it in GitHub.
11. Run the explicit exact-principal bootstrap on the target.
12. Confirm authenticated Portal access and logout invalidation.

## Context checkpoint

```yaml
checkpoint_version: 2
updated_at: 2026-08-01T08:46:00+02:00
base_head: 55b63820f50976e3fcf605f1cea0810183d2b842
implementation_head: 9eb3bfb738baae25885a8a289c47ee01de9f71f5
branch: feat/portal-authentik-public-oidc-20260801
pr: "#903"
status: in_progress
proven:
  - PR 876 failures were mechanical static-validation failures after its functional tests passed.
  - Replacement branch is synchronized with current develop through merged PR 901.
  - Public runtime contains no automatic membership grant.
  - Public blueprint contains no client secret and uses the exact public callback.
  - Deployment contract refuses bootstrap, restore and live-capital authorization.
  - Control-plane publication, Docker socket, privileged mode and host networking are prohibited.
derived:
  - The actual issuer can be trusted only after target-side provider/application query plus discovery equality.
unknown:
  - Exact-head PR 903 CI result.
  - Target-side public Authentik discovery and JWKS result.
  - Exact first principal subject.
  - Password/TOTP browser acceptance and logout result.
conflicts: []
first_failure:
  marker: PR_903_EXACT_HEAD_CI_PENDING
  evidence: Required workflows were queued for implementation head 9eb3bfb738baae25885a8a289c47ee01de9f71f5.
validation:
  - Security run 30688360952 queued.
  - Portal Web run 30688360950 queued.
  - Freqtrade CI run 30688360963 queued.
  - AI Program Closure E2E run 30688360970 queued.
  - AI Platform CI run 30688360934 queued.
  - Portal Universal E2E run 30688360936 queued.
blockers:
  - Exact-head CI must pass before merge.
  - Trusted-runner deployment requires merged implementation and a separate frozen request PR.
  - Password/TOTP and exact-principal bootstrap require owner interaction on the target.
next_action: Inspect the first completed failing workflow on PR 903, repair it on the same branch, and repeat until the exact head is green.
```

Terminal evidence must include these exact lines:

```text
secret_values_recorded=false
live_capital_authorized=false
```
