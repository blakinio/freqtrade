# AI Trading Portal — Model Control Foundation

## Purpose

P5 adds a portal-owned control layer over immutable model identities without becoming a new research engine and without mutating existing bot configuration revisions.

The implementation lives under:

```text
ai_platform/portal/model_control/
```

It consumes the canonical P1 `ModelVersion`, audit and event contracts and reuses the P2 database/session plus transactional audit/outbox persistence pattern.

## Authority boundaries

The layers remain separate:

```text
Research registry
  -> reproducible evidence and candidate/validated research state

P5 model control
  -> immutable portal model metadata
  -> promotion-slot policy
  -> promotion / rollback history
  -> validation of future model assignment

P2 BotConfigRevision
  -> immutable concrete model assignment for a bot revision

Execution runtime
  -> runs the exact model pinned by the selected bot configuration revision
```

P5 does not reinterpret the research registry as deployment authority. Registering a model in P5 does not promote it, revise a bot, restart a runtime or change a running assignment.

## Immutable model registry

`portal_model_versions` stores the canonical serialized `ModelVersion` keyed by:

```text
(tenant_id, model_version_id)
```

There is intentionally no repository operation that updates an existing `ModelVersion` row. A duplicate identity is rejected instead of overwriting artifact, dataset, feature, parameter, training-window or Git identity.

The original canonical `ModelVersion.lifecycle_state` is also preserved as registered metadata. Promotion-slot changes do not rewrite that immutable record.

## Promotion slots

A promotion slot is keyed by:

```text
(tenant_id, model_family_id, environment)
```

and points to exactly one immutable `model_version_id`.

The slot is policy for future assignment. It is not a second mutable model pointer inside a running bot.

Changing a slot therefore does not modify any existing `BotConfigRevision`. To apply a different model to a bot, the control plane must create a new immutable bot configuration revision through its own owned workflow after P5 assignment validation succeeds.

## Promotion eligibility

P5 accepts only the following canonical model lifecycle states as promotion-slot targets:

```text
VALIDATED
PROMOTED
DRY_RUN
SHADOW
```

P5 rejects promotion of:

```text
EXPERIMENTAL
CANDIDATE
LIVE_SMALL
PRODUCTION
DEPRECATED
REJECTED
```

This deliberately prevents the portal foundation from turning experimental or live-capital lifecycle labels into assignment authorization.

Promotion requires the canonical `model.promote` capability.

## Registration

Registration requires `model.train` capability because P1 currently has no narrower `model.register` capability.

A successful registration transaction writes atomically:

1. immutable `portal_model_versions` metadata;
2. canonical `model.registered` audit evidence;
3. canonical `model.registered` outbox event.

Registration never creates or changes a promotion slot.

If audit/outbox persistence fails, the model registration is rolled back with the transaction.

## Promotion

A promotion transaction:

1. resolves the tenant-scoped immutable model;
2. verifies its lifecycle state is eligible;
3. rejects an already-active target;
4. changes the tenant/family/environment promotion slot;
5. appends a `PROMOTE` transition to promotion history;
6. writes canonical `model.promoted` audit evidence;
7. writes canonical `model.promoted` outbox evidence.

All writes occur in one database transaction.

## Rollback

Rollback selects a previously promoted immutable version. It never edits the target artifact or model identity.

A rollback is accepted only when:

- a current promotion slot exists;
- the target differs from the current slot target;
- the target model exists in the same tenant;
- the target belongs to the same model family;
- the target lifecycle state remains P5-assignable;
- the target was previously reached by a `PROMOTE` transition in the same tenant/family/environment slot.

A successful rollback atomically changes the slot, appends a `ROLLBACK` history transition and writes canonical `model.rolled_back` audit/outbox evidence.

A prior rollback alone does not manufacture promotion eligibility: rollback targets must have historical evidence of an explicit promotion in that same slot.

## Assignment validation

`ModelControlService.validate_new_assignment()` is deliberately read-only.

Given a prospective immutable `BotConfigRevision`, it verifies that:

1. the revision belongs to the request tenant;
2. the pinned model exists in that tenant;
3. the current promotion slot for that model family and revision environment exists;
4. the slot points to the exact `model_version` pinned by the revision.

It does not persist or mutate the bot revision. P2 remains the owner of bot configuration state.

This prevents a newly registered challenger from silently replacing the model used by an existing or future bot revision.

## Tenant isolation and permissions

All model reads and lifecycle mutations are scoped by `tenant_id`.

Capability baseline:

```text
model.read     -> model/slot/history reads and assignment validation
model.train    -> immutable model registration
model.promote  -> promotion and rollback
```

Cross-tenant model identifiers are not resolved through another tenant's registry.

## Transactional evidence

P5 writes audit and outbox records through the canonical P2 persistence tables and P1 envelopes.

For registration, promotion and rollback, domain-state changes and evidence are committed in the same transaction. An outbox write failure therefore rolls back the associated model or promotion-slot mutation.

P4 remains responsible for later at-least-once outbox publication and observability. P5 does not redefine P4 delivery semantics.

## Persistence

P5 introduces:

```text
portal_model_versions
portal_model_promotion_slots
portal_model_promotion_history
```

`portal_model_promotion_history` is append-only through the repository interface. It records explicit transition provenance separately from the current promotion slot read model.

## Protected research boundaries

P5 does not:

- train or tune models;
- run model comparison or backtests;
- consume protected final holdout `20260801-20260930`;
- alter frozen thresholds `0.006/-0.009`;
- reopen completed Phase 6 or change authoritative `selected_model = null`;
- reinterpret PyTorch or RL evidence as promotion authorization;
- enable live capital;
- mutate P2 bot state or P4 event/observability contracts.

The existing research lifecycle and evidence remain authoritative inputs to future separately governed workflows.
