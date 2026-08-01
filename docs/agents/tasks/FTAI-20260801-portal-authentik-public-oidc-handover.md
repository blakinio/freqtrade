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

## Goal and frozen contract

```text
https://quant.molehill.cloud
  -> https://auth.molehill.cloud
  -> password plus Authentik TOTP/MFA
  -> https://quant.molehill.cloud/api/identity/callback
  -> Portal-owned authenticated session
```

```text
Portal origin: https://quant.molehill.cloud
Authentik origin: https://auth.molehill.cloud
Callback: https://quant.molehill.cloud/api/identity/callback
Flow: OIDC Authorization Code plus PKCE
Scopes: openid profile email
Principal identity: exact iss plus sub
```

The retired `auth.quant.molehill.cloud` hostname is forbidden.

## Inherited target evidence

- Authentik 2026.5.5 server, worker and PostgreSQL are deployed on Synology.
- Target runtime secrets are stored outside GitHub in a persistent mode-`0600` file.
- PostgreSQL has no host-published port.
- Readiness repair PR 862 merged as `6ac747a069455ddfbfa00d861008dd81fbf509cf`.
- Request-only PR 865 was consumed and closed without merge.
- Run `30625762233` produced artifact `portal-authentik-local-test-deploy-865` proving healthy services, no privileged or host-network containers, no Docker socket and `live_capital_authorized=false`.
- That artifact did not prove an OIDC provider or application.
- The owner completed `akadmin` password and TOTP setup over `https://auth.molehill.cloud`.
- Recorded Cloudflare routes:

```text
https://quant.molehill.cloud -> http://192.168.1.2:3031
https://auth.molehill.cloud  -> http://192.168.1.2:9000
```

## Replacement branch history

Initial frozen state:

```text
develop: 55b63820f50976e3fcf605f1cea0810183d2b842
PR 876 head: 23bf942330af0f6ce3c09c4526905058a8161449
PR 876 merge base: 1060dec433a7e9d72e53ccddb6d76fe93842b187
PR 876 divergence: 18 ahead, 34 behind
PR 876 review threads: 0
```

PR 876 functional tests passed; its failures were mechanical Ruff, pre-commit and formatting failures. The replacement branch was refreshed from frozen `develop` through PR 901, merged as:

```text
a5c02b8c492023f0e42695ae73611c12f08de5e8
```

While PR 903 was being repaired, `develop` advanced by 12 commits to:

```text
3afe281de86673902ded7625d6dade94105b5ee9
```

Those commits changed only WickHunter production materialization paths and did not overlap the Portal OIDC diff. Refresh PR 905 merged exact `develop` into the feature branch as:

```text
2ab38527de472a37ded855c93d6a26872f77df73
```

## Implemented public HTTPS changes

PR 903 contains:

- public Authentik application slug `freqtrade-portal`;
- confidential provider `Freqtrade Portal Public OIDC`;
- strict public callback and scopes `openid`, `profile`, `email`;
- no client secret in repository content;
- HTTPS-only production or staging identity runtime;
- Secure, SameSite=Lax, Path=/ `__Host-portal_session` and `__Host-portal_csrf` cookies;
- no automatic first membership or email, domain or group promotion;
- explicit exact-issuer-and-subject bootstrap with audit action `identity.membership_bootstrapped`;
- subject hashing in bootstrap output;
- target client-secret preservation and refusal of implicit rotation;
- deployed provider/application query and issuer derivation;
- discovery and JWKS validation from inside the identity container;
- public redirect probe through `https://quant.molehill.cloud`;
- internal-only Python control plane and one LAN-published Next.js BFF;
- no Docker socket, privileged mode, host networking or control-plane host port;
- frozen exact-one-file deployment workflow on `freqtrade-staging` and environment `synology-staging`;
- secret-free report uploaded even after failure;
- identity fixture disabled and `live_capital_authorized=false`.

Retired:

