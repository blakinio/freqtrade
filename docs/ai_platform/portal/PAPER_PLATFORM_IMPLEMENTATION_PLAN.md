# PAPER Platform Implementation Plan

Status: `accepted dependency-gated implementation plan`

Architecture authority: `ADR-019`, `ADR-020`, `ADR-021`, `ADR-022`

Target architecture: `docs/ai_platform/portal/PAPER_FIRST_PLATFORM_ARCHITECTURE.md`

Executor prompt: `docs/agents/prompts/PAPER_PLATFORM_EXECUTOR.md`

Short alias: `WDROŻENIE PAPER`

## 1. Objective

Deliver one secure, authoritative and recoverable PAPER platform path before broadening the product. PAPER is the default and only currently authorized operational mode. SHADOW is optional for bounded test, training, diagnostic or parity work. LIVE remains unreachable.

This plan is a dependency graph, not proof of implementation and not authorization to mutate protected environments, secrets, private exchange credentials or live capital.

## 2. Current-state anchors

Verified on `2026-08-10` against `develop@2a9bee4895981f0a2b7f7f08e0e1d2d2e2ad646a`; every execution invocation must re-resolve live state before mutation:

- default/integration branch: `develop`;
- `main`: accepted target release branch; physical migration is not assumed complete;
- #1353 trusted runtime/control-state separation: `closed`;
- #1357 authored/desired/observed revision state: `closed`;
- #1354 runtime isolation: `open` with draft PR #1431; reuse or explicitly supersede it rather than duplicate it;
- #1355 Runtime Supervisor: `open`, priority P0 / critical risk;
- #1356 architecture-registry lifecycle guard: `open`;
- #1396 WickHunter SHADOW/PAPER mode lifecycle: `open`; reconcile it with ADR-022 rather than reimplement blindly.

Closed Issues are evidence to verify, not work to reopen automatically. Open Issues are hypotheses to re-check against exact code before implementation.

## 3. Programme invariants

- no reachable LIVE transition;
- no production/private trading credential activation, real order or withdrawal path;
- managed PAPER Freqtrade runtimes keep `dry_run: true`;
- SHADOW only when a bounded package states its need and exit condition;
- browser never reaches Freqtrade, Supervisor, Gateway, Vault or exchange credentials directly;
- only Runtime Supervisor has container-engine authority;
- Gateway is the only Portal-to-Freqtrade application boundary;
- deterministic risk remains final veto;
- intent, HTTP 202 or ACK is never represented as reconciled execution;
- exact generation, eligibility, risk and execution-profile identity accompanies execution/evidence claims;
- unsupported host enforcement fails closed;
- do not expand product breadth while doing so increases `PARTIAL`/`DISCONNECTED` debt instead of closing a complete path.

## 4. Gate overview

```text
G0 truth and PAPER guardrails
  -> G1 runtime-state conformance
  -> G2 effective runtime isolation
  -> G3 Runtime Supervisor + Gateway authority
  -> G4 command/reconciliation/valuation spine
  -> G5 first complete PAPER vertical slice
  -> G6 PAPER realism and parity
  -> G7 portfolio risk and Evidence Workbench
  -> G8 operational/protected-target acceptance
  -> G9 release-branch migration when independently ready
```

G9 is independent of bot mode and never unlocks LIVE.

## 5. G0 — One truth and PAPER fail-closed guardrails

### Goal

Remove governance contradictions and make PAPER-first policy an enforceable repository invariant.

### Work

1. Merge ADR-022, PAPER architecture, this plan and executor prompt.
2. Replace lifecycle wording that makes SHADOW mandatory or exposes a current `live-small`/LIVE progression.
3. Reconcile WickHunter #1396 and programme wording with PAPER-first policy while preserving valid historical SHADOW evidence.
4. Resolve #1356 with a validator that prevents closed/completed Issues from remaining in `open_architecture_findings`.
5. Establish status authority:
   - `ARCHITECTURE_REGISTRY.yaml` = architecture/document authority;
   - `tools/portal_audit/ledger/*` = exact-head implementation inventory after migration acceptance;
   - older feature/programme status views = generated/validated roll-ups or historical evidence;
   - GitHub Issues = work ownership, not standalone implementation truth.
6. Add fail-closed contract tests proving LIVE is omitted/rejected across reachable schema/API/UI/config/runtime/promotion boundaries.
7. Hide, feature-flag or explicitly mark disconnected product surfaces unavailable.

### Acceptance

- no governing document requires SHADOW before PAPER;
- no reachable operation enables LIVE;
- registry/ADR links and lifecycle state are consistent;
- closed #1353/#1357 are no longer represented as open findings after exact validation;
- implementation-status authority and roll-up rules are explicit and CI-enforced;
- code guardrail changes have focused/integration tests; docs-only runtime E2E may be `NOT_APPLICABLE_WITH_REASON`.

