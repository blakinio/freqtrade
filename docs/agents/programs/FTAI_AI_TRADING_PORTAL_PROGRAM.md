# FTAI AI Trading Portal Program

## Program ID

`FTAI-PROGRAM-AI-TRADING-PORTAL`

## Status

`production-like-staging-blocked`

## Mission

Build a secure, modern and extensible portal above the existing Freqtrade AI Platform that can manage dry-run bot runtimes, model lifecycle, deterministic risk, post-trade intelligence, safe continual learning, Cloudflare-protected access and autonomous full-platform validation.

## Current program state

Repository-backed implementation has progressed through P12 simulation-first acceptance, completed software-addressable product surfaces, PI-01 through PI-04 repository integrations, bounded PI-06 identity/deployment packages, PI-07 Vault credential brokering, PI-08 private dry-run submission, BM-00 through BM-09 and BMW browser convergence.

The final repository-side bot-management closure completed in BM-09 PR #675, squash merge `d7ae949cb91d44e260ca7c32e193d69238fad120`. Exact implementation head `e0a90ccdcfb3dc0e1ac03acede92f0f8c9da70e3` passed AI Platform CI `30437195010`, Portal Web CI `30437194948`, Portal Universal E2E `30437195047`, Freqtrade CI `30437194987` and workflow security `30437194958`.

Canonical stage status remains:

- P0-P10 complete for declared bounded acceptance;
- P11 blocked until real owner-approved Cloudflare/protected GitHub staging and five-probe External E2E acceptance pass;
- P12 complete in simulation-first mode and not a substitute for P11;
- P13 deferred until measured bottleneck or unmet-SLO evidence exists;
- P14 blocked and separately owner-approved; this program does not authorize live capital.

Post-P12 status:

- PI-01, PI-02, PI-03 and PI-04 repository packages are complete;
- PI-05 remains provider/channel and privacy-policy gated;
- PI-06 repository backend, BFF/browser integration and Authentik/Synology deployment package are complete, while real target identity acceptance remains owner-managed;
- PI-07 repository credential broker is complete, while real Vault target acceptance remains owner-managed;
- PI-08 repository private dry-run submission is complete, PR #669, merge `530f61caf9d5d4644068a93baa0b7a09298f24c6`;
- BM-07 private position/order command activation is complete, PR #672, merge `ef0550744104f4c82ef3f106181f14442f9b82af`;
- BM-09 closes the repository-side bot-management sequence without changing P11 or P14.

Repository or fixture evidence does not prove real Authentik, Vault, Synology, Freqtrade or Cloudflare target acceptance.

## Source of truth

In order:

1. current repository, PR and exact-head CI state;
2. `AGENTS.md`;
3. existing AI Platform lifecycle and evidence records;
4. portal architecture/status documents;
5. the active dated task and its context checkpoint.

Chat history and private UI captures are not durable program state.

## Required reads

- `AGENTS.md`
- `docs/agents/CONTEXT_HANDOFF.md`
- `docs/ai_platform/ARCHITECTURE.md`
- `docs/ai_platform/ROADMAP.md`
- `docs/ai_platform/portal/README.md`
- `docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md`
- `docs/ai_platform/portal/SECURITY_ARCHITECTURE.md`
- `docs/ai_platform/portal/DELIVERY_ROADMAP.md`
- `docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md`
- `docs/ai_platform/portal/NEXT_WORK_AND_REPAIR_PLAN.md`
- `docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md`

Task-specific agents read additional documents only when relevant.

## Program invariants

- Freqtrade is an internal execution engine, not a public portal backend.
- Browser traffic never talks directly to Freqtrade, exchanges or a secret store.
- Portal execution reaches Freqtrade only through a controlled private adapter boundary.
- AI predictions and deterministic risk approval are not unrestricted execution authority.
- Every execution intent remains subject to deterministic risk and immutable attribution.
- Exchange credentials remain opaque, tenant-scoped, withdrawal-disabled and uncommitted.
- Research workers cannot access runtime credentials.
- Models, configurations, strategies and risk policies used for decisions are immutable and attributable.
- Post-trade analysis may create insights, experiments and candidates, not immediate production mutation.
- Autonomous repair creates regression evidence, branches and PRs; it does not patch production.
- Live capital requires a separate explicitly reviewed work package.
- Repository or simulated P11 evidence cannot be represented as real Cloudflare production-like staging acceptance.
- Cloudflare Access supplements product authorization and never replaces portal tenant membership, capabilities or local session revocation.
- Browser-readable storage receives no IdP access, ID or refresh token.
- Repository deployment validation cannot be represented as real Synology, Authentik, MFA, recovery, Vault, private Freqtrade or restore acceptance.
- Runtime acknowledgement is not authoritative execution proof; reconciliation remains required.

## Protected existing AI boundaries

This program cannot change:

