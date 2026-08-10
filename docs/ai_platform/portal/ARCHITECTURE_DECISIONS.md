# AI Trading Portal — Architecture Decisions

This document records program-level decisions that downstream agents should not silently redefine.

A change to an accepted decision requires a bounded architecture/contract change with migration impact documented.

## ADR-001 — Freqtrade is an internal execution engine

Status: `accepted`

Decision:

- Portal-facing APIs are owned by the portal control plane.
- Freqtrade REST/WebSocket details are hidden behind `ExecutionAdapter`.
- Freqtrade is private-network-only.

Reason:

Decouples product/API evolution from execution-engine details and reduces public attack surface.

## ADR-002 — Modular monolith control plane first

Status: `accepted`

Decision:

Start with one FastAPI control-plane deployment with strict internal modules rather than independent microservices for every domain.

Reason:

Reduces operational complexity while preserving future extraction through explicit contracts/events.

Revisit when:

- independent scaling is measured;
- security isolation requires process boundaries;
- release cadence or ownership requires independent deployment.

## ADR-003 — Tenant boundary from day one

Status: `accepted`

Decision:

All tenant-owned portal entities carry explicit tenant identity and are authorized server-side even for an initial single-user deployment.

Reason:

Retrofitting tenancy later is high risk, especially around exchange credentials and trading resources.

## ADR-004 — One BotInstance maps to one isolated Freqtrade runtime initially

Status: `accepted`

Decision:

Use one isolated runtime per portal bot as the baseline isolation unit.

Reason:

Clear strategy/model/config attribution, failure containment, restart independence and secret scoping.

Revisit when:

Measured resource cost justifies safe consolidation without losing attribution/isolation.

## ADR-005 — Deterministic risk gate between intent and execution

Status: `accepted`

Decision:

AI/manual strategies create trade intent. A versioned deterministic risk policy must approve/reject it before execution.

Reason:

Model confidence is not capital authority.

## ADR-006 — Immutable model/config/risk identities

Status: `accepted`

Decision:

Every production/dry-run decision is attributable to immutable strategy, model, feature schema, bot config and risk policy versions.

Reason:

Required for reproducibility, rollback, trade analysis and audit.

## ADR-007 — Training is separate from promotion

Status: `accepted`

Decision:

Training and post-trade learning may create candidates automatically. Active model assignment changes only through lifecycle/promotion policy.

Reason:

Prevents a self-learning loop from silently modifying production behavior.

## ADR-008 — Decision Black Box is first-class data

Status: `accepted`

Decision:

Record decision-time evidence separately from later outcomes for AI-assisted trades.

Reason:

Enables reliable attribution and avoids hindsight contamination in post-trade diagnosis.

## ADR-009 — Event-driven integration uses versioned events plus durable state

Status: `accepted`

Decision:

Use versioned domain events, transactional outbox and idempotent consumers. Event transport is not the sole authoritative database.

Initial transport target: NATS JetStream.

Reason:

Supports real-time decoupling without confusing transient messaging with system-of-record ownership.

## ADR-010 — PostgreSQL first; object storage for large immutable artifacts

Status: `accepted`

Decision:

Use PostgreSQL for portal metadata/read models and S3-compatible storage for datasets, models, replay bundles and large evidence.

TimescaleDB may be added where time-series query requirements justify it.

Reason:

Avoids premature multi-database complexity while keeping large artifacts out of relational rows.

## ADR-011 — Cloudflare-protected ingress with hidden origin

Status: `accepted`

Decision:

Public portal ingress is designed for Cloudflare edge protection and Tunnel-based origin connectivity. Privileged surfaces additionally use Zero Trust/Access policies.

Reason:

Reduces direct origin exposure and centralizes external ingress controls.

Application RBAC, tenant isolation and private internal networking remain mandatory.

## ADR-012 — Autonomous repair is PR-based, not production self-patching

Status: `accepted`

Decision:

Agents may diagnose, reproduce, add regression tests, patch owned code on isolated branches and create PRs. They do not modify production directly or bypass CI.

