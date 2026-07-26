# AI Trading Portal — Next Work and Repair Plan

## 1. Purpose

This document is the durable continuation route for agents deciding what to implement or repair after the bounded P0-P12 portal foundation.

It exists because stage completion, product completeness and external integration readiness are different claims. A roadmap stage marked `done` means its declared bounded acceptance passed; it does not imply that every target UI capability, private provider, runtime command or production-like environment is complete.

Use this document to select the next bounded task. Use `POST_P12_INTEGRATION_BACKLOG.md` for the detailed PI package contracts and `UI_DELIVERY_STATUS.md` for truthful per-surface delivery status.

## 2. Source-of-truth order

Before starting work, verify in this order:

1. current `develop`, open PRs, active branches and required CI;
2. `AGENTS.md` and `docs/agents/CONTEXT_HANDOFF.md`;
3. `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`;
4. this plan;
5. `DELIVERY_ROADMAP.md`, `POST_P12_INTEGRATION_BACKLOG.md` and task-specific architecture documents;
6. the active dated task record and its `## Context checkpoint`.

Repository and merged-task evidence override stale status sentences. Chat history and private UI captures are not durable state.

## 3. Verified program snapshot

Snapshot date: `2026-07-26`.

### Roadmap stages

- P0-P10: `done` for their declared bounded acceptance criteria.
- P11: `blocked`; repository contracts and verifier exist, but real Cloudflare, protected GitHub staging and five-probe External E2E acceptance have not been proven.
- P12: `done` in simulation-first mode; it does not replace P11.
- P13: `deferred` after the measured-need NO-GO assessment.
- P14: `blocked`; no live-capital authorization exists.

### Post-P12 integrations

- PI-01 Private Runtime Read and Reconciliation: `done`, PR #234.
- PI-02 Authoritative Valuation and Unrealized PNL: `done`, PR #267, merge `0c8fdfe6fb50ff635403ae963484bf4e6883e1e1`.
- PI-03 Canonical Inference and Drift Telemetry: `done`, PR #239 with closure PR #260.
- PI-04 Centralized Runtime Observability: `done` for repository-side contracts, PR #261; target-environment backend connectivity remains deployment-owned and must fail closed when absent.
- PI-05 External Notification Delivery: `planned`; provider/channel and privacy policy are unresolved.
- PI-06 Product Identity and Session Lifecycle: `planned`; the IdP, membership, session, MFA, recovery and revocation decision is accepted in `PI06_IDENTITY_AND_SESSION_DECISION.md`, while implementation has not started.
- PI-07 Runtime Credential Broker and Rotation: `planned`; requires a selected secret backend and security review.
- PI-08 Private Dry-Run Approved Execution Submission: `planned`; depends on PI-07 and must remain dry-run-only.

The concrete `FreqtradeExecutionAdapter.submit_approved_intent` path remains fail-closed with `ORDER_SUBMISSION_NOT_IMPLEMENTED`. Deterministic simulator execution is not evidence of private Freqtrade order submission.

## 4. Product completion and decision packages

### 4.1 Bot Operations convergence — complete

Task `FTAI-20260726-portal-bot-operations-completion` and PR #320 complete the software-addressable bot operations workflow by composing existing backend contracts:

- `GET /v1/bots/{bot_id}`;
- `POST /v1/bots/{bot_id}/revisions` for immutable configuration revision;
- `POST /v1/bots/{bot_id}/desired-state` for capability-gated desired lifecycle state;
- canonical operations, valuation, risk, telemetry, runtime-observability and audit reads.

Delivered behavior includes:

- fleet columns for open-position count, realized/unrealized PNL state, risk state, runtime health and last attributable activity;
- environment, status, exchange, strategy, model, market and risk filters;
- bot-scoped positions, orders, trades, valuations, risk decisions, runtime logs and audit evidence;
- browser/BFF support for immutable revision creation;
- browser/BFF support for desired-state changes with permission, confirmation, conflict, stale-state and unavailable behavior;
- explicit separation of runtime lifecycle controls from trade execution authority;
- bounded server-side composition rather than unbounded browser N+1 calls;
- regression coverage for immutable revision, desired-state idempotency, conflict handling and fail-closed valuation attribution.

The package does not implement credential brokering, PI-08 order submission, external notification delivery, P11 infrastructure or live capital.

### 4.2 PI-06 identity and session decision — complete

Task `FTAI-20260726-portal-pi06-identity-decision` records the accepted product identity architecture in `PI06_IDENTITY_AND_SESSION_DECISION.md`.

Selected boundaries:

- authentik is the product IdP and owns primary authentication, authenticator enrollment, MFA challenge, IdP session and recovery flows;
- the portal database owns product principals, tenants, memberships, roles, capabilities and local session revocation;
- immutable OIDC `iss` + `sub` maps the external identity to the portal principal;
- the BFF uses Authorization Code Flow with PKCE and opaque server-side sessions; browser-readable storage receives no IdP token or refresh material;
- privileged mutation capabilities require MFA, and declared high-impact actions require authentication no older than five minutes;
- membership and role changes invalidate affected portal sessions synchronously in v1;
- Cloudflare Access remains an additional privileged-ingress control and never replaces application session, tenant or RBAC enforcement;
- Synology Docker Compose is accepted as the initial bounded target but remains a documented single-host failure domain and is not P11 or P14 evidence.