- LAN-only OIDC workflow, blueprint and automatic-membership runtime;
- automatic Synology preview workflow and script that could overwrite port `3031` with fixture identity after unrelated web changes.

## Provider evidence rule

The target deployer must:

1. apply the blueprint;
2. query the deployed provider and associated application;
3. read the actual application slug;
4. derive `https://auth.molehill.cloud/application/o/<deployed-slug>/`;
5. require equality with the frozen issuer;
6. fetch discovery and JWKS inside the identity container;
7. fail closed on any mismatch.

The provider, discovery and JWKS are not yet proven because no post-merge deployment request has run.

## CI repair evidence

- AI Platform tests passed repeatedly with `1036 passed, 71 skipped`; failures were import order and deterministic formatter differences.
- Freqtrade pre-commit passed mypy before reporting only deployer import layout, unused `noqa` directives and formatting.
- Exact repository Ruff fixes and formatting were applied in commit `742e9b892f9b10ebfd1739135eb92b56985b9d6c`.
- The isolated formatter workflow was removed in commit `246e81a46528fc04b0a3c33dda638abbb5ddaf49`.
- Security analysis passed on the preceding exact head.
- No PR comments or unresolved review threads existed at the last inspection.

All workflows must pass again on the final head after the exact `develop` refresh and this checkpoint commit.

## Safety boundary

No live capital, production trading, real exchange orders, withdrawals, exchange credentials in GitHub, destructive restore, database host publication, Docker socket, privileged mode, host networking or unauthenticated public terminal state is authorized.

Any Freqtrade runtime remains dry-run and receives no order authority.

## Remaining gates

1. Require every applicable workflow green on the exact final PR 903 head.
2. Require PR 903 mergeable, current with `develop` and free of unresolved review threads.
3. Merge PR 903 with `expected_head_sha`.
4. Close superseded PR 876 without merge.
5. Create a separate request-only PR containing exactly:

```text
deploy/synology/portal-oidc/run-requests/public-oidc-20260801-v1.json
```

6. Validate the secret-free deployment artifact and close the request PR without merge.
7. Owner performs password plus TOTP browser acceptance.
8. Confirm missing membership fails closed.
9. Obtain the exact target principal subject without storing it in GitHub.
10. Run explicit exact-principal bootstrap on the target.
11. Confirm authenticated access and logout invalidation.

## Context checkpoint

```yaml
checkpoint_version: 4
updated_at: 2026-08-01T09:04:00+02:00
develop_head: 3afe281de86673902ded7625d6dade94105b5ee9
develop_refresh_merge: 2ab38527de472a37ded855c93d6a26872f77df73
formatted_code_head: 742e9b892f9b10ebfd1739135eb92b56985b9d6c
branch: feat/portal-authentik-public-oidc-20260801
pr: "#903"
status: in_progress
proven:
  - feature branch contains exact develop head 3afe281de86673902ded7625d6dade94105b5ee9
  - incoming develop changes did not overlap Portal OIDC paths
  - public runtime has no automatic membership grant
  - blueprint contains no client secret and uses the exact public callback
  - deployment contract refuses bootstrap, restore and live-capital authorization
  - competing fixture deployment on port 3031 is retired
  - deployer has repository-generated Ruff fixes and formatting
derived:
  - actual issuer is trusted only after target provider query and discovery equality
unknown:
  - final exact-head PR 903 CI result
  - target public discovery and JWKS result
  - exact first principal subject
  - password/TOTP browser acceptance and logout result
conflicts: []
first_failure:
  marker: PR_903_FINAL_EXACT_HEAD_CI_PENDING
  evidence: exact develop refresh and checkpoint require a new complete CI set
blockers:
  - exact-head CI must pass before merge
  - deployment requires merged implementation and separate frozen request PR
  - password/TOTP and exact-principal bootstrap require owner interaction
next_action: validate every workflow on the exact PR head, repair concrete failures, then merge with expected_head_sha
```

Terminal evidence must include:

```text
secret_values_recorded=false
live_capital_authorized=false
```
