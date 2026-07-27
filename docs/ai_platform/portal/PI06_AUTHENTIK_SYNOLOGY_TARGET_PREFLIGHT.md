# PI-06 Authentik/Synology Target Preflight

## Purpose

This package verifies the real Synology staging runner and the owner-managed inputs required before any Authentik deployment mutation. It converts the remaining PI-06 boundary from an assumed external blocker into a deterministic, non-sensitive readiness report.

The preflight is not deployment or target acceptance. It must not start, stop, recreate, pull or remove containers; create Authentik users; bootstrap an administrator; change DNS/TLS; execute recovery; restore data; or claim successful OIDC/MFA behavior.

## Runner and environment mapping

The guarded workflow targets the established staging resources:

- runner name: `freqtrade-synology-staging`;
- routing label: `freqtrade-staging`;
- protected environment: `synology-staging`;
- durable state variable: `OTERYN_STAGING_STATE_DIR=/var/lib/oteryn-staging-state`.

The runner list proves the unique custom label. The workflow routes only by that label because a job that specifies multiple labels requires the runner to possess every one of them. Once assigned, the preflight independently verifies the exact runner name and that `runner.os` is Linux before declaring readiness.

The frozen request reserves three distinct roots directly below that state directory:

- `/var/lib/oteryn-staging-state/portal-authentik`;
- `/var/lib/oteryn-staging-state/portal-authentik-backups`;
- `/var/lib/oteryn-staging-state/portal-authentik-restore`.

The workflow creates only a temporary fsync/rename/read-back probe below the existing state directory and removes it before completion.

## Protected environment variables

The `synology-staging` environment must define these non-secret variables:

- `OTERYN_STAGING_STATE_DIR`;
- `PI06_AUTHENTIK_PUBLIC_BASE_URL`;
- `PI06_PORTAL_PUBLIC_BASE_URL`;
- `PI06_PORTAL_IDENTITY_CLIENT_ID`.

Both public URLs must use HTTPS, contain no embedded credentials, query or fragment, and have resolvable DNS. The preflight records only boolean DNS results, never the URL values.

## Protected environment secrets

The environment must define:

- `PI06_AUTHENTIK_POSTGRES_PASSWORD`;
- `PI06_AUTHENTIK_SECRET_KEY`;
- `PI06_AUTHENTIK_BOOTSTRAP_PASSWORD_HASH`;
- `PI06_PORTAL_OIDC_CLIENT_SECRET`;
- `PI06_PORTAL_SESSION_HMAC_KEY_B64`;
- `PI06_PORTAL_FLOW_ENCRYPTION_KEY_B64`;
- `PI06_AUTHENTIK_AGE_RECIPIENT`.

The bootstrap value must be a Django password hash, not plaintext. The `age` value is the recipient only; the offline private recovery key must not be stored in the routine GitHub environment. Secret values are used only for in-memory validation and a chmod-600 temporary steady-state runtime file under `runner.temp`. The temporary file is removed automatically and Compose is rendered with `config --quiet`.

The report contains only required, missing or invalid variable names. It never contains secret values, private keys, passwords, client secrets or bootstrap material.

## Host checks

The preflight verifies:

1. exact runner identity and Linux scheduling;
2. Docker socket access, Docker server availability and Compose v2;
3. supported AMD64/ARM64 architecture, at least two CPU cores and 2 GiB memory;
4. Python 3, Docker, `age` and `openssl` availability;
5. writable durable storage with at least 4 GiB free;
6. atomic write, fsync, rename and read-back with cleanup;
7. distinct target, backup and isolated restore roots outside workspace and runner temp;
8. no partial Authentik named-volume or network state;
9. no unrelated container publishing the frozen loopback service port 9000;
10. fail-closed runtime environment validation and secret-safe Compose rendering.

Container, volume and network inventories are reported only as counts. The workflow does not inspect container environment variables.

## Trigger contract

The workflow is inert until a separate pull request adds exactly:

`deploy/synology/portal-authentik/run-requests/target-preflight-20260727-v1.json`

That pull request must contain no other changed path. The request authorizes only the bounded storage probe and explicitly keeps deployment, bootstrap and restore unauthorized. After terminal evidence is captured, the request PR is closed without merge.

## Result interpretation

`ready_for_controlled_deployment: true` proves only that the runner, host prerequisites, durable roots, protected input names and static runtime render are ready. It does not prove:

- Authentik or PostgreSQL startup;
- OIDC provider/application configuration;
- real login or callback behavior;
- WebAuthn/TOTP enrollment or challenge;
- portal session cookies, CSRF, logout or revocation;
- generic recovery behavior;
- encrypted backup creation or isolated restore;
- Cloudflare P11 ingress acceptance;
- any trading or live-capital authorization.

A passing report permits a separate, reviewed deployment request with exact mutation scope. A failing report leaves PI-06 active and records only the concrete missing names or host blockers.