## 6. G1 — Runtime-state conformance baseline

### Goal

Verify the closed #1353/#1357 implementation against ADR-020/ADR-022 and fill only proven residual gaps.

### Work

- map authored revision, desired revision/generation and observed generation storage/APIs;
- prove Freqtrade cannot redefine Portal-authoritative generation/config evidence;
- bind operating mode, PAPER eligibility evidence and `paper_execution_profile_digest` to immutable generation identity;
- verify optimistic concurrency, stale revision rejection, migration and rollback behavior;
- expose unknown/degraded/drift state instead of optimistic defaults.

### Acceptance

- exact code/migration/test evidence supports each state claim;
- saving a DRAFT never executes it;
- wrong/stale generation or state-version changes fail closed;
- migration plus rollback/restore tests pass;
- closed Issues stay closed unless a new evidence-backed regression exists.

## 7. G2 — Effective runtime isolation

### Goal

Complete #1354 through PR #1431 or its explicitly documented successor.

### Work

- finish immutable `RuntimeIsolationProfile` and resolved `RuntimeIsolationPlan` binding;
- host capability discovery and deterministic plan resolution;
- hardened non-root image, read-only root, no-new-privileges, drop capabilities, no Docker socket/host ports/devices;
- hard CPU, memory/swap, PID, durable-storage, tmpfs and log bounds;
- deny-by-default network/egress policy with only required public market-data and local Gateway relationships;
- structural plus effective kernel/host attestation;
- real-Docker positive and negative tests, including unsupported-host rejection;
- verify Synology behavior only under separately authorized protected-target acceptance.

### Acceptance

- PR #1431 or successor is terminal with no unintended duplicate implementation;
- requested flags or `docker inspect` alone are not accepted as effective enforcement proof;
- unsupported controls produce `HOST_INCOMPATIBLE` with bounded reason codes;
- real-Docker tests prove no host port, no privilege/capability escape, bounded resources/storage/logs and blocked unauthorized reachability;
- independent security audit and exact-head required CI pass.

## 8. G3 — Runtime Supervisor and Gateway

### Goal

Close #1355 and isolate privileged lifecycle authority from application access.

### Work

- minimal Runtime Supervisor as the only process with container-engine access;
- read-only trusted generation view and allow-listed lifecycle API over UDS with peer credentials;
- no arbitrary image, command, environment, mount, port, device, capability or network parameters;
- durable command journal, idempotency, state/version preconditions and monotonic fencing;
- generation-bound Gateway over UDS, never a general reverse proxy;
- generation-local Freqtrade API credentials inaccessible to ordinary workers;
- engine restart policy `NO`; desired-state reconciliation controls recreation;
- one active execution-owned generation per tenant/bot.

### Acceptance

- repository/deployment evidence proves no Docker socket outside Supervisor;
- Supervisor cannot access exchange credentials and Gateway cannot create containers;
- duplicate/stale/expired/wrong-generation commands cannot duplicate or mutate runtime state;
- worker/daemon restart cannot resurrect a stale generation;
- UDS ACL/identity negative tests and real-Docker lifecycle E2E pass;
- security review and exact-head CI pass.

## 9. G4 — Authoritative reconciliation and valuation spine

### Goal

Make observed generation, orders, positions, trades and valuation authoritative rather than inferred from intents or ACKs.

### Work

- durable desired-state/reconciliation worker;
- generation-aware ordering, source sequence/version, reconciliation epoch and duplicate/conflict hashes;
- command lifecycle from received to reconciled terminal state;
- `ExecutionSafetyEpoch`/fencing for exposure-increasing PAPER commands;
- authoritative Gateway reads for runtime health, orders, positions and trades;
- valuation with freshness and generation attribution;
- outbox/inbox, retry/backoff, poison/dead-letter states and replay tooling;
- explicit stale/degraded/unavailable/drift states and lag metrics.

### Acceptance

- HTTP 202/intent/ACK never appears as completed execution;
- observed generation and reconciled state are visible to API/UI/audit;
- duplicate, out-of-order, stale input and worker crashes converge correctly;
- valuation refuses missing/stale/wrong-generation evidence;
- stale safety-epoch commands fail closed;
- integration tests use real PostgreSQL and the real Gateway/runtime boundary where applicable.

## 10. G5 — First complete PAPER vertical slice

### Goal

Deliver one end-to-end product journey before expanding feature breadth.

### Journey

```text
create bot
-> immutable revision
-> PAPER eligibility check
-> desired RuntimeGeneration
-> Supervisor rollout
-> Gateway health/read
-> observed RuntimeGeneration
-> PAPER order/position/trade evidence
-> authoritative valuation
-> reconciliation
-> Decision Black Box/audit
-> controlled restart
-> rollback to prior generation
```

### Required scenarios

