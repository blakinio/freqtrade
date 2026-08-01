---
task_id: FTAI-20260731-portal-local-authentik-oidc-integration
status: active
branch: feat/portal-local-authentik-oidc-20260731
base_branch: develop
created: 2026-07-31
updated: 2026-07-31
related_pr: 876
owned_paths:
  - .github/workflows/portal-oidc-local-test-deploy.yml
  - ai_platform/portal/identity/local_test_runtime.py
  - ai_platform/portal/identity/oidc.py
  - ai_platform/portal/identity/runtime.py
  - ai_platform/portal/web/lib/identity.ts
  - deploy/synology/portal/Dockerfile
  - deploy/synology/portal-oidc/
  - tests/ai_platform/portal/identity/test_oidc.py
  - tests/ai_platform/portal/deployment/test_portal_oidc_local_deploy.py
  - docs/agents/tasks/FTAI-20260731-portal-local-authentik-oidc-integration.md
---

# Portal local Authentik OIDC integration

## Goal

Replace the Synology Portal identity fixture with a real local Authentik OIDC Authorization Code + PKCE flow while preserving the LAN-only test boundary, target-owned secrets, local portal sessions and all no-live-capital controls.

## Frozen product contract

- Portal origin: `http://192.168.1.2:3031`.
- Browser callback: `http://192.168.1.2:3031/api/identity/callback`.
- Authentik issuer: `http://192.168.1.2:9000/application/o/freqtrade-portal-local/`.
- Client ID: `freqtrade-portal-local`.
- Scopes: `openid profile email`.
- Immutable principal key: OIDC `iss` + `sub`.
- MFA context: OIDC `amr` or `acr`, enforced by the portal for the local administrator membership.
- Browser session authority: opaque portal-owned session through the Next.js BFF and the internal Python identity session API.

## Security and deployment contract

- Normal identity transport remains HTTPS-only with `__Host-*` Secure cookies.
- Plain HTTP is accepted only when `PORTAL_ENVIRONMENT=test`, identity fixture is disabled, and `PORTAL_IDENTITY_TRANSPORT_MODE=local_http_test` is explicit.
- Local HTTP accepts only private or loopback addresses and same-origin discovery endpoints.
- Authentik provider/application configuration is an idempotent blueprint.
- Authentik generates and preserves the confidential client secret.
- The deployment reads the secret only inside the trusted Synology execution, records it only in a persistent `0600` runtime env file, and refuses silent rotation.
- The control-plane container has no host-published port.
- PostgreSQL remains unpublished.
- No application mounts the Docker socket or uses privileged/host networking.
- Portal data remains fixture/test data; identity is real OIDC.
- No exchange credentials, live trading, withdrawals, restore, public ingress or live capital are authorized.

## Checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-31T18:43:00+02:00
branch: feat/portal-local-authentik-oidc-20260731
base_branch: develop
pr: 876
head: e96354b40c3476d5d59687a6aab567933a35862b
status: active
proven:
  - The Next.js BFF browser callback is /api/identity/callback.
  - The Python session API callback is /v1/identity/callback and is reached only by the BFF.
  - The OIDC client requires openid, profile and email scopes and validates issuer, audience, nonce, PKCE and signed JWKS tokens.
  - Portal product membership is local and cannot be granted from email, domain or browser tenant input.
  - The existing Authentik stack is healthy and persists its runtime secrets under the protected Synology staging state directory.
  - The existing Portal preview is on private-LAN TCP 3031 and currently uses fixture identity.
  - Implementation PR 876 was opened against develop from exact head e96354b40c3476d5d59687a6aab567933a35862b.
derived:
  - A separate internal identity session API is required because the deployed Next.js Portal does not itself host the Python identity service.
  - The LAN-only HTTP target requires a narrowly gated test transport because production cookies and issuer validation are HTTPS-only.
unknown:
  - The final exact implementation merge SHA and deployment request PR number.
  - The Authentik-generated provider client secret value; it must remain unknown outside Synology.
  - Whether full browser acceptance will stop at the owner's interactive MFA challenge.
first_failure:
  marker: EXACT_HEAD_CI_PENDING
  evidence: PR 876 must pass all required exact-head checks before merge.
validation_required:
  - focused OIDC and identity tests
  - Authentik blueprint/deployment contract tests
  - Docker build and Compose render gates
  - Ruff and Ruff format
  - pre-commit and codespell where applicable
  - GitHub Actions security analysis
  - AI Platform CI
  - Freqtrade CI
  - CI Gate
blockers: []
next_action: Resolve all exact-head PR 876 CI failures, merge with expected_head_sha, then create exactly one frozen deployment request from the resulting develop SHA.
```