The decision resolves the PI-06 owner/product entry gate. It does not provision authentik, Cloudflare resources, secrets, users or a production identity environment and does not mark PI-06 implementation complete.

### 4.3 External and owner-gated integrations

The following are not ordinary autonomous UI repair tasks:

- PI-06 implementation must follow the accepted identity/session decision and remain a separate reviewed package;
- email/webhook/push delivery requires the PI-05 provider and destination policy decision;
- runtime credential injection requires PI-07 and a security-reviewed secret backend;
- approved private Freqtrade dry-run submission requires PI-08 after PI-07;
- real Cloudflare production-like staging requires intentional owner provisioning under P11;
- live-small remains P14 and requires a separate explicit authorization package.

### 4.4 Deployment-owned observability

Repository-side PI-04 contracts are complete, but a real Loki/Tempo/Prometheus-compatible target environment, retention policy, dashboards and credentials are deployment-owned. UI and API mode must report `UNAVAILABLE` when these sources are not configured; they must not fabricate successful empty results.

## 5. Completed Bot Operations task record

Completed task ID:

`FTAI-20260726-portal-bot-operations-completion`

### Goal

Turn the bot fleet and Bot Detail routes into the primary tenant-scoped operational workflow by composing existing canonical APIs and exposing existing immutable-revision and desired-state mutations safely.

### Delivered acceptance

1. Bot fleet enrichment from existing canonical read models without N+1 unbounded browser calls.
2. Bot-scoped detail sections for configuration, runtime state, positions, orders, trades, valuation, risk, observability and audit evidence.
3. Immutable-revision form using `POST /v1/bots/{bot_id}/revisions`.
4. Start/pause/stop desired-state controls using `POST /v1/bots/{bot_id}/desired-state`.
5. Permission-denied, conflict, stale, partial, unavailable, empty and mutation-pending states.
6. Confirmation and idempotency behavior for lifecycle changes.
7. TypeScript, lint, production build, Chromium E2E, AI Platform, security and repository CI validation on the final implementation head.
8. Documentation updates to `UI_DELIVERY_STATUS.md`, the program record and this plan.

### Preserved boundaries

- browser clients communicate only with portal/BFF routes and receive no private runtime endpoint or credential;
- every bot-scoped row is tenant and bot attributed;
- stale, partial, mismatched or unavailable evidence remains visibly degraded and is never represented as current;
- revision mutation creates a new immutable revision and cannot silently edit the prior revision;
- desired-state mutation is capability-gated and produces attributable audit evidence;
- lifecycle controls do not call exchange order endpoints and do not implement PI-08;
- no live-capital state is introduced;
- frozen thresholds, Phase 6 evidence and protected holdout policy remain unchanged.

## 6. Dependency-ordered continuation after the PI-06 decision

Unless live repository evidence changes the order:

1. declare and implement the separate PI-06 Product Identity and Session Lifecycle package from `PI06_IDENTITY_AND_SESSION_DECISION.md`;
2. implement PI-05 one external channel at a time after provider and privacy decisions;
3. declare PI-07 only after the secret backend, rotation policy and security review are resolved;
4. implement PI-08 only after PI-07, keeping execution private, risk-gated, audited and dry-run-only;
5. resume P11 whenever the owner intentionally starts real external staging and run all five protected ingress probes;
6. keep P13 deferred until measured bottleneck/SLO evidence exists;
7. keep P14 blocked until separately authorized.

Liquid20 and other read-only feature integrations may proceed in parallel only with disjoint paths and explicit task ownership. They must not silently change the core identity, execution, credential, P11 or live-capital gates.

## 7. Documentation repair rules

Every completion PR must update all status-bearing files it owns in the same reviewed package or in a bounded immediate closure package.

At minimum, agents must check:

- `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`;
- `docs/ai_platform/portal/DELIVERY_ROADMAP.md` when a P-stage changes;
- `docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md` when a PI status changes;
- `docs/ai_platform/portal/UI_DELIVERY_STATUS.md` when a product surface changes;
- this file when the recommended next action changes;
- the active task checkpoint and exact merge/CI evidence.

Do not leave a merged PR described as `draft`, `active` or merely `planned`. Do not mark target-environment connectivity complete from repository-only tests.

## 8. Stop conditions

Stop and record a blocker instead of improvising when:

- required owner/provider/IdP/secret-backend policy is absent;
- an active PR owns the same paths;
- the proposed change exposes IdP, Freqtrade, exchange or observability credentials to the browser;
- the work would enable real capital or withdrawals;
- the work would weaken deterministic risk, audit, tenant isolation or safety tests;
- evidence would be mislabeled as real P11 acceptance;
- a scale/service extraction is proposed without measured need.

## 9. Current next action

Declare a separate `FTAI-YYYYMMDD-portal-pi06-product-identity-lifecycle` implementation task after a fresh `develop` and path-ownership preflight. Implement versioned identity/session/membership contracts, OIDC Authorization Code + PKCE through the BFF, opaque server-side sessions, membership-derived tenant context, CSRF, MFA/step-up enforcement, logout/revocation/back-channel logout and deterministic denied/expired/revoked/cross-tenant/recovery E2E. Keep authentik/Cloudflare target provisioning, secrets and real P11 acceptance in separately controlled deployment evidence, and do not start PI-07, PI-08 or live capital.