- happy path;
- risk rejection and no-trade evidence;
- stale data/source unavailable;
- duplicate command and out-of-order event;
- worker/Supervisor/Gateway/runtime crash and recovery;
- generation replacement conflict;
- restart and rollback;
- unsupported host isolation;
- browser journey without fixture interception.

### Acceptance

- real PostgreSQL, real container engine and real Freqtrade `dry_run: true` runtime;
- no browser/public direct runtime access;
- exact data/model/config/risk/profile/image/isolation/generation identities in evidence;
- no duplicate side effects across retry/recovery/restore;
- focused, component, integration, independent audit, real Chromium E2E and exact-head CI pass.

## 11. G6 — PAPER realism and parity

### Goal

Make PAPER assumptions explicit, immutable and comparable.

### Work

- `PaperExecutionProfile` schema, persistence, digest and generation binding;
- fees, spread, slippage, latency, liquidity, partial fills, cancel/replace, stale-data, funding, margin and liquidation assumptions;
- automatic backtest/replay/PAPER parity report;
- explicit limitations when queue position, depth or throttling cannot be modeled;
- immutable resettable `PaperPortfolioGeneration` instead of destructive reset;
- stress scenarios and profile compatibility/versioning.

### Acceptance

- runs are comparable only with exact profile identity or explicit differences;
- UI/API show assumptions and limitations;
- parity divergences have reason codes and source evidence;
- no result is labelled realistic without supporting evidence;
- Freqtrade remains the PAPER runtime unless measured gaps justify a separate ADR.

## 12. G7 — Portfolio risk and Evidence Workbench

### Goal

Compose research, eligibility, PAPER operation and portfolio safety into one coherent product.

### Work

- Portfolio Risk Engine and immutable virtual-capital/budget allocator;
- gross/net/per-symbol/correlation/concentration/drawdown/turnover/liquidity limits;
- portfolio/bot kill switches, source-health and drift suspension;
- shared versioned `ExecutionPlan` state machine for bounded entry/exit/DCA/grid/TWAP behavior;
- Evidence Workbench: idea → dataset → experiment → validation → candidate → `PAPER_ELIGIBLE` → PAPER → drift/review/retire;
- champion/challenger with optional SHADOW and no automatic promotion;
- Decision Black Box including `NO_TRADE` and `RISK_REJECTED`;
- outcome-oriented navigation.

### Acceptance

- bots cannot self-allocate virtual capital;
- every execution plan has legal transitions and recovery semantics;
- model/strategy promotion is explicit and exact-identity-bound;
- AI cannot bypass deterministic intent/portfolio risk;
- product surfaces use authoritative data and disclose degraded/unavailable states.

## 13. G8 — Operations and protected-target acceptance

### Goal

Prove the PAPER platform is observable and recoverable in the intended environment without granting LIVE authority.

### Work

- SLOs for source freshness, command-to-observed latency, reconciliation/outbox lag, restart rate, parity divergence and drift;
- independent deadman path that does not depend on the failing platform alert channel;
- PostgreSQL/artifact backup and clean-environment restore drill;
- restore/replay proving no duplicate commands or stale-generation resurrection;
- disk/log/storage capacity and cleanup controls;
- Authentik/Vault/Cloudflare/Synology acceptance only under separate protected-environment authorization;
- move execution to a compatible Linux host/VM if Synology cannot prove hard isolation.

### Acceptance

- alert-delivery failure is externally detectable;
- backup restore reproduces authoritative state and exact evidence identities;
- runtime recreation after restore is deliberate, fenced and idempotent;
- measured RTO/RPO are recorded;
- protected-target acceptance cannot be inferred from a deployment package or CI result.

## 14. G9 — `main` release migration

Follow ADR-021 and the existing migration programme. This gate is independent of bot mode.

Acceptance requires protected `main`, dedicated `develop -> main` promotion, release CI, immutable build-once/promote-same-digest evidence, branch-reference cleanup and safe default-branch routing. A stable production release may still run PAPER only and never unlocks LIVE.

## 15. Parallelization and programme completion

Do not parallelize competing writers to RuntimeGeneration/state migrations, isolation/Supervisor lifecycle contracts, reconciliation/valuation authority, status-ledger migration or protected-host runtime architecture.

Preferred critical path:

```text
G0 -> verify G1 -> finish G2 -> G3 -> G4 -> G5 -> G6/G7 -> G8
```

The PAPER programme is complete only when ADR-022 is technically enforced, one status authority is CI-enforced, runtime isolation/Supervisor/Gateway are effective, observed state is authoritative, the first full PAPER journey passes real runtime/browser E2E, PAPER execution assumptions/parity are explicit, portfolio risk/evidence are composed for supported journeys, operational recovery evidence exists for the authorized target, and all related PR/task/Issue/registry state is terminal and accurate.

Completion grants no LIVE or real-capital authority.
