# AI Trading Portal — Next Work and Repair Plan

## 1. Purpose

This document is the durable continuation route for agents deciding what to implement or repair after the bounded P0-P12 portal foundation.

Stage completion, product completeness and external integration readiness are different claims. A roadmap stage marked `done` means its declared bounded acceptance passed; it does not imply every target UI capability, private provider, runtime command or production-like environment is complete.

Use this document to select the next bounded task. Use `POST_P12_INTEGRATION_BACKLOG.md` for detailed PI package contracts and `UI_DELIVERY_STATUS.md` for truthful per-surface delivery status.

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
- PI-06 Product Identity and Session Lifecycle: `active`; the accepted architecture, repository backend and same-origin BFF/browser-session integration are complete. Real Authentik/Synology provisioning, MFA enrollment, recovery, backup/restore and target-environment acceptance remain.
- PI-07 Runtime Credential Broker and Rotation: `planned`; requires a selected secret backend and security review.
- PI-08 Private Dry-Run Approved Execution Submission: `planned`; depends on PI-07 and must remain dry-run-only.

The concrete `FreqtradeExecutionAdapter.submit_approved_intent` path remains fail-closed with `ORDER_SUBMISSION_NOT_IMPLEMENTED`. Deterministic simulator execution is not evidence of private Freqtrade order submission.

## 4. Completed product and PI-06 subpackages

### 4.1 Bot Operations convergence — complete

Task `FTAI-20260726-portal-bot-operations-completion` and PR #320 complete the software-addressable bot operations workflow by composing canonical bot, runtime-evidence, valuation, risk, observability and audit APIs.

Delivered behavior includes:

- bounded bot fleet enrichment and filters;
- bot-scoped positions, orders, trades, valuations, risk decisions, runtime logs and audit evidence;
- immutable configuration revisions;
- start/pause/stop desired-state controls with confirmation, permission, stale-state, conflict and idempotency behavior;
- explicit separation of lifecycle commands from execution authority.

The package does not implement credential brokering, PI-08 order submission, external notification delivery, P11 infrastructure or live capital.

### 4.2 PI-06 identity and session decision — complete

Task `FTAI-20260726-portal-pi06-identity-decision` records the accepted architecture:

- Authentik is the product IdP and owns primary authentication, authenticator enrollment, MFA challenge, IdP session and recovery flows;
- the portal database owns principals, tenants, memberships, roles, capabilities and local session revocation;
- immutable OIDC `iss` plus `sub` maps external identity to the portal principal;
- the BFF uses Authorization Code plus PKCE and opaque server-side sessions;
- privileged mutations require MFA, with five-minute step-up for declared high-impact administration;
- membership and role changes invalidate affected sessions synchronously;
- Cloudflare Access remains supplemental privileged ingress and never replaces application authorization;
- Synology Docker Compose is an accepted bounded target but remains a single-host failure domain and is not P11 or P14 evidence.

### 4.3 PI-06 repository identity backend — complete

Task `FTAI-20260726-portal-pi06-product-identity-lifecycle`, PR #341, squash merge `41834d18f3a05b0dfa44dc5af9b97942e685d2a1`, delivered:

- OIDC discovery, Authorization Code plus PKCE, JWKS signature, issuer, audience, expiry and nonce validation;
- one-time login state and encrypted PKCE verifier material;
- immutable external principal mapping;
- portal-owned memberships, roles, validity and membership versions;
- opaque sessions with keyed hashes only in storage;
- secure host-only session cookies and server-verified CSRF;
- membership-derived tenant/capability context;
- MFA, step-up, logout, logout-all, synchronous revocation and back-channel logout;
- migrations, deterministic configuration and security tests.

Exact final backend head `c258567cabd1c9ddf3d90c63f36319be99463978` passed AI Platform CI #1415, Freqtrade CI #1713 and GitHub Actions Security Analysis #1580.

### 4.4 PI-06 same-origin BFF/browser sessions — complete

Task `FTAI-20260726-portal-pi06-bff-browser-session-integration`, PR #361, squash merge `4f76eecadcb8dda964a8d247327db9dc6ef1c931`, delivered:

- same-origin login, callback, session, logout and logout-all routes;
- safe HTTPS authorization redirects and relative application returns;
- forwarding of opaque session/CSRF cookies without browser-readable IdP tokens;
- optimistic Proxy denial plus Route Handler defense in depth;
- double-submit CSRF for existing browser mutations;
- tenant/MFA session display and logout controls;
- deterministic fixture states for anonymous, expired, revoked, MFA-missing, stale-step-up and cross-tenant denial;
- browser security regression coverage while preserving the existing product suite.

