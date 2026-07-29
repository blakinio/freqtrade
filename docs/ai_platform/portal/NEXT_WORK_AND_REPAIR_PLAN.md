# AI Trading Portal — Next Work and Repair Plan

## 1. Purpose

This document is the durable continuation route after the bounded P0-P12 portal foundation and the repository-side bot-management sequence.

Stage completion, repository product closure and real target acceptance are different claims. Use `POST_P12_INTEGRATION_BACKLOG.md` for PI package contracts and `UI_DELIVERY_STATUS.md` for truthful surface status.

## 2. Source-of-truth order

Before starting work, verify:

1. current `develop`, open PRs, active branches and required CI;
2. `AGENTS.md` and `docs/agents/CONTEXT_HANDOFF.md`;
3. `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`;
4. this plan;
5. `DELIVERY_ROADMAP.md`, `POST_P12_INTEGRATION_BACKLOG.md` and task-specific architecture;
6. the active dated task and its `## Context checkpoint`.

Merged repository evidence overrides stale status sentences. Chat history and private UI captures are not durable state.

## 3. Verified program snapshot

Snapshot date: `2026-07-29`.

### Roadmap stages

- P0-P10: `done` for their declared bounded acceptance.
- P11: `blocked`; real Cloudflare, protected GitHub staging and five-probe external acceptance are unproven.
- P12: `done` in simulation-first mode; it does not replace P11.
- P13: `deferred` until measured bottleneck or unmet-SLO evidence exists.
- P14: `blocked`; no live-capital authorization exists.

### Post-P12 integrations

- PI-01 Private Runtime Read and Reconciliation: `done`, PR #234.
- PI-02 Authoritative Valuation and Unrealized PNL: `done`, PR #267.
- PI-03 Canonical Inference and Drift Telemetry: `done`, PR #239 and closure PR #260.
- PI-04 Centralized Runtime Observability: repository contracts `done`, PR #261; real backend connectivity remains deployment-owned.
- PI-05 External Notification Delivery: `planned`; provider/channel, destination ownership and privacy policy are unresolved.
- PI-06 Product Identity and Session Lifecycle: repository backend, BFF/browser integration and Authentik/Synology deployment package are complete; real target provisioning, MFA, recovery and restore acceptance remain owner-managed.
- PI-07 Runtime Credential Broker and Rotation: repository software and deployment contracts `done`, PR #666, merge `436b5350e54a33cbf070738a2328b142ffcd5174`; real Vault target acceptance remains owner-managed.
- PI-08 Private Dry-Run Approved Execution Submission: `done`, PR #669, merge `530f61caf9d5d4644068a93baa0b7a09298f24c6`; closure PR #670, merge `bc5493435c3b895e65adcea9f84920b36da33b2e`.

PI-08 is private, risk-gated, credential-brokered, idempotent, dry-run-only and reconciliation-dependent. Runtime acknowledgement is not execution proof.

### Bot-management packages

- BM-00 through BM-06: complete for contracts, catalog, builder, command persistence, signals, grid and exchange-product scope.
- BMW-01 through BMW-03: complete for browser creation, operations and safe signal/grid/exchange convergence.
- BM-07 Position/Order Command Activation: `done`, PR #672, merge `ef0550744104f4c82ef3f106181f14442f9b82af`.
- BM-08 Dashboard Read Model Completion: `done`, PR #651, merge `8cabed2dd116da3e5ac2156650d0b69803667fa6`.
- BM-09 Bot-Management E2E Closure: `done`, PR #675, merge `d7ae949cb91d44e260ca7c32e193d69238fad120`.

Repository-side BM-00 through BM-09 and BMW delivery is closed. BM-09 passed exact-head AI Platform, Portal Web, Portal Universal E2E, Freqtrade and workflow-security gates while retaining explicit repository-only acceptance semantics.

## 4. Completed private execution path

### PI-07 credential boundary

The single approved credential path uses Vault-backed tenant/runtime-scoped leases. Credentials remain opaque, withdrawal-disabled and absent from browser, logs, public evidence and repository state. Real Vault initialization, unseal, certificates, enrollment and restore remain target evidence.

### PI-08 submission and reconciliation

Approved intents bind exact tenant, bot, config revision, runtime revision, correlation and idempotency identity before private transport. Degraded health, kill switch, stale binding or unavailable credentials fail closed. Accepted transport responses remain pending until authoritative reconciliation.

### BM-07 command activation

Close, partial-close, close-all, take-profit and cancel operations reserve durable pending-reconciliation evidence before private I/O. Exact replay does not repeat mutations. DCA, grid and exposure-increasing replacement reuse PI-08. Unsupported price-changing replacement remains rejected.

No browser can address Freqtrade directly and no production/live path was introduced.

## 5. Completed product closure

BM-08 provides the server-owned tenant-scoped dashboard read model with explicit current, attention, degraded, stale, partial, unavailable and not-applicable evidence states.

BM-09 adds:

- one versioned repository scenario matrix covering every required family exactly once;
- validation that all referenced evidence paths exist;
- critical Chromium traversal of dashboard, fleet, bot detail, exchanges, signals and grid;
- browser request evidence excluding private Freqtrade mutation routes and credential references;
- replay proof separating accepted persisted intent from execution proof;
- deterministic backend and browser closure in `Portal Universal E2E`.

This proves repository integration only. It is not real Authentik, Vault, Synology, Freqtrade or Cloudflare target acceptance.

## 6. Remaining owner-gated or separately declared work

The following are not ordinary repairs and must not be inferred from BM-09 completion:

1. PI-05 may start only after an owner selects one provider/channel and destination/privacy policy.
2. PI-06 real target acceptance may start only with intentional Synology access, protected secrets, DNS/TLS routing, test users, MFA devices, offline recovery material and an isolated restore target.
3. Real Vault and private Freqtrade target acceptance remain owner-managed deployment evidence.
4. P11 may resume only after explicit owner start and approved Cloudflare/protected-environment resources.
5. P13 remains measured-need-only.
6. P14 remains separately owner-approved and blocked; software completion never authorizes capital.

Any new repository package must receive a dated task, explicit owned paths, acceptance criteria and exact-head validation. Do not reopen or silently extend BM-00 through BM-09.

## 7. Documentation repair rules

Every completion PR must update all status-bearing files it owns. At minimum check:

- `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`;
- `DELIVERY_ROADMAP.md` when a P-stage changes;
- `POST_P12_INTEGRATION_BACKLOG.md` when a PI status changes;
- `UI_DELIVERY_STATUS.md` when a product surface changes;
- this file when the recommended continuation changes;
- the active task checkpoint and exact merge/CI evidence.

Do not leave merged work described as draft, active or planned. Do not mark target connectivity complete from deterministic repository tests.

## 8. Stop conditions

Stop and record a blocker instead of improvising when:

- required owner/provider/IdP/secret-backend policy is absent;
- an active PR owns the same paths;
- a change would expose IdP, Freqtrade, exchange or observability credentials to the browser;
- work would enable real capital or withdrawals;
- work would weaken deterministic risk, audit, tenant isolation or safety tests;
- fixture evidence would be mislabeled as real target acceptance;
- scale or extraction is proposed without measured need.

## 9. Current next action

Keep the repository-side BM sequence closed. Start no additional package until a separately governed owner decision supplies PI-05 provider policy, PI-06 target-acceptance resources or P11 staging prerequisites. Keep P14 blocked.
