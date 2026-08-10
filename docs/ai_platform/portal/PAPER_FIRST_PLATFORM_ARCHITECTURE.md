# PAPER-First Quant Platform Architecture

Status: `accepted policy and target refinement`

Owner acceptance: `2026-08-10`

Binding decision: `ADR-022`

Related decisions: `ADR-019`, `ADR-020`, `ADR-021`

Implementation sequence: `docs/ai_platform/portal/PAPER_PLATFORM_IMPLEMENTATION_PLAN.md`

## 1. Purpose

The Quant Platform is an owner-controlled, auditable research and PAPER execution environment built around private Freqtrade runtimes. Its product value is not an opaque promise that AI will produce profit. Its defensible value is that every PAPER decision can be reconstructed, explained and constrained by deterministic risk using exact data, feature, strategy, model, parameter, configuration, code, artifact, execution-profile and runtime-generation identity.

This document defines the PAPER-first target architecture. It is not proof that every component is implemented, integrated, deployed or accepted on a protected host.

## 2. Binding operating-mode policy

### PAPER

`PAPER` is the default and only currently authorized operational trading mode.

A managed Freqtrade runtime uses `dry_run: true`. It may consume current public market data and produce simulated orders, positions, trades and PnL through approved PAPER semantics. PAPER never grants real exchange-order or live-capital authority.

### SHADOW

`SHADOW` is an optional, bounded validation mode. It consumes current or replayed inputs and creates decisions/evidence without simulated order submission when that distinction is required for:

- model or strategy training/validation;
- source and feature diagnostics;
- observation-only integration/runtime tests;
- replay-to-runtime parity;
- drift, latency or decision-timing analysis.

Every new SHADOW package must state why PAPER is not appropriate for that evidence, its bounded duration/exit condition and the evidence it produces. SHADOW is not a mandatory promotion stage.

### LIVE

`LIVE` is reserved terminology only. It is unreachable in the current state machine and must fail closed in every mode-setting boundary. The platform does not activate production trading credentials, send real orders, allocate real capital or enable withdrawals.

A future LIVE design cannot be inferred from PAPER implementation. It requires a separate owner-approved programme and ADR.

## 3. Lifecycle and eligibility

### 3.1 Strategy/model lifecycle

```text
experiment
   -> candidate
   -> validated
   -> paper-eligible
   -> paper
   -> paper-suspended | retired
```

Optional side lane:

```text
candidate | validated -> shadow-validation -> validated
```

### 3.2 Eligibility states

```text
NOT_EVALUATED
RESEARCH_ONLY
PAPER_ELIGIBLE
PAPER_SUSPENDED
RETIRED
```

Eligibility applies to an immutable evidence tuple, not a mutable strategy/model name:

```text
dataset_digest
feature_schema_digest
strategy_digest
model_digest_or_none
parameter_digest
risk_policy_digest
paper_execution_profile_digest
code_sha
artifact_digest
validation_evidence_digest
```

A changed tuple requires a new eligibility decision. `PAPER_ELIGIBLE` never implies LIVE eligibility.

## 4. Runtime identity and state

ADR-020 remains authoritative. Every executable generation binds at least:

```text
tenant_id
bot_id
runtime_generation_id
config_revision_id
strategy/model/parameter identities
risk_policy_id + digest
paper_execution_profile_id + digest
image/artifact digests
runtime_isolation_profile_id + digest
runtime_isolation_plan_id + digest
gateway_contract_version
operating_mode = PAPER | bounded SHADOW
eligibility_evidence_id
```

The platform keeps three separate state classes:

- **authored state** — immutable user-authored revisions and evidence;
- **desired state** — the generation the Control Plane wants active;
- **observed state** — the generation and application state proven by Supervisor/Gateway reconciliation.

Saving a revision, returning HTTP `202`, writing an intent or receiving a runtime ACK is not execution proof.

## 5. Trusted runtime topology

```text
Browser
  |
  v
same-origin Web/BFF
  |
  v
FastAPI Control Plane --------> PostgreSQL authority
  |                                  |
  |                                  +-- authored/desired/observed state
  |                                  +-- durable command journal
  |                                  +-- outbox/inbox and audit
  |
  +--> reconciliation worker --UDS--> Runtime Supervisor --> container engine
  |                                  (only engine authority)
  |
  +--> application worker ----UDS--> generation-bound Gateway
                                      |
                                      v
                                 private Freqtrade
                                 PAPER generation
```

Invariants:

- only Runtime Supervisor has container-engine authority;
- browser, BFF, API, ordinary workers, AI/training and Gateway have no Docker socket;
- Supervisor accepts an approved immutable generation identity, never arbitrary image/mount/command/env/network/capability passthrough;
- Gateway is the only Portal-to-Freqtrade application boundary and is not a general reverse proxy;
- Freqtrade has no public/host port and no browser reachability;
- host capability or effective isolation failure produces `HOST_INCOMPATIBLE`, never a weaker fallback;
- only one active execution-owned generation exists for `(tenant_id, bot_id)`;
- replacement is stop-then-replace until a separately justified design changes it;
- reconciliation, not acknowledgement, determines observed truth.

## 6. Durable command and reconciliation semantics

Every lifecycle or PAPER execution command carries:

```text
command_id
tenant_id
bot_id
runtime_generation_id
safety_epoch
idempotency_key
expected_state_version
issued_at
expires_at
actor
reason
payload_digest
```

