# PI-07 Vault Synology Runbook

## Boundary

This runbook is for an owner-managed Synology/Linux target. It never authorizes public Vault ingress, withdrawals, non-dry-run execution or live capital.

## 1. Prepare protected directories

Create these outside the Git checkout:

```bash
install -d -m 0700 /volume1/docker/portal-vault/{tls,operator,approle,backup}
```

Provision a private CA and a server certificate valid for internal DNS name `vault`. Install:

```text
tls/ca.crt       mode 0444
tls/vault.crt    mode 0444
tls/vault.key    mode 0400, readable by the Vault container user only
```

Copy `.env.example` to a protected runtime environment file and keep it mode `0600`.

## 2. Validate repository package

```bash
python deploy/synology/portal-vault/validate_vault.py \
  --env-file /volume1/docker/portal-vault/portal-vault.env
```

Resolve every validation error before starting a container.

## 3. Start Vault without publishing it

```bash
cd deploy/synology/portal-vault
docker compose --env-file /volume1/docker/portal-vault/portal-vault.env up -d vault
docker compose --env-file /volume1/docker/portal-vault/portal-vault.env ps
```

Verify that `docker port portal-vault-vault-1` reports no host mapping and that the `portal_vault_private` network is internal.

## 4. Initialize and unseal

Run initialization through `docker compose exec`, not through a host-published endpoint:

```bash
docker compose --env-file /volume1/docker/portal-vault/portal-vault.env \
  exec vault vault operator init
```

Immediately transfer root/unseal material to an offline owner-managed recovery system. Do not save it in the project directory, Docker logs, screenshots, shell history or ChatGPT.

Unseal through the same private exec boundary. After initial bootstrap, create a constrained operator token with only the mount, policy, AppRole and audit capabilities needed by the operator scripts. Revoke the initial root token after confirming recovery material and constrained administration.

Write the constrained token to:

```text
/volume1/docker/portal-vault/operator/vault-operator-token
```

Set mode `0400` or `0600`.

## 5. Bootstrap PI-07

```bash
docker compose --env-file /volume1/docker/portal-vault/portal-vault.env \
  --profile bootstrap run --rm bootstrap
```

Confirm:

```bash
docker compose --env-file /volume1/docker/portal-vault/portal-vault.env exec vault \
  vault audit list
docker compose --env-file /volume1/docker/portal-vault/portal-vault.env exec vault \
  vault secrets list
docker compose --env-file /volume1/docker/portal-vault/portal-vault.env exec vault \
  vault auth list
```

Required results are two file audit devices, KV v2 mount `portal-secrets/`, AppRole and policy `portal-credential-broker`.

## 6. Create a dry-run credential record

Use an authorized operator token. Never place values directly in the command line where shell history records them. Build a mode-`0600` temporary JSON file in a protected RAM-backed or encrypted operator location and write it through `vault kv put`.

The document must include:

```json
{
  "tenant_id": "tenant-a",
  "connection_id": "conn-okx-1",
  "credential_ref": "credref_okxDryRun01",
  "exchange_id": "okx",
  "exchange_api_key": "<protected>",
  "exchange_api_secret": "<protected>",
  "exchange_passphrase": "<protected-or-omit>",
  "runtime_api_username": "<protected>",
  "runtime_api_password": "<protected>",
  "withdrawals_enabled": false,
  "dry_run_only": true,
  "rotated_at": "2026-07-28T20:00:00Z",
  "revoked": false
}
```

Write it at:

```text
portal-secrets/tenants/tenant-a/exchange-connections/credref_okxDryRun01
```

Then set matching KV v2 custom metadata:

```text
tenant_id=tenant-a
connection_id=conn-okx-1
credential_ref=credref_okxDryRun01
exchange_id=okx
rotated_at=<same UTC timestamp>
revoked=false
withdrawals_enabled=false
dry_run_only=true
```

Delete and securely dispose of the temporary plaintext file immediately after the write.

## 7. Mount AppRole material into the broker

The bootstrap creates protected files:

```text
approle/role-id
approle/secret-id
```

Mount these read-only into the portal execution backend. Configure the broker with internal endpoint `https://vault:8200`, the private CA, KV mount `portal-secrets`, token TTL maximum 15 minutes and credential maximum age 90 days.

Do not mount the constrained operator token into the broker.

## 8. Rotate AppRole SecretID daily

Create an owner-managed Synology scheduled task that runs before the 24-hour SecretID expires:

```bash
docker compose --env-file /volume1/docker/portal-vault/portal-vault.env \
  --profile rotate-approle run --rm rotate-approle-secret-id
```

Alert on any non-zero result. The broker reads the atomically replaced file on its next AppRole login.

## 9. Rotate exchange/runtime credentials before 90 days

Create a new KV v2 version with new secret values, a new `rotated_at`, and updated custom metadata. Verify exchange permissions independently and confirm withdrawals are disabled before marking the BM-06 connection current.

At 90 days the broker returns `ROTATION_REQUIRED` and refuses resolution. Never extend the timestamp without replacing and verifying the actual credential.

## 10. Revoke

Set `revoked=true` in both the document and custom metadata, revoke the external exchange key, and refresh the BM-06 credential inspection. Destroy obsolete KV versions only after retention and incident requirements are satisfied.

## 11. Audit and capacity

Both audit volumes must remain writable. Vault can refuse API requests when every enabled audit device fails, so monitor capacity and write errors independently. Rotate audit files using an owner-managed process and signal Vault to reopen file devices after rotation.

Audit records are sensitive operational evidence. Restrict access and never upload raw logs to a public issue or PR.

## 12. Backup and restore

Use Vault integrated-storage snapshots through an authenticated private exec path. Encrypt snapshots immediately with an offline owner-controlled key, record SHA-256, and test restore on an isolated host. A repository test is not restore acceptance.

## 13. Target acceptance

Record exact image digest, certificate identities/expiry, Docker network inspection, audit-device state, AppRole policy/TTL, credential metadata, rotation test, revocation test, encrypted snapshot and isolated restore evidence. Do not record secret values.

Only after this evidence exists may the deployment be described as target-accepted. PI-08 software may use deterministic/fake Vault evidence in CI, but real private runtime submission still requires its separate reviewed package.
