# PI-06 Authentik/Synology Deployment Package

Status: **repository package implemented; owner-managed target acceptance blocked**

## Scope

This package turns the accepted PI-06 identity decision into a deterministic, secret-free Synology Docker Compose delivery artifact. It intentionally stops before provisioning real infrastructure or claiming successful login, MFA, recovery or restore.

The stack contains only:

- Authentik server;
- Authentik worker;
- PostgreSQL;
- named persistent volumes;
- an internal database network;
- a loopback-only HTTP listener intended for an owner-managed local reverse proxy or Cloudflare Tunnel.

Authentik and PostgreSQL are pinned by exact version and multi-platform image digest. The package has no Redis dependency because the selected Authentik release line uses PostgreSQL-backed task processing. The Authentik containers explicitly listen on IPv4 inside the container because Authentik 2026.5 changed its default listener to IPv6 wildcard, which can fail on IPv4-only Synology environments.

## Security boundaries

- No committed password, secret key, client secret, session key, encryption key, recovery code or user identity.
- No public database port.
- No public wildcard Authentik bind.
- No Docker socket mount or managed Docker outpost.
- No privileged container or host networking.
- No `/etc/localtime` or `/etc/timezone` mount.
- Database traffic stays on an internal Compose network.
- Browser and portal code still use the merged same-origin BFF; Authentik does not become the product authorization source.
- Cloudflare Access and P11 remain separate.

## Image policy

The checked deployment contract pins:

- `docker.io/authentik/server:2026.5.5` by digest;
- `docker.io/library/postgres:16.13-alpine3.23` by digest.

A future upgrade changes both the exact tag and digest in one reviewed package. Authentik major releases must be upgraded sequentially, and server, worker and any future outpost must remain on the same Authentik version.

## Bootstrap policy

Initial administration uses a one-shot `AUTHENTIK_BOOTSTRAP_PASSWORD_HASH` held in a chmod-600 file outside Git. `bootstrap.sh` refuses a non-empty database, starts the stack with the hash, waits for health, then recreates server and worker without bootstrap material and removes the one-shot file.

The package never derives tenancy or portal administration from email, IdP groups or first login. After Authentik setup, the portal principal and membership still require the explicit restricted PI-06 portal bootstrap path.

## Backup and restore

`backup.sh` stops server and worker for a consistent maintenance window, streams a PostgreSQL custom-format dump and the media/template volumes directly into `age` encryption, and writes SHA-256 checksums. No plaintext SQL archive is created.

`restore.sh` requires a destructive confirmation phrase, verifies checksums, stops application services, restores the database and volumes, restarts the stack and runs Authentik health checks. Real restore acceptance requires a separate owner-managed exercise on non-production target resources.

## Acceptance state

Repository evidence may prove syntax, invariant checks, Compose rendering and deterministic tests. It cannot prove:

- Synology CPU/RAM/storage suitability;
- real container pulls on the target architecture;
- real DNS/TLS/Tunnel routing;
- OIDC login or callback;
- WebAuthn/TOTP enrollment and challenge;
- logout/back-channel revocation against the target IdP;
- recovery and break-glass operation;
- encrypted backup retention or successful target restore;
- Cloudflare P11 acceptance.

Those items remain blocked until the owner supplies and operates the target resources without committing secrets.
