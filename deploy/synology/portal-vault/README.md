# PI-07 HashiCorp Vault on Synology

This package defines the repository-validated deployment target for the private PI-07 credential broker. It does not contain credentials and does not prove that a real Synology target has been initialized or accepted.

## Security boundary

- Vault is reachable only on the Docker `portal_vault_private` network.
- No Vault port is published on the host and no Cloudflare/public route is allowed.
- The listener accepts TLS 1.3 only and uses owner-managed certificate files.
- Integrated Raft storage persists on `portal_vault_data`.
- Two independent file audit devices persist on separate named volumes.
- The broker AppRole has read-only access to exact tenant credential paths.
- Broker tokens live for 10 minutes and cannot exceed 15 minutes.
- AppRole SecretIDs live for 24 hours and must be rotated with the dedicated profile.
- Exchange credentials must declare `withdrawals_enabled=false`, `dry_run_only=true`, and must be rotated before 90 days.

## Required owner-managed files

Create these outside the repository checkout with restrictive permissions:

```text
/volume1/docker/portal-vault/tls/ca.crt
/volume1/docker/portal-vault/tls/vault.crt
/volume1/docker/portal-vault/tls/vault.key
/volume1/docker/portal-vault/operator/vault-operator-token
/volume1/docker/portal-vault/approle/
```

The Vault certificate must be valid for the internal DNS name `vault`. The operator token file must be mode `0400` or `0600`. The AppRole output directory must be writable only by the portal operator and broker runtime.

## Repository validation

```bash
python deploy/synology/portal-vault/validate_vault.py \
  --env-file deploy/synology/portal-vault/.env.example \
  --example
```

For a real environment, copy `.env.example` to a protected file outside Git and run validation without `--example`.

## Start, initialize and bootstrap

```bash
docker compose --env-file /protected/portal-vault.env up -d vault
docker compose --env-file /protected/portal-vault.env exec vault vault operator init
docker compose --env-file /protected/portal-vault.env exec vault vault operator unseal
docker compose --env-file /protected/portal-vault.env --profile bootstrap run --rm bootstrap
```

Initialization output contains root and unseal material. Never store it in this repository, shell history, Docker logs or the NAS project directory. Follow the canonical runbook before executing these commands.

## AppRole SecretID rotation

Run at least daily, before the current 24-hour SecretID expires:

```bash
docker compose --env-file /protected/portal-vault.env \
  --profile rotate-approle run --rm rotate-approle-secret-id
```

Schedule this through an owner-managed Synology task using a protected environment file. The role ID remains stable; the SecretID file is atomically replaced with mode `0600`.

## Credential writes

Credential values are written by an authorized operator, never by the read-only broker. Every KV v2 record and its custom metadata must bind:

```text
tenant_id
connection_id
credential_ref
exchange_id
rotated_at
revoked=false
withdrawals_enabled=false
dry_run_only=true
```

The server-side path is:

```text
portal-secrets/tenants/<tenant_id>/exchange-connections/<credential_ref>
```

Do not expose the physical Vault path in portal APIs or browser data.
