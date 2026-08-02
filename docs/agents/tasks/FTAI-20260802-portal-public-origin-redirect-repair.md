---
task_id: FTAI-20260802-portal-public-origin-redirect-repair
status: active
branch: fix/portal-public-origin-redirect-20260802
base_branch: develop
created: 2026-08-02
updated: 2026-08-02
parent_task: FTAI-20260801-portal-authentik-public-oidc-handover
owned_paths:
  - ai_platform/portal/web/lib/identity.ts
  - ai_platform/portal/web/app/api/identity/callback/route.ts
  - ai_platform/portal/web/app/api/identity/login/route.ts
  - deploy/synology/portal-oidc/deploy.py
  - tests/ai_platform/portal/deployment/test_portal_oidc_public_origin.py
  - docs/agents/tasks/FTAI-20260802-portal-public-origin-redirect-repair.md
---

# Portal public-origin redirect repair

## Incident

After successful Authentik password and TOTP authentication, the public callback created the Portal session but returned a browser redirect to `https://0.0.0.0:3000/`. Chrome rejected the non-routable container address with `ERR_ADDRESS_INVALID`.

## Confirmed cause

The Next.js callback route built the final redirect from `request.nextUrl.origin`. Behind Cloudflare Tunnel and the container listener, that origin can be the internal listener address rather than the public Portal origin.

## Required result

- final callback redirects use an explicit trusted `PORTAL_PUBLIC_ORIGIN`;
- production fails closed if the public origin is absent or invalid;
- local fixture/test mode may use the request origin as a bounded fallback;
- the Synology web container receives `PORTAL_PUBLIC_ORIGIN=https://quant.molehill.cloud`;
- target-side deployment proves a fixture callback returns a `Location` on the public HTTPS origin;
- existing Authentik secret, Portal keys and exact owner membership remain unchanged;
- no restore, trading, withdrawal or live-capital authority.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-08-02T10:58:00+02:00
status: active
proven:
  - Authentik password and TOTP completed in the owner browser
  - callback redirected to internal 0.0.0.0:3000
  - callback route currently derives the final origin from request.nextUrl.origin
unknown:
  - exact-head implementation CI result
  - target-side public-origin callback probe result
blockers: []
next_action: implement trusted public-origin redirects, add target-side callback probe, validate, merge and deploy
```

```text
secret_values_recorded=false
live_capital_authorized=false
```
