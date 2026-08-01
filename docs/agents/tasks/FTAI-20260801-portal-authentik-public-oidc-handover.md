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
  - .github/workflows/portal-synology-lan-preview.yml
  - ai_platform/portal/identity/bootstrap_membership.py
  - ai_platform/portal/identity/oidc.py
  - ai_platform/portal/identity/public_runtime.py
  - ai_platform/portal/identity/runtime.py
  - ai_platform/portal/web/lib/identity.ts
  - deploy/synology/portal/Dockerfile
  - deploy/synology/portal/deploy-preview.sh
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

## Inherited target evidence

- Authentik 2026.5.5 server, worker and PostgreSQL were deployed on Synology.
- Runtime secrets are target-owned in a persistent mode-`0600` environment file.
- PostgreSQL has no host-published port.
- Authentik readiness repair PR 862 merged as `6ac747a069455ddfbfa00d861008dd81fbf509cf`.
- Request-only rerun PR 865 was consumed and closed without merge.
- Deployment run `30625762233` produced artifact `portal-authentik-local-test-deploy-865` with healthy Authentik services, no privileged or host-network containers, no Docker socket and `live_capital_authorized=false`.
- That artifact did not prove that an OIDC provider or application existed.
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

The 13 implementation paths from PR 876 did not overlap any path changed between its merge base and the frozen `develop` head.

Exact PR 876 failures were mechanical:

- AI Platform CI run `30648432349`: 1035 tests passed and 71 skipped before Ruff `I001` stopped the job.
- Freqtrade CI run `30648432361`: import ordering, Ruff modernization, security/path rules and formatting in the LAN deployer.
- Portal Web CI `30648432355`, Portal Universal E2E `30648432447` and security `30648432363` passed.

## Replacement branch

The replacement branch was created from PR 876 and refreshed through merge PR 901 from exact `develop` head `55b63820f50976e3fcf605f1cea0810183d2b842`.

PR 901 merged into the feature branch as:

```text
a5c02b8c492023f0e42695ae73611c12f08de5e8
```

The feature branch is based on current frozen `develop` and does not revert newer Portal work.

## Implemented public HTTPS changes

PR 903 adds:

- public Authentik application slug `freqtrade-portal` and provider `Freqtrade Portal Public OIDC`;
- confidential client with strict callback `https://quant.molehill.cloud/api/identity/callback`;
- scopes `openid`, `profile` and `email`;
- no client secret in the repository blueprint;
- public identity runtime requiring `PORTAL_ENVIRONMENT=production|staging` and transport `https`;
- Secure, SameSite=Lax, Path=/ `__Host-portal_session` and `__Host-portal_csrf` cookies;
- no automatic first membership or email, domain or group promotion;
- explicit one-time exact-principal bootstrap keyed by exact deployed issuer plus subject;
- immutable audit action `identity.membership_bootstrapped`;
- subject hashing instead of subject disclosure in bootstrap output;
- target secret preservation and refusal of implicit client-secret rotation;
- discovery and JWKS probes from inside the Portal identity container;
- public Portal redirect probe through `https://quant.molehill.cloud`;
- internal-only Python control plane and one LAN-published Next.js BFF;
- no Docker socket, privileged mode or host networking;
- request-only trusted-runner workflow accepting exactly one frozen request file;
- secret-free report uploaded even on failure;
- fixture identity disabled in the public runtime;
- explicit `live_capital_authorized=false`.

Retired from the replacement diff:

- LAN-only Authentik blueprint and deployment workflow;
- LAN identity runtime containing automatic local-owner membership;
- automatic Synology preview workflow and script that could overwrite port `3031` with fixture identity after unrelated web changes.

## Provider slug evidence rule

The repository contract declares application slug `freqtrade-portal`. Deployment must not trust only the blueprint filename or a local constant. The target deployer:

1. applies the blueprint;
2. queries the deployed provider and associated application from Authentik;
3. reads the actual deployed application slug;
4. derives `https://auth.molehill.cloud/application/o/<deployed-slug>/`;
5. requires equality with the frozen issuer;
6. fetches discovery and JWKS from inside the identity container;
7. fails closed on any mismatch.

