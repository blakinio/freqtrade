# PI-07 HashiCorp Vault Credential Broker

## Status and scope

PI-07 implements the repository-side secret boundary selected by the owner on 2026-07-28. HashiCorp Vault is the only credential backend for this package. The implementation is TLS-only, private-network-only, audited, withdrawal-disabled and dry-run-only.

This package does not submit an order. Private Freqtrade submission remains PI-08, position/order command activation remains BM-07, and live capital remains P14.

## Trust boundary

```text
Portal/BFF
  -> control/execution backend
  -> PI-07 VaultCredentialBroker
  -> private TLS Vault AppRole + KV v2
  -> bounded in-memory credential lease
  -> trusted private runtime consumer
```

Browsers receive only the existing opaque `credential_ref` and secret-free connection status. They never receive:

- Vault tokens, RoleIDs or SecretIDs;
- exchange API keys, secrets or passphrases;
- runtime API usernames or passwords;
- physical Vault paths or private runtime endpoints.

## Credential record

The broker constructs the Vault path from validated tenant and opaque-reference segments. It does not accept an arbitrary Vault path from an API request.

A KV v2 document contains exact tenant, connection, reference and exchange identity plus secret values and mandatory policy flags. The broker rejects the document unless:

- all identities match the lease request;
- `withdrawals_enabled` is false;
- `dry_run_only` is true;
- it is not revoked;
- `rotated_at` is not in the future and is younger than 90 days;
- the request execution mode is `dry_run`.

KV metadata drives the existing BM-06 `CredentialReferenceStatusPort` without exposing secret values. The public states remain `CURRENT`, `ROTATION_REQUIRED`, `REVOKED` and `UNAVAILABLE`.

## AppRole and token policy

The broker reads RoleID and SecretID from protected mounted files. Login tokens:

- have a 10-minute TTL;
- cannot exceed 15 minutes;
- are kept in mutable process memory and cleared on replacement or shutdown;
- receive only the `portal-credential-broker` read policy.

The AppRole SecretID is valid for 24 hours and is rotated by a dedicated owner-managed one-shot operator. No root/operator token is available to the broker.

## Lease behavior

A successful resolution creates a five-minute in-memory lease. Secret values are held in mutable buffers, made available only through callback-based use, and overwritten when the lease closes. The serializable evidence includes identity, Vault version, rotation time, issue/expiry time and an opaque digest reference, but no secret field or Vault path.

Python cannot guarantee that every interpreter or third-party-library copy is physically erased. The design therefore additionally minimizes lifetime and copying, forbids serialization, keeps use callback-scoped, and destroys the broker-owned mutable buffers deterministically.

## Transport

The HTTP transport requires:

- HTTPS;
- a private/internal host or explicitly allowed internal hostname;
- owner-managed CA verification;
- no redirects;
- no embedded URL credentials;
- bounded timeout and response size;
- `trust_env=false`, preventing proxy-environment routing.

Authentication, transport, protocol, unavailable, scope, policy, revocation and rotation failures use stable reason codes and never include secret values.

## Synology target

`deploy/synology/portal-vault/` supplies:

- Vault 2.0.3 pinned by full multi-platform index digest;
- integrated Raft storage;
- TLS 1.3-only listener;
- no host-published port;
- internal Docker networking;
- read-only container root and dropped capabilities;
- separate persistent volumes for two file audit devices;
- idempotent KV v2/AppRole/policy/audit bootstrap;
- daily AppRole SecretID rotation operator;
- static deployment validator and invariant tests.

Repository validation does not prove a real Synology deployment, initialization, unseal, certificate ownership, audit retention, backup/restore or runtime connectivity. Those require separate owner-managed target acceptance.

## Rotation and revocation

Exchange/runtime credential data must be replaced before 90 days. Rotation is a new KV v2 version with updated `rotated_at` and matching custom metadata. A revoked, deleted or destroyed version fails closed. Revocation must also update the exchange-connection product status through the existing BM-06 inspection seam.

## Acceptance evidence

PI-07 acceptance requires focused broker, tenant-isolation, redaction, lease-clearing, withdrawal, rotation, Vault transport and deployment invariant tests plus full repository CI on the exact reviewed head.
