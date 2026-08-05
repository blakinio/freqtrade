# Portal schema integrity and migration authority

## Status and scope

The Portal database authority is `ai_platform.portal.database.schema` and its command-line entry point is `python -m ai_platform.portal.database.cli`. It owns the ordered durable schema manifest, exact schema revision chain, readiness comparison, migration serialization and value-free integrity evidence for the Portal.

The supported production database dialect is PostgreSQL. SQLite remains supported only for local development and tests. Every SQLite connection enables and verifies `PRAGMA foreign_keys=ON`; SQLite success is not production-dialect evidence.

The authoritative revision chain is:

1. `20260803_01_portal_authoritative` — the original exact 41-table Portal schema;
2. `20260805_02_oidc_logout_replay` — adds the durable OIDC back-channel logout replay table.

The current revision is valid only when all of the following match:

- the complete ordered revision sequence and identifiers;
- database dialect for every revision;
- deterministic schema fingerprint for every revision;
- current tables and columns;
- column types, nullability and server defaults;
- primary, unique and check constraints;
- foreign keys and delete behavior;
- indexes.

Readiness fails closed for a missing, pending, duplicated, unknown, reordered or divergent revision and for any unexpected Portal table.

## Startup and deployment contract

Application startup never creates or alters the schema. The required order is:

1. create a database backup;
2. run the read-only integrity scan;
3. quarantine and investigate any orphaned hard relation;
4. run `python -m ai_platform.portal.database.cli migrate` from the exact deployment image;
5. run `python -m ai_platform.portal.database.cli check` from the same image;
6. start the application only after the check reports `status: ready`;
7. preserve the secret-free readiness report with the exact image and source revision.

The migration runner uses a PostgreSQL transaction-scoped advisory lock. Concurrent exact-image invocations converge on the same ordered revision chain. PostgreSQL DDL and each revision record are committed atomically; a failure rolls the current migration transaction back. A runtime restart or connection-pool replacement must re-run readiness before accepting traffic.

An existing database at the exact revision-1 fingerprint may upgrade to revision 2 by creating only `portal_oidc_logout_replays` and appending the second revision row. A database that merely resembles revision 1 but has an unknown row, altered table, missing index, extra table or different fingerprint is not upgraded automatically.

A fresh empty database is created directly at the current schema and records both ordered revision rows. This makes revision history and readiness equivalent between fresh creation and an exact `1→2` upgrade.

No migration or readiness command authorizes trading, withdrawals, protected production deployment or live capital.

## OIDC logout replay evidence

`portal_oidc_logout_replays` stores no raw logout token. Its primary key is a SHA-256 digest of the canonical `(issuer, client_id, jti)` tuple. The exact bounded tuple values are retained to detect a theoretical digest collision, and a separate SHA-256 request fingerprint binds the validated subject and IdP session semantics.

The first transaction owns the replay key and atomically performs all of the following:

- creates the processing reservation;
- revokes matching sessions;
- writes the single identity audit event;
- stores the terminal revoked-session count and processing timestamp;
- changes the reservation to `completed`;
- commits all records together.

A rollback removes the processing reservation together with every mutation. Therefore a committed `processing` record is treated as invalid state rather than as a successful request.

An exact replay returns the original terminal result and performs no second revocation or audit write. The same `(issuer, client_id, jti)` with different validated semantics fails closed with a non-enumerating conflict response.

Repository acceptance includes SQLite restart evidence and two independent PostgreSQL connections proving one mutation owner. It does not constitute protected Authentik staging evidence or authorize a protected deployment.

## Existing data and quarantine policy

A database containing Portal tables without the authoritative revision table is never adopted or modified automatically. The command fails with `UnversionedSchemaError` and records only table names and relation counts.

The required repair workflow is:

1. stop writers;
2. take and verify a backup;
3. run `scan` and retain its value-free report;
4. quarantine the database when any hard relation has orphans;
5. determine the source and owner of every orphan without deleting, reassigning or rewriting evidence;
6. rebuild the authoritative schema in an empty database;
7. restore only owner-approved rows through bounded, tenant-aware import logic;
8. run `check` and application reconciliation;
9. retain rollback access to the last known-good backup.

Immutable audit, security, risk, order, trade, model and event evidence must not be silently repaired. A repository change may define a deterministic repair, but execution against protected data requires separate owner authorization.

## Hard relational contracts

The following relations are database-enforced because the child has no valid meaning without the parent and cross-tenant substitution would violate authorization or evidence integrity:

| Child | Parent | Key | Delete behavior |
| --- | --- | --- | --- |
| `portal_bot_config_revisions` | `portal_bots` | `(tenant_id, bot_id)` | `RESTRICT` |
| `portal_tenant_memberships` | `portal_identity_principals` | `principal_id` | `RESTRICT` |
| `portal_identity_sessions` | `portal_tenant_memberships` | `(membership_id, principal_id)` | `RESTRICT` |
| `portal_risk_decisions` | `portal_trade_intents` | `(tenant_id, trade_intent_id)` | `RESTRICT` |
| `portal_model_promotion_slots` | `portal_model_versions` | `(tenant_id, current_model_version_id)` | `RESTRICT` |
| `portal_bot_command_history` | `portal_bot_commands` | `(scope_tenant_id, command_id)` | `RESTRICT` |
| `portal_bot_command_idempotency_conflicts` | `portal_bot_commands` | `(scope_tenant_id, existing_command_id)` | `RESTRICT` |

The integrity scanner evaluates these relations without returning row values.

## Intentional soft references

The following identifiers are intentionally not foreign keys. They represent historical evidence, provider-owned identities, immutable external facts or a command that may not have been accepted into the local authoritative store.

| Field | Reason for soft reference | Required application validation |
| --- | --- | --- |
| audit and event `actor_id` | actor may be external, deleted or retained only as historical evidence | non-empty bounded identifier; tenant authorization at write time |
| identity audit `principal_id` and `membership_id` | audit must survive account and membership lifecycle changes | validate existing identity when action targets a live account; preserve original value afterward |
| session revocation `session_id_hash` and `idp_session_id` | revocation may arrive after local session expiry or deletion | hashed/bounded input; issuer and principal scope validation |
| model promotion history `from_model_version_id` and `to_model_version_id` | immutable promotion evidence must survive later registry retention changes | referenced model must exist and belong to the tenant at transition time |
| learning source, hypothesis, experiment and candidate identifiers | evidence can originate from retained or external experiment systems | tenant-scoped existence and state checks before mutation |
| intelligence snapshot/outcome analysis identifiers | imported trade and inference evidence may have independent retention | tenant-scope and payload-consistency checks before analysis persistence |
| telemetry runtime, source and configuration identifiers | provider/runtime identities are authoritative outside this schema | trusted-provider reconciliation and tenant binding before persistence |
| bot command conflict `attempted_command_id` | rejected attempt is deliberately absent from the accepted command store | bounded identifier and digest evidence retained in the conflict record |
| operational order, position and trade source identifiers | trusted runtime/provider owns their lifecycle | provider reconciliation, tenant binding and monotonic observation rules |

A soft reference must never be converted into a hard foreign key solely to satisfy drift tooling. Its boundary validation and retention purpose must be preserved.

## Backup and restore evidence

The schema workflow creates an authoritative PostgreSQL database, records the exact ordered revisions, takes a database backup, restores it into an empty database and runs readiness against the restored database. Passing evidence proves schema/revision preservation only; it does not prove a protected-production backup, protected data recovery time or owner acceptance.

## Evidence boundaries

Generated schema artifacts contain names, counts, constraint definitions, fingerprints, dialect and revision metadata. They must not contain database URLs, passwords, tokens, row values, private endpoints or protected identifiers. Fixture, simulator, SQLite and ephemeral PostgreSQL evidence must be labelled as such and must never be described as protected-target execution proof.