- frozen `entry_prediction_threshold = 0.006`;
- frozen `exit_prediction_threshold = -0.009`;
- protected final holdout v2 `20260801-20260930` or its authorization date;
- completed Phase 6 candidates, policy and evidence;
- authoritative Phase 6 `selected_model = null`;
- historical PyTorch/RL evidence status.

Any future work affecting these boundaries requires a separate research package governed by the AI Platform lifecycle.

## Program architecture

Six planes:

1. Portal / UX Plane
2. Control Plane
3. Execution Plane
4. AI / Research Plane
5. Data Plane
6. Quality & Autonomous Validation Plane

Cross-cutting controls are Security, Risk and Observability.

## Repository completion evidence

### Identity

PI-06 delivered the Authentik-compatible identity/session backend, same-origin BFF/browser session handling and a secret-free Synology deployment package. Opaque sessions, CSRF, membership-derived tenant/capability context, MFA, step-up, logout and revocation are repository-tested. Real users, devices, recovery and restore remain target evidence.

### Credential and private execution

PI-07 provides the single approved Vault-backed credential boundary. PI-08 binds approved intents to exact tenant, bot, configuration and runtime revisions, reserves idempotent attempts before private transport, independently verifies dry-run mode and treats ambiguous/accepted transport responses as unproven until reconciliation.

BM-07 maps bounded position/order commands to private dry-run runtime operations. It reserves pending-reconciliation evidence before I/O, prevents repeat mutation on exact replay and routes exposure-increasing DCA/grid/replacement through PI-08.

### Product and E2E

BM-08 provides the authoritative tenant-scoped dashboard read model with explicit source states.

BM-09 provides:

- one versioned matrix covering each required scenario family exactly once;
- validation that all evidence references exist;
- critical Chromium traversal across dashboard, fleet, bot detail, exchange, signal and grid surfaces;
- browser request evidence excluding private Freqtrade mutation and credential paths;
- replay evidence separating persisted intent from execution proof;
- exact-head backend, browser, full CI and security acceptance.

This closes repository-side BM-00 through BM-09 and BMW delivery only.

## Parallelization policy

Shared contract changes are serialized through a dedicated contract-change task. New work must inspect current `develop`, open PRs and active task ownership before editing shared paths.

Every new package requires a dated task, branch, exact owned paths, authoritative source definition, fail-closed states and acceptance evidence. Completed BM packages must not be silently reopened or extended.

P13 scale or service extraction remains deferred without measured need.

## Quality policy

Every implementation adds tests at its layer. Full-platform acceptance includes, as applicable:

- unit, contract and integration tests;
- security E2E;
- Playwright browser E2E;
- deterministic exchange simulator;
- AI learning-loop E2E;
- visual and responsive acceptance;
- chaos and recovery scenarios;
- bounded autonomous diagnosis and repair.

Simulation, local and CI evidence must remain labeled as such. Real production-like staging acceptance requires the real protected external ingress path.

## Security posture

Target ingress:

```text
Internet -> Cloudflare -> Tunnel -> Portal
```

Privileged surfaces add Zero Trust/Access policy. Freqtrade remains private.

The current P11 blocker is external: owner-approved Cloudflare Tunnel, DNS, Access, WAF, rate-limit and direct-origin-denial state plus protected GitHub staging variables/secrets must be provisioned or confirmed and the real External E2E workflow must pass.

## Product surface

Canonical navigation includes dashboard, performance, positions, terminal, bot management, AI intelligence, operations, exchanges, profile/security, notifications and administration.

Protected browser paths use the same-origin PI-06 boundary with opaque cookies, CSRF and backend-authoritative tenant/capability enforcement. Bot management consumes canonical server models and never creates direct browser-to-Freqtrade authority.

Third-party private captures are inspiration or evidence only and must not be copied with personal data or proprietary assets.

## Completion definition

The first major production-like staging milestone requires a real protected path that can:

1. authenticate a test user;
2. create a tenant-scoped dry-run AI bot;
3. provision an isolated private Freqtrade runtime;
4. execute a deterministic simulated trade through risk gates;
5. reconcile PNL and execution evidence;
6. produce post-trade analysis and insight;
7. create a bounded learning experiment/candidate without changing the active model;
8. pass critical browser, security and AI E2E;
9. generate an evidence-based repair PR for a seeded defect;
10. prove no public Freqtrade exposure and no live-capital authorization.

Repository-side software covers the bounded implementation and deterministic quality layer, but the milestone remains incomplete until real P11 protected external ingress acceptance passes.

## Next actions by authorization lane

- PI-06 target acceptance: only when the owner supplies Synology access, protected secrets, DNS/TLS routing, test users, MFA devices, offline recovery material and an isolated restore target.
- PI-05 delivery: only after the owner selects a provider/channel and destination/privacy policy.
- P11 external staging: only when the owner intentionally starts the infrastructure phase and supplies approved Cloudflare/protected-environment resources.
- P13: only from measured need.
- P14: remain blocked until separate explicit capital authorization and all prerequisites.

There is no remaining autonomous BM package after BM-09. Do not start another package by extending the completed sequence implicitly.