Reason:

Preserves evidence, reviewability and rollback.

## ADR-013 — Deterministic exchange simulator is required for full E2E

Status: `accepted`

Decision:

Critical full-platform E2E uses a deterministic market/exchange simulator and dry-run/test runtimes by default.

Reason:

Real-market nondeterminism and real capital are unsuitable as the primary acceptance mechanism.

## ADR-014 — Production-like E2E traverses security boundaries

Status: `accepted`

Decision:

Staging E2E exercises the externally protected Cloudflare path. There is no hidden application endpoint that bypasses authentication/security solely for tests.

Reason:

A security boundary not exercised by acceptance tests can fail independently of the product logic.

## ADR-015 — No portal work retroactively alters research evidence

Status: `accepted`

Decision:

Portal implementation cannot reopen completed Phase 6, alter frozen Phase 5 parameters, iteratively consume protected holdout data, or promote experimental PyTorch/RL evidence.

Reason:

Product implementation and research validity are separate governance concerns.

## ADR-016 — Remaining integrations use separate PI packages

Status: `accepted`

Decision:

- Remaining authoritative-source, private-runtime, identity, observability and provider integrations after the bounded P0-P12 foundation are routed through stable `PI-*` packages in `POST_P12_INTEGRATION_BACKLOG.md`.
- PI packages do not renumber or replace P0-P14.
- Private runtime reads/reconciliation, runtime credential brokering and approved-intent submission are separate packages with separate entry and security gates.
- A `planned` PI package is not active until a dated task, branch, owned paths and acceptance evidence are declared.
- P11, P13 and P14 retain their existing blocked/deferred/owner-gated semantics.

Reason:

The remaining work crosses several architectural planes and has materially different security and capital risk. A single catch-all implementation task would obscure authoritative data ownership, create unsafe dependency shortcuts and make completion claims ambiguous.

Consequence:

The recommended first software package is read-only `PI-01 Private Runtime Read and Reconciliation`. Higher-risk credential and dry-run submission work follows only after its explicit dependencies pass. No PI package authorizes live capital.

## ADR-017 — Liquid20 portal evidence is read-only and not execution authority

Status: `accepted`

Decision:

- Liquid20 run evidence remains authoritative and is mounted into the portal read-only.
- The server-side read-model exposes only bounded versioned event, summary and health contracts through same-origin BFF routes.
- Bybit and Binance source identity and feed semantics remain explicit; cross-exchange events are not silently deduplicated or presented as one complete volume feed.
- Portal health must state `research_preview: true` and `trading_authorized: false`.
- The Liquidations page cannot create a signal, trade intent, order, model promotion or capital authorization.
- Any Wick Hunter-inspired strategy, AI model, deterministic replay, dry-run adapter, DCA, leverage or live-small work is a separate prospectively declared lifecycle package.

Reason:

A working market-data page proves data presentation, not data acceptance, synchronization validity, strategy edge, risk acceptance or safe execution. Keeping the observation path separate prevents portal integration from bypassing research and capital-governance gates.

Consequence:

Future agents must use `LIQUIDATIONS_AND_AI_BOT_ARCHITECTURE.md`, preserve immutable evidence and no-lookahead rules, and follow the standard model/strategy/risk/execution lifecycle before making any trading claim.

## ADR-018 — Production portal hostname is `quant.molehill.cloud`

Status: `accepted`

Decision:

- The canonical public production hostname for the AI Trading Portal is `https://quant.molehill.cloud`.
- The hostname belongs to the owner-controlled `molehill.cloud` zone and is intended to use the Cloudflare-protected ingress and hidden-origin model defined by ADR-011.
- Local, test and staging addresses remain separate and must not be presented as the production origin.
- DNS, Cloudflare Tunnel routing, TLS, OIDC redirect URIs, cookie scope and deployment configuration must use this hostname consistently when the production ingress package is activated.
- This decision reserves the production hostname; it does not by itself claim that DNS, Tunnel, TLS, OIDC or the production deployment is already active.

