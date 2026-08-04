# Portal schema integrity and migration authority

## Status and scope

The Portal database authority is `ai_platform.portal.database.schema` and its command-line entry point is `python -m ai_platform.portal.database.cli`. It owns the ordered durable schema manifest, exact schema revision, readiness comparison, migration serialization and value-free integrity evidence for the Portal.

The supported production database dialect is PostgreSQL. SQLite remains supported only for local development and tests. Every SQLite connection enables and verifies `PRAGMA foreign_keys=ON`; SQLite success is not production-dialect evidence.

The current authoritative revision is `20260803_01_portal_authoritative`. The revision is valid only when all of the following match:

- revision sequence and identifier;
- database dialect;
- deterministic schema fingerprint;
- tables and columns;
- column types, nullability and server defaults;
- primary, unique and check constraints;
- foreign keys and delete behavior;
- indexes.

Readiness fails closed for a missing, pending, duplicated, unknown or divergent revision and for any unexpected Portal table.

## Startup and deployment contract

Application startup never creates or alters the schema. The required order is:

1. create a database backup;
2. run the read-only integrity scan;
3. quarantine and investigate any orphaned hard relation;
4. run `python -m ai_platform.portal.database.cli migrate` from the exact deployment image;
5. run `python -m ai_platform.portal.database.cli check` from the same image;
6. start the application only after the check reports `status: ready`;
7. preserve the secret-free readiness report with the exact image and source revision.

The migration runner uses a PostgreSQL transaction-scoped advisory lock. Concurrent exact-image invocations converge on one revision row. PostgreSQL DDL and the revision record are committed atomically; a failure rolls the revision back. A runtime restart or connection-pool replacement must re-run readiness before accepting traffic.

No migration or readiness command authorizes trading, withdrawals, protected production deployment or live capital.

## Existing data and quarantine policy

A database containing Portal tables without the authoritative revision is never adopted or modified automatically. The command fails with `UnversionedSchemaError` and records only table names and relation counts.

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

The schema workflow creates an authoritative PostgreSQL database, records the exact revision, takes a database backup, restores it into an empty database and runs readiness against the restored database. Passing evidence proves schema/revision preservation only; it does not prove a protected-production backup, protected data recovery time or owner acceptance.

## Evidence boundaries

Generated schema artifacts contain names, counts, constraint definitions, fingerprints, dialect and revision metadata. They must not contain database URLs, passwords, tokens, row values, private endpoints or protected identifiers. Fixture, simulator, SQLite and ephemeral PostgreSQL evidence must be labelled as such and must never be described as protected-target execution proof.
