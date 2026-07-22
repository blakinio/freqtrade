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