Reason:

A single canonical production origin prevents conflicting hostnames across DNS, identity callbacks, browser sessions, security policies, deployment configuration and operational evidence.

Consequence:

Future production-ingress, identity and deployment work must treat `https://quant.molehill.cloud` as the target external origin or explicitly replace this ADR through a bounded architecture change.

## ADR-019 — Architecture authority uses a registry and exact implementation evidence

Status: `accepted`

Decision:

- The repository-root `ARCHITECTURE_REGISTRY.yaml` is the canonical index of architecture documents, domains, authority and review state.
- This accepted decision log remains binding until a decision is explicitly superseded through a bounded architecture change.
- Exact current code, configuration, migrations, tests, workflow results and deployed-target evidence determine implementation state.
- A target-state or domain architecture document may define approved direction, but it must not be reported as implemented solely because it is accepted or documented.
- Historical baseline documents preserve context and constraints from their original scope; they do not override accepted decisions or exact current-state evidence.
- Material architecture changes update the registry and this decision log in the same change set, including migration impact and affected domains.

Reason:

The platform has evolved beyond its original research MVP and now contains several architecture documents with different scopes. Without explicit authority and implementation-state rules, valid historical or target-state documents can be mistaken for current platform truth.

Consequence:

Architecture reviews and autonomous agents must begin with `ARCHITECTURE_REGISTRY.yaml`, follow its authority order, and cite exact evidence for every current-state claim. Documentation alone never creates runtime, production, credential, trading or live-capital authority.

## ADR-020 — Secure dry-run runtime control uses RuntimeGeneration, Runtime Supervisor and per-runtime Gateway

Status: `accepted`

Accepted by owner: `2026-08-08`

Decision:

The canonical next execution-plane architecture is **Option C** from Issue #1358:

```text
browser -> portal-web -> portal-api -> PostgreSQL
                                |
                                v
                           portal-worker
                          /             \
          generation-bound Gateway      narrow lifecycle request
                    |                           |
                    v                           v
              Freqtrade API              Runtime Supervisor
                    |                           |
                    v                           v
          isolated Freqtrade runtime       container engine
```

The following invariants are binding:

1. **`RuntimeGeneration` is the execution identity.** Every runtime read, command, reconciliation record and execution claim binds to an immutable generation containing exact tenant, bot, config revision, image/artifact digests, strategy/model/risk identities, exchange mode/revision, isolation-profile version and gateway-contract version.
2. **Bot config authoring is separate from rollout.** Latest/authored revision, desired revision and observed active runtime generation/revision are distinct. A `DRAFT` revision is never executable merely because it was saved. Running-bot changes require an explicit apply/restart-with-revision mutation.
3. **Runtime replacement is initially stop-then-replace.** Blue/green concurrent execution is deferred until a separate measured need and safety design exist.
4. **Runtime Supervisor is the only Portal component with container-engine authority.** Portal API, ordinary workers, web, AI/training workers and exchange-verification workers do not receive raw Docker/container-engine access. The supervisor accepts only validated immutable generation specifications and rejects arbitrary image, mount, port, capability, environment and command passthrough.
5. **Per-runtime Gateway is the only Portal-to-Freqtrade application boundary.** It exposes narrowly reviewed read/valuation/reduce-only/submission capabilities and is not a general Freqtrade reverse proxy. No browser/public ingress reaches it.
6. **Same-host Portal-to-Gateway transport defaults to Unix domain sockets with OS ACLs and generation-bound socket identity.** A future multi-host variant must use authenticated TLS/mTLS workload identity. Plain routable HTTP is not an accepted trust boundary.
7. **Freqtrade API credentials are generation-local.** They exist only between the Gateway and its Freqtrade runtime and rotate on replacement; Portal workers do not receive them.
8. **Dry-run does not require private exchange trading credentials.** Exchange connectivity distinguishes `PUBLIC_DATA` from `PRIVATE_TRADING`. Current dry-run runtimes use public-data venue metadata/capabilities without exchange key/secret material. Private trading credentials remain separately governed and do not become activatable through this ADR.
9. **Runtime storage is split by trust class.** Portal-authoritative generation/identity evidence is control-owned and never runtime-writable; immutable config/artifacts are read-only; Freqtrade trade/state data is explicit durable writable state for the generation; temporary/log/cache writes are explicit and bounded.
10. **A reviewed RuntimeIsolationProfile is mandatory.** It includes non-root/no privilege gain, `no-new-privileges`, capability minimization, read-only root, explicit writable mounts/tmpfs, CPU/memory/PID/log bounds, immutable image digest, no Docker socket, no Portal DB/Vault/NATS/Redis/unrelated-runtime reachability, and only required public market-data egress plus the local Gateway relationship.
11. **Reconciliation, not acknowledgement or event delivery, is authoritative.** PostgreSQL durable state is the recovery spine. Events may reduce latency but do not replace durable desired state, command identity or reconciliation. Ordering is generation-first, then source sequence/version when available, then durable reconciliation epoch/attempt, with source timestamps used for freshness and hashes for duplicate/conflict detection.
12. **Emergency execution uses a monotonic safety fence.** Kill-switch activation/release advances an `ExecutionSafetyEpoch`; exposure-increasing commands must carry the exact current generation and epoch, and stale epochs fail closed. Risk-reducing operations remain governed by a separately explicit reduce-only policy.
13. **Process roles split by privilege, not by premature business microservices.** The target deployable profiles are `portal-api`, ordinary `portal-worker`, `runtime-supervisor`, `exchange-verification-worker` and `training-worker`, with the minimum authority required for each. Domain ownership remains modular-monolith-first unless ADR-002 revisit criteria are met.
14. **Freqtrade remains replaceable and upstream-isolated.** This target architecture requires no upstream `freqtrade/` core modification; Freqtrade remains behind the private adapter/Gateway boundary.

### Binding refinement — RuntimeIsolationProfile + Runtime Supervisor Contract

Accepted by owner: `2026-08-08`.

`RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md` is the binding detailed refinement of ADR-020 for Portal-managed Freqtrade dry-run runtime isolation and Supervisor materialization. It does not add production, private-exchange or live-capital authority.

The refinement makes the following additional invariants explicit:

1. Every executable `RuntimeGeneration` binds one immutable `RuntimeIsolationProfile` **and** one resolved immutable `RuntimeIsolationPlan`, including their digests. A generation's security/resource envelope is never edited in place.
2. Security invariants have no fallback. Host-capability-resolved controls may select only pre-approved mechanisms that preserve the required hard bound; absence of an acceptable mechanism makes the host incompatible.
3. `RuntimeHostCapabilityReport` is generated by the Supervisor and treated as point-in-time host evidence. The Control Plane never guesses CPU/PID/cgroup/storage/log/network capability.
4. `isolation_plan_digest` represents stable canonical resolved semantics, not volatile report IDs, timestamps, host names or boot IDs. Recovery on another compatible host is allowed only when the same plan can be reproduced and attested.
5. Provisioning requires both structural/static container attestation and **effective host/kernel enforcement attestation**. Configured Compose/Docker values or `inspect` output alone are not sufficient evidence of CPU/PID/quota/network enforcement.
6. Portal-managed Freqtrade requires hard CPU, memory/swap, PID, durable-state, log and tmpfs containment. Missing effective containment fails closed rather than silently weakening the profile.
7. The Portal uses an approved hardened Freqtrade image without relying on the repository root Dockerfile's sudo/NOPASSWD convenience. The Supervisor only uses pre-present immutable image content and does not pull or build images.
8. Control-owned RuntimeGeneration/manifest evidence is not mounted writable into Freqtrade; immutable config/artifacts are read-only; durable writable state is generation-scoped and hard bounded; secret material is generation-local and separate.
9. Each generation has an isolated network relationship plus a versioned `MarketDataEgressPolicy`; a plain Docker bridge is not by itself proof of deny-by-default egress enforcement.
10. Freqtrade has no host/public port. The generation-local Gateway remains the only Portal-to-Freqtrade application boundary.
11. The Supervisor accepts lifecycle identity only, never arbitrary image/mount/command/env/network/capability/container-engine parameters, and uses a minimal read-only trusted generation view.
12. Portal-managed Freqtrade uses engine restart policy `NO`; host/daemon recovery is explicit desired-state reconciliation and may not resurrect stale generations.
13. One `(tenant_id, bot_id)` cannot have two different generations simultaneously in execution-owned active lifecycle states; conflicts fail rather than auto-stop the incumbent generation.
14. The Supervisor is lifecycle/isolation truth only. Positions, orders, trades, valuation and execution success remain Gateway/reconciliation truth.
15. WH09 evidence is a host-capability warning, not a reason to weaken Portal requirements: PR #1392 records Synology rejection of CPU CFS/NanoCPUs and diagnostic PR #1394 reports that the same target discarded a configured PID limit. Effective enforcement must therefore be verified.
16. Draft implementation PR #1388 currently contains isolation-profile identity but not `isolation_plan_digest`; it or a successor must add the plan binding before claiming conformance with this refinement.