Target lifecycle:

```text
RECEIVED
  -> VALIDATED
  -> RISK_ACCEPTED | RISK_REJECTED
  -> DISPATCHED
  -> ACKNOWLEDGED
  -> OBSERVED
  -> RECONCILED
  -> COMPLETED | FAILED | EXPIRED
```

Only reconciled authoritative state may be presented as completed execution. Duplicate, stale, expired, wrong-generation and wrong-safety-epoch commands fail closed. Recovery and replay must not duplicate side effects.

## 7. PAPER execution realism

`PaperExecutionProfile` is an immutable first-class target object and part of `RuntimeGeneration` identity.

Minimum profile:

```text
venue + market_type
order_types
maker/taker fee schedule
spread model
slippage model
latency model
liquidity/market-depth model
partial-fill policy
cancel/replace and timeout policy
stale-market-data policy
funding and mark-price model
margin and liquidation model
exchange throttling assumptions
profile schema/version + digest
```

The first implementation should use Freqtrade dry-run as the operational PAPER engine and the existing deterministic simulator/replay as the comparison layer. A second custom execution engine is justified only by measured, documented parity gaps that cannot be safely handled through the existing adapter/profile boundary.

Every PAPER result must state its assumptions. Unsupported queue position, incomplete market depth or approximated partial fills remain explicit limitations rather than being hidden behind a single marketing score.

## 8. Parity and evidence

For each eligible strategy/generation, produce a parity report across applicable evidence:

```text
BACKTEST
vs DETERMINISTIC REPLAY
vs PAPER
```

Compare at least:

- signals and no-trade decisions;
- intents, deterministic risk approvals/rejections and reason codes;
- expected versus observed prices;
- fees, spread, slippage, latency and partial fills;
- orders, positions and trades;
- PnL, exposure, turnover and drawdown;
- source/feature freshness and quality;
- divergence reasons and unresolved unknowns.

The Decision Black Box traces:

```text
input data
-> features
-> deterministic strategy/model evidence
-> TradeIntent
-> RiskDecision
-> ExecutionPlan/command
-> expected PAPER outcome
-> observed/reconciled outcome
```

`NO_TRADE`, `RISK_REJECTED`, degraded and unavailable states are first-class evidence.

## 9. Portfolio-level safety

Per-intent deterministic risk remains mandatory. The target Portfolio Risk Engine additionally controls PAPER budgets across bots:

- gross/net and per-symbol exposure;
- long/short concentration and correlated exposure;
- daily/rolling loss and drawdown limits;
- liquidity and turnover limits;
- maximum concurrent positions;
- source-health, stale-data and model/feature-drift suspension;
- portfolio and per-bot kill switches;
- immutable budget/allocation revisions.

A bot cannot allocate additional virtual capital to itself. Portfolio allocation is an explicit versioned decision.

## 10. Product composition

Product navigation should follow user outcomes rather than internal module count:

1. Overview;
2. Research & Evidence;
3. PAPER Bots;
4. Risk & Portfolio;
5. Operations & Audit.

Disconnected pages must be hidden, feature-flagged or explicitly marked unavailable. A persisted intent, mock provider or fixture-backed page is not presented as a working trading capability.

The first complete vertical slice is:

```text
create bot
-> immutable revision
-> PAPER eligibility
-> desired RuntimeGeneration
-> Supervisor rollout
-> Gateway health/read
-> observed RuntimeGeneration
-> orders/positions/trades + authoritative valuation
-> reconciliation
-> audit/Decision Black Box
-> controlled restart
-> rollback to prior generation
```

## 11. Technology and scaling posture

Keep the Control Plane modular-monolith-first. Separate Supervisor and Gateway because they are trust boundaries, and separate durable/background workers where execution characteristics require it.

Default platform choices:

- PostgreSQL is authoritative state and the initial outbox/inbox/command-journal spine;
- object storage holds immutable artifacts and evidence;
- Redis, if used, is cache/ephemeral coordination only;
- NATS/JetStream is optional after measured fan-out/throughput need and never the sole source of truth;
- Kubernetes is not required at the current scale;
- Freqtrade remains replaceable behind the private adapter/Gateway boundary;
- unsupported Synology host enforcement fails closed; execution may move to a dedicated Linux host/VM rather than weakening isolation.

## 12. Operational acceptance

PAPER operational maturity requires exact evidence for:

- real PostgreSQL, real container engine and real Freqtrade dry-run integration;
- effective isolation and negative tests;
- idempotent crash/retry/recovery behavior;
- desired/observed reconciliation and stale-generation fencing;
- authoritative orders/positions/trades/valuation;
- controlled restart and rollback without duplicate side effects;
- SLOs, source freshness, queue/reconciliation lag and drift;
- independent deadman alerting;
- backup plus clean-environment restore drill;
- exact artifact/config/generation provenance;
- protected-target acceptance only when separately authorized.

## 13. Non-goals

Current PAPER work does not authorize or prioritize:

- LIVE or real-capital execution;
- withdrawals or production trading credentials;
- copy/social trading or strategy marketplace;
- autonomous model/code promotion;
- reinforcement learning as execution authority;
- more bot types before a shared `ExecutionPlan` and first complete vertical slice;
- broad microservices or Kubernetes;
- replacement of Freqtrade without measured adapter/parity evidence.
