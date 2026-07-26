# PI-06 Authentik/Synology Runbook

## 1. Preconditions

Use a dedicated Synology Docker project and storage path. Authentik's small Compose deployment requires at least 2 CPU cores and 2 GB RAM; reserve additional headroom for PostgreSQL, portal services and DSM. Confirm current backups before any upgrade or restore.

Required host tools:

- Docker Compose v2;
- Python 3;
- `age` and an offline recipient/private key pair;
- `openssl` for generating runtime secrets;
- enough protected storage for database and media backups.

Do not expose TCP 5432. Keep the Authentik host listener on `127.0.0.1`. Do not mount the Docker socket; this package does not deploy managed Docker outposts.

## 2. Prepare runtime configuration

Copy `.env.example` to a chmod-600 file outside the repository. Generate values interactively and avoid shell-history leakage where practical.

```bash
umask 077
openssl rand -base64 36   # PostgreSQL password, maximum 99 characters
openssl rand -base64 60   # Authentik secret key
openssl rand -base64 32   # portal session HMAC key
openssl rand -base64 32   # portal OIDC-flow encryption key
```

Keep the checked image tag+digest pairs unchanged unless a separate upgrade review authorizes replacements. Set no steady-state bootstrap password or hash.

Validate before every start:

```bash
python3 deploy/synology/portal-authentik/validate.py \
  --env-file /volume1/docker/portal-authentik/runtime.env

docker compose \
  --env-file /volume1/docker/portal-authentik/runtime.env \
  -f deploy/synology/portal-authentik/compose.yml \
  config --quiet
```

## 3. Restricted initial bootstrap

Generate a Django password hash through the pinned Authentik image using the interactive `ak hash_password` command. Put only this hash in a temporary chmod-600 file:

```text
AUTHENTIK_BOOTSTRAP_PASSWORD_HASH=<django-password-hash>
```

Run only on an empty database:

```bash
BOOTSTRAP_CONFIRM=INITIALIZE_EMPTY_AUTHENTIK_DATABASE \
ENV_FILE=/volume1/docker/portal-authentik/runtime.env \
BOOTSTRAP_ENV_FILE=/run/user/$(id -u)/authentik-bootstrap.env \
sh deploy/synology/portal-authentik/bootstrap.sh
```

The script refuses an initialized public schema, removes the temporary hash file and recreates server/worker without bootstrap material. Immediately enroll at least two hardware-backed WebAuthn authenticators for the break-glass administrator where possible, store recovery codes offline and restrict the Authentik admin route through the owner-managed privileged ingress policy.

## 4. Configure the portal OIDC application

Create an Authentik OAuth2/OIDC provider and application through the restricted admin path:

1. confidential client;
2. Authorization Code grant enabled;
3. PKCE `S256` required by the portal;
4. Implicit, Password and Device Code grants disabled;
5. exact callback URI: `https://<portal-host>/api/identity/callback`;
6. exact post-logout return allow-list;
7. back-channel logout pointed to the private identity-enabled portal API route;
8. no wildcard redirect URI;
9. no email-domain or group-based automatic tenant membership.

Inject the resulting issuer, client ID and client secret into the portal control plane using `portal-identity.env.example` as the key list. Inject the 32-byte base64 session and flow-encryption keys. Never expose these values through Next.js public variables or browser storage.

Use the explicit restricted portal bootstrap command/migration to create the first portal principal and membership. First login alone must not create product administration rights.

## 5. MFA and recovery configuration

For every mutation-capable human role:

- prefer WebAuthn/passkey or hardware key;
- permit TOTP as fallback;
- issue offline single-use recovery codes;
- prohibit email or SMS as the sole privileged factor;
- require fresh authentication for authenticator changes, recovery completion and portal membership administration.

Recovery responses must not reveal whether an account exists. Successful recovery revokes prior portal sessions and forces MFA re-enrollment when administrator assistance was required.

## 6. Health and fail-closed checks

```bash
docker compose --env-file "$ENV_FILE" -f compose.yml ps
docker compose --env-file "$ENV_FILE" -f compose.yml exec -T server ak healthcheck
docker compose --env-file "$ENV_FILE" -f compose.yml exec -T worker ak healthcheck
docker compose --env-file "$ENV_FILE" -f compose.yml exec -T worker ak dump_config >/dev/null
```

Verify:

- server, worker and PostgreSQL are healthy;
- only loopback TCP 9000 is published;
- no TCP 5432 listener exists on the host;
- no container has the Docker socket, host networking or privileged mode;
- portal protected routes fail closed if Authentik or session storage is unavailable.

## 7. Encrypted backup

Run in a maintenance window. The script briefly stops server and worker while PostgreSQL remains available.

```bash
AGE_RECIPIENT='age1...' \
BACKUP_CONFIRM=BACKUP_AUTHENTIK_DATABASE_AND_VOLUMES \
ENV_FILE=/volume1/docker/portal-authentik/runtime.env \
BACKUP_DIR=/volume1/backup/portal-authentik \
sh deploy/synology/portal-authentik/backup.sh
```

Copy the encrypted `.dump.age`, `.volumes.tar.age` and `.sha256` files to a second protected location. Test decryption and restore on isolated non-production resources periodically.

## 8. Restore exercise

A restore is destructive. Snapshot the current volumes first and use isolated non-production storage for routine exercises.

```bash
BACKUP_BASE=/volume1/backup/portal-authentik/authentik-YYYYMMDDTHHMMSSZ \
RESTORE_CONFIRM=RESTORE_AUTHENTIK_DATABASE_AND_VOLUMES \
ENV_FILE=/volume1/docker/portal-authentik/runtime.env \
sh deploy/synology/portal-authentik/restore.sh
```

After restore, prove database and application health, then perform owner-managed login, MFA challenge, portal session, logout-all and membership-revocation probes. A repository test cannot substitute for this exercise.

## 9. Upgrade and rollback

1. Read every intervening Authentik release note; major releases must be sequential.
2. Take and verify an encrypted backup.
3. Record the old image tags and digests.
4. Update Authentik server and worker together; update PostgreSQL only through its supported upgrade procedure.
5. Render Compose and run static validation before pulling.
6. Start PostgreSQL, then server and worker; inspect migrations and health.
7. Run owner-managed identity probes.
8. If acceptance fails, stop application services and restore the prior database/volumes with the prior image digests.

Do not perform an in-place PostgreSQL major-version change by replacing only the image tag. Use logical dump/restore or the documented PostgreSQL upgrade mechanism.

## 10. Owner-managed acceptance checklist

PI-06 remains `active` until durable evidence proves on the target environment:

- OIDC login and exact callback;
- MFA enrollment and challenge for WebAuthn and TOTP fallback;
- opaque host-only portal cookies and CSRF;
- logout and logout-all;
- Authentik back-channel and portal membership revocation;
- generic recovery behavior and forced MFA re-enrollment where required;
- encrypted backup creation and isolated restore;
- no direct database or Freqtrade exposure.

Cloudflare ingress/direct-origin denial is evaluated separately under P11.