Reason:

Directly wiring the existing P3/PI/BM components into one general worker would combine container-engine authority, private runtime control and secret-adjacent responsibilities, while leaving runtime-generation identity, writable control evidence, replacement persistence, transport consistency and kill-switch races unresolved. A bounded supervisor and per-runtime Gateway reduce blast radius, make provenance explicit, preserve one-bot/one-runtime isolation and keep Freqtrade private without prematurely decomposing the control-plane business domains.

The refinement additionally responds to real host evidence: a container runtime may accept or display requested isolation settings without the target kernel effectively enforcing them. Therefore reproducible generation identity must include the resolved isolation plan and successful provisioning must prove effective containment, not merely requested configuration.

Migration impact:

Implementation must proceed in dependency order and remain fail closed between stages:

1. separate config draft/authored, desired revision and observed runtime generation state;
2. introduce control-owned `RuntimeGeneration` persistence and trusted storage separation;
3. make an executable generation bind `RuntimeIsolationProfile` and resolved `RuntimeIsolationPlan` identities;
4. implement capability discovery, plan resolution and effective attestation for the reusable isolation profile;
5. introduce the narrow Runtime Supervisor boundary;
6. introduce the generation-bound per-runtime Gateway and generation-local Freqtrade API authentication;
7. compose PI-01 authoritative reconciliation with monotonic/generation-aware ordering;
8. converge PI-02 valuation on the same Gateway read boundary;
9. add kill-switch execution safety epoch/fencing;
10. compose PI-08 exposure-increasing submission and BM-07 private activation only after the preceding safety gates pass;
11. compose authenticated API-mode deployment/E2E and only then connect downstream AI/learning producers to authoritative runtime evidence.

Until a stage is implemented and verified, existing higher-risk operations remain unavailable/fail closed rather than falling back to direct Freqtrade access or weaker isolation.

Affected architecture/issues:

- `RUNTIME_ISOLATION_AND_SUPERVISOR_CONTRACT.md`;
- #1086, #1091, #1092, #1093, #1097, #1099, #1100, #1120, #1136;
- #1353, #1354, #1355, #1357;
- owner decision package #1358;
- current host evidence in PRs #1392 and #1394.

Consequence:

Older target-state wording that implies a generic worker directly controls Docker/Freqtrade, that every dry-run runtime receives exchange trading credentials, that runtime identity is only `(tenant_id, bot_id)`, or that requested container-engine flags alone prove isolation is superseded by ADR-020 and this refinement. Target-state documents must be interpreted through both until they are updated.

Documentation acceptance does not prove implementation. This decision grants no production deployment, protected-host mutation, exchange-credential activation, withdrawal, model-promotion or live-capital authority.

## ADR-021 — Release branches, deployment environments and bot operating modes are orthogonal

Status: `accepted`

