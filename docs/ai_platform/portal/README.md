# AI Trading Portal Program

## Purpose

The AI Trading Portal is the future product/control layer above the existing Freqtrade-based AI Platform. It provides a modern web portal, secure bot orchestration, AI/model lifecycle controls, trade intelligence, observability, and autonomous end-to-end validation without turning an ML model or a browser session into an unrestricted execution authority.

This program is additive. It does not modify the frozen Phase 5 candidate, the protected prospective final holdout, the completed Phase 6 comparison contract, or the authoritative Phase 6 `selected_model = null` outcome.

## Core principle

```text
Portal manages intent and policy.
AI produces predictions and research candidates.
Risk controls can veto execution.
Freqtrade owns trade execution and lifecycle.
The exchange remains the external execution venue.
```

Freqtrade is therefore an execution engine behind a private adapter boundary, not the public backend of the portal.

## Architecture planes

The target system is divided into six explicit planes:

1. **Portal / UX Plane** — user-facing web application and BFF/API boundary.
2. **Control Plane** — bot specifications, lifecycle, exchange connections, policy and orchestration.
3. **Execution Plane** — isolated Freqtrade runtimes and exchange connectivity.
4. **AI / Research Plane** — datasets, features, training, experiments, model registry and controlled promotion.
5. **Data Plane** — metadata, event streams, market/trade telemetry, artifacts and audit records.
6. **Quality & Autonomous Validation Plane** — deterministic simulators, browser E2E, security E2E, AI scenario tests and controlled agent-assisted repair.

Cross-cutting boundaries:

- **Security Plane** — Cloudflare edge, Zero Trust for privileged surfaces, identity, RBAC, secrets, tenant isolation and audit.
- **Risk Plane** — deterministic capital and execution controls independent from model confidence.
- **Observability Plane** — OpenTelemetry-compatible traces, metrics, logs and correlation IDs across user action -> portal -> orchestrator -> Freqtrade -> trade analysis.

## Initial implementation posture

The portal remains a **modular monolith control plane** plus isolated workers/runtimes, not a premature fleet of microservices. Boundaries and contracts remain explicit so modules can later split into services without changing portal-facing APIs.

Current project-specific shape:

```text
ai_platform/portal/
  contracts/       # shared versioned API/event/domain contracts
  control_plane/   # FastAPI modular control plane
  execution/       # Freqtrade adapter/orchestration boundary
  events/          # event/outbox integration
  observability/   # telemetry contracts/instrumentation
  risk/            # deterministic risk policy
  model_control/   # model lifecycle control integration
  intelligence/    # post-trade analysis and AI insights
  learning/        # insight -> hypothesis -> experiment workflow
  simulator/       # deterministic exchange/market simulator
  e2e/             # full-platform scenario harness
  web/             # Next.js/React portal
  deploy/          # production-like deployment boundary
  quality_agent/   # bounded autonomous diagnosis/repair
```

Implementation work must continue to follow the frozen architecture and safety boundaries rather than treating a merged foundation slice as completion of an entire roadmap stage.

## Documentation map

- `SYSTEM_ARCHITECTURE.md` — components, planes, trust boundaries and deployment evolution.
- `SECURITY_ARCHITECTURE.md` — Cloudflare, Zero Trust, identity, secrets, segmentation and threat controls.
- `AI_ML_AND_LEARNING_ARCHITECTURE.md` — training, model registry, continual learning and safe self-improvement.
- `DATA_AND_OBSERVABILITY_ARCHITECTURE.md` — data ownership, event contracts, decision snapshots, telemetry and retention.
- `QUALITY_AND_AUTONOMOUS_E2E.md` — full-platform testing, user simulation and bounded agent-assisted repair.
- `UI_INFORMATION_ARCHITECTURE.md` — target portal navigation and major product surfaces.
- `UI_DELIVERY_STATUS.md` — truthful per-surface implementation/integration status and remaining read-model gaps.
- `ARCHITECTURE_DECISIONS.md` — accepted program-level decisions that downstream agents must not silently redefine.
- `DELIVERY_ROADMAP.md` — staged delivery plan and gates.
- `AGENT_EXECUTION_PLAN.md` — bounded agent workstreams, ownership and dependencies.

## Non-negotiable safety boundaries

- Freqtrade REST/WebSocket surfaces are private and never exposed directly to the public Internet.
- Exchange keys are never committed, never returned to the browser after storage, and must not have withdrawal permission.
- New trading configurations remain `dry_run: true` until a separately reviewed live-capital work package is explicitly approved.
- Research jobs cannot access production exchange credentials.
- Training or post-trade analysis cannot directly mutate a running production model or strategy.
- Model promotion is explicit, auditable and evidence-gated.
- Autonomous repair agents may create branches, regression tests and PRs; they may not patch production or bypass CI.
- Raw private UI captures, profile identifiers, session material and third-party proprietary assets must not be committed as product code or public documentation.

## Relationship to the existing AI Platform

The existing research lifecycle remains authoritative:

`experiment -> candidate -> validated -> dry-run -> shadow -> live-small -> production -> retired`

The portal consumes only artifacts whose lifecycle state allows the requested use. It must never reinterpret historical evidence to retroactively change completed comparison contracts.

The protected final holdout `20260801-20260930`, frozen thresholds `0.006/-0.009`, completed Phase 6 comparison, PyTorch evidence track and RL evidence tracks remain governed by their existing records and are outside this portal architecture work package.