The deployed provider and discovery document remain unproven until the implementation merges and a separate request-only deployment PR runs.

## CI repair evidence

PR 903 exact-head iterations established:

- AI Platform tests passed twice with `1036 passed, 71 skipped`; initial failures were import ordering and then two deterministic formatter differences.
- Freqtrade pre-commit passed mypy and identified only deployer import layout, two unused `noqa` directives and Ruff formatting.
- The exact repository Ruff hooks were applied to the deployer by one isolated branch-only formatter run.
- The temporary formatter workflow was removed immediately after its output commit.
- Security analysis passed on the preceding exact head.
- No PR comments or unresolved review threads existed at the checkpoint.

Code formatter output commit:

```text
742e9b892f9b10ebfd1739135eb92b56985b9d6c
```

Temporary formatter removal commit:

```text
246e81a46528fc04b0a3c33dda638abbb5ddaf49
```

All required workflows must still pass on the final documentation checkpoint head before merge.

## Safety boundary

This task does not authorize live capital, production trading, real exchange orders, withdrawals, exchange credentials in GitHub, destructive restore, database host publication, Docker socket access, privileged containers, host networking or an unauthenticated public Portal terminal state.

Any Freqtrade runtime remains dry-run and receives no order authority.

## Remaining gates

1. Require all applicable workflows green on the exact final PR 903 head.
2. Require zero unresolved review threads and a mergeable, up-to-date PR.
3. Merge PR 903 with `expected_head_sha`.
4. Close superseded PR 876 without merge after PR 903 merges.
5. Create one separate request-only PR containing exactly:

```text
deploy/synology/portal-oidc/run-requests/public-oidc-20260801-v1.json
```

6. Run deployment only through environment `synology-staging` and runner `freqtrade-staging`.
7. Validate and retain the secret-free deployment artifact, then close the request PR without merge.
8. Owner completes password plus TOTP login.
9. Confirm missing membership fails closed.
10. Obtain the exact target principal subject without recording it in GitHub.
11. Run explicit exact-principal bootstrap on the target.
12. Confirm authenticated Portal access and logout invalidation.

## Context checkpoint

```yaml
checkpoint_version: 3
updated_at: 2026-08-01T09:01:00+02:00
base_head: 55b63820f50976e3fcf605f1cea0810183d2b842
code_head: 742e9b892f9b10ebfd1739135eb92b56985b9d6c
checkpoint_parent: 246e81a46528fc04b0a3c33dda638abbb5ddaf49
branch: feat/portal-authentik-public-oidc-20260801
pr: "#903"
status: in_progress
proven:
  - PR 876 failures were mechanical static-validation failures after functional tests passed.
  - Replacement branch is synchronized with frozen develop through merged PR 901.
  - Public runtime contains no automatic membership grant.
  - Public blueprint contains no client secret and uses the exact public callback.
  - Deployment contract refuses bootstrap, restore and live-capital authorization.
  - Control-plane publication, Docker socket, privileged mode and host networking are prohibited.
  - Competing fixture deployment on port 3031 is retired.
  - Deployer has repository-generated Ruff fixes and formatting.
derived:
  - The actual issuer is trusted only after target provider/application query and discovery equality.
unknown:
  - Final exact-head PR 903 CI result.
  - Target public Authentik discovery and JWKS result.
  - Exact first principal subject.
  - Password/TOTP browser acceptance and logout result.
conflicts: []
first_failure:
  marker: PR_903_FINAL_EXACT_HEAD_CI_PENDING
  evidence: Final documentation checkpoint creates a new exact head requiring complete CI.
blockers:
  - Exact-head CI must pass before merge.
  - Trusted-runner deployment requires merged implementation and a separate frozen request PR.
  - Password/TOTP and exact-principal bootstrap require owner interaction on the target.
next_action: Validate every workflow on the exact PR head, repair any concrete failure, then merge with expected_head_sha.
```

Terminal evidence must include these exact lines:

```text
secret_values_recorded=false
live_capital_authorized=false
```