Accepted by owner: `2026-08-10`

Issue: `#1438`

Decision:

The platform uses three independent control dimensions:

1. **Deployment environment:** `dev | staging | production`.
2. **Bot operating mode:** `SHADOW | PAPER | LIVE`.
3. **Release channel:** `candidate | stable`.

Their meanings must never be inferred from one another. In particular, `environment=production` does not imply `mode=LIVE`, and a source branch is not a deployment environment.

The source/release model is:

- `develop` remains the controlled integration branch and upstream `freqtrade/freqtrade:develop` synchronization boundary;
- `main` is the accepted target canonical release branch;
- ordinary feature/fix/audit/architecture/CI/infrastructure work integrates through short-lived branches into `develop`;
- after the physical `main` migration is complete, stable release promotion uses a dedicated reviewed `develop -> main` path;
- direct ordinary feature integration into `main` is prohibited;
- staging consumes immutable candidate artifacts and production consumes explicitly authorized immutable stable artifacts originating from exact `main` commits;
- branch advancement alone never authorizes a deployment;
- production deployment consumes exact release/artifact provenance rather than a moving branch tip;
- the preferred supply-chain pattern is build once and promote the same immutable digest from staging acceptance to stable/production.

Environment isolation is binding: staging and production maintain separate authoritative state, secrets/credentials and protected-deployment authority. Artifact promotion does not implicitly migrate database/runtime state.

Bot-mode promotion is separately governed. A production environment may run stable SHADOW or PAPER generations. LIVE remains fail-closed until a separate owner-approved live-capital, credential, execution and risk-acceptance package authorizes it. No branch, release-channel or environment promotion can supply missing PAPER/LIVE eligibility.

`docs/ai_platform/portal/RELEASE_ENVIRONMENT_AND_BOT_MODE_ARCHITECTURE.md` is the binding detailed architecture for this decision.

Reason:

The temporary single-`develop` trunk policy intentionally deferred a production/release split until an explicit owner decision. The platform now has protected staging workflows, production-capable Portal architecture and explicit SHADOW/PAPER/LIVE runtime semantics. Treating `develop` as “test” and `main` as “production” would conflate source integration with deployment authority and, more dangerously, allow production environment terminology to be mistaken for live-trading authority.

Separating the dimensions provides auditable release provenance, safer promotion/rollback, clear upstream synchronization and an explicit guarantee that production infrastructure does not silently grant bot execution authority.

Migration impact:

The target decision supersedes the temporary 2026-08-09 single-trunk architecture policy, but implementation is staged and must not be fabricated by documentation:

1. merge ADR-021, registry and governance updates into the currently authoritative `develop` branch;
2. create `main` from the exact accepted migration base;
3. configure required `main` rules/protection and release gates before using it as release authority;
4. update workflow triggers, automation and deployment/release references for the two-branch model;
5. verify `develop -> main` release promotion and immutable artifact provenance without live-capital authority;
6. change the repository default branch to `main` only after agent, CI, upstream-sync and deployment routing are proven safe;
7. retain `develop` as the integration branch.

Until the physical migration has exact repository evidence, agents must distinguish **accepted target architecture** from **implemented branch state** and continue routing ordinary work according to the current proven repository/governance state.

Historical task/PR/deployment evidence using phrases such as “production research/shadow runtime” remains immutable history. New evidence should identify environment, release channel and bot mode separately; old wording is mapped only when exact evidence proves the mapping.

Consequence:

The canonical target flow is:

```text
upstream develop -> fork develop -> candidate artifact -> staging acceptance
                 -> release promotion -> main -> stable immutable artifact -> production authorization
```

This is not full ceremonial GitFlow. Production-critical hotfixes may use a narrowly authorized stable repair path, but the semantic fix must be reconciled back into `develop`.

ADR-021 does not weaken ADR-019 or ADR-020 and grants no production deployment, protected-host mutation, exchange credential activation, PAPER/LIVE promotion, model promotion, order submission, withdrawal or live-capital authority.