Exact final implementation head `ec1970a9272bec241a1bab3c447ebd36f53afa58` passed Portal Web CI #287, Portal Universal E2E #292, AI Platform CI #1521, Freqtrade CI #1837 and GitHub Actions Security Analysis #1702. Portal Web CI passed typecheck, lint, production build and all 37 Chromium tests.

This is repository and deterministic fixture evidence. It does not prove a real Authentik instance, MFA enrollment, recovery, Synology deployment or Cloudflare ingress.

## 5. External and owner-gated boundaries

The following are not ordinary UI repairs:

- real Authentik/Synology target provisioning and identity acceptance require a separate deployment package;
- email/webhook/push delivery requires the PI-05 provider and destination policy decision;
- runtime credential injection requires PI-07 and a security-reviewed secret backend;
- approved private Freqtrade dry-run submission requires PI-08 after PI-07;
- real Cloudflare production-like staging requires intentional owner provisioning under P11;
- live-small remains P14 and requires separate explicit authorization.

Repository-side PI-04 contracts are complete, but a real Loki/Tempo/Prometheus-compatible target environment, retention policy, dashboards and credentials are deployment-owned. UI and API mode must report `UNAVAILABLE` when these sources are not configured.

## 6. Dependency-ordered continuation

Unless live repository evidence changes the order:

1. declare a separate PI-06 Authentik/Synology deployment package with pinned images, runtime-injected secret placeholders, restricted bootstrap, health checks, migrations, backup/restore and recovery runbooks;
2. on owner-managed target resources, prove real login, MFA enrollment/challenge, session cookies, logout, logout-all, membership revocation, recovery and restore without committing credentials;
3. implement PI-05 one external channel at a time only after provider and privacy decisions;
4. declare PI-07 only after the secret backend, rotation policy and security review are resolved;
5. implement PI-08 only after PI-07, keeping execution private, risk-gated, audited and dry-run-only;
6. resume P11 whenever the owner intentionally starts real external staging and run all five protected ingress probes;
7. keep P13 deferred until measured bottleneck/SLO evidence exists;
8. keep P14 blocked until separately authorized.

Liquid20 and other read-only feature integrations may proceed in parallel only with disjoint paths and explicit task ownership. They must not silently change identity, execution, credential, P11 or live-capital gates.

## 7. Deployment package acceptance boundaries

The next Authentik/Synology package may autonomously add repository deployment definitions and deterministic validators, but it must preserve these boundaries:

- pin Authentik, PostgreSQL and supporting image digests or immutable versions;
- commit no password, client secret, cookie key, encryption key, recovery code or user identity;
- use runtime-injected placeholders and fail closed when required values are absent;
- expose only intended portal/IdP ingress and keep the control plane, database and Freqtrade private;
- restrict bootstrap and document removal/disablement after first setup;
- add health checks, migration ordering, backups, restore verification and rollback;
- distinguish repository validation from owner-managed deployment evidence;
- do not combine Cloudflare P11 acceptance, PI-07, PI-08 or P14.

Stop and record a blocker rather than fabricating real acceptance when target resources, DNS, certificates, users, MFA devices or protected secrets are unavailable.

## 8. Documentation repair rules

Every completion PR must update all status-bearing files it owns in the same reviewed package or in a bounded immediate closure package.

At minimum, agents must check:

- `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`;
- `docs/ai_platform/portal/DELIVERY_ROADMAP.md` when a P-stage changes;
- `docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md` when a PI status or dependency changes;
- `docs/ai_platform/portal/UI_DELIVERY_STATUS.md` when a product surface changes;
- this file when the recommended next action changes;
- the active task checkpoint and exact merge/CI evidence.

Do not leave a merged PR described as draft, active or planned. Do not mark target-environment connectivity complete from repository-only tests.

## 9. Stop conditions

Stop and record a blocker instead of improvising when:

- required owner/provider/IdP/secret-backend policy is absent;
- an active PR owns the same paths;
- the proposed change exposes IdP, Freqtrade, exchange or observability credentials to the browser;
- the work would enable real capital or withdrawals;
- the work would weaken deterministic risk, audit, tenant isolation or safety tests;
- evidence would be mislabeled as real Authentik, recovery or P11 acceptance;
- a scale/service extraction is proposed without measured need.

## 10. Current next action

Declare `FTAI-YYYYMMDD-portal-pi06-authentik-synology-deployment` after a fresh `develop`, open-PR and path-ownership preflight. Add a bounded, secret-free deployment package with pinned Authentik/PostgreSQL definitions, private networking, runtime-injected configuration, restricted bootstrap, health checks, migrations, backup/restore, recovery and rollback runbooks, and deterministic configuration tests. Record real login, MFA, revocation, recovery and restore as blocked until owner-managed Synology resources are available. Keep Cloudflare P11 acceptance, PI-07, PI-08 and live capital separate.
