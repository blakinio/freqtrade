# AI Trading Portal implementation boundary

This directory contains the project-specific AI Trading Portal implementation for this Freqtrade fork.

The Portal is **partially implemented and actively evolving**. Do not infer feature completeness from this README or from the presence of a package. Current implementation status is proven from the exact repository head by the living Portal completeness ledger at `tools/portal_audit/ledger/index.json`; architecture and target-state authority are indexed by `ARCHITECTURE_REGISTRY.yaml` and the canonical documents under `docs/ai_platform/portal/`.

## Current package boundary

Selected implemented roots include:

```text
ai_platform/portal/
  contracts/       # versioned domain/API/event contracts
  control_plane/   # FastAPI/control-plane domain and persistence composition
  execution/       # Freqtrade adapter and managed runtime orchestration
  events/          # event and transport boundaries
  credentials/     # credential metadata and secret-reference boundaries
  database/        # database/schema support
  identity/        # identity and authorization integration
  security/        # Portal security controls and sensitive-data guards
  risk/            # deterministic risk policy evaluation
  observability/   # runtime/telemetry contracts and helpers
  e2e/             # full-platform scenario definitions/harness
  web/             # Next.js/React Portal
```

Additional packages may represent implemented components, compatibility surfaces, research work, or target-state work. Use the living exact-head ledger and task-specific evidence before making an implementation-completeness claim.

Deployment-specific code is intentionally separated under `deploy/` (including Synology targets) and supporting deployment/ingress configuration may also live under `ai_platform/portal/deploy/`.

## Dependency direction

Preferred high-level dependency direction remains:

```text
contracts
  ^
  |
control_plane <---- model_control
  ^    ^             ^
  |    |             |
  |   risk        learning
  |                  ^
execution          intelligence
  ^                  ^
  |                  |
  +------ events / observability

simulator/e2e depend on public/internal contracts, not private implementation details.
web depends on Portal APIs/contracts, never on Freqtrade internals.
```

Avoid circular imports between domain packages. Shared concepts move into versioned contracts only through an explicit contract-change task.

## Source-of-truth hierarchy

- **Current implementation:** exact code, migrations, tests, workflows, deployed-target evidence, and `tools/portal_audit/ledger/index.json` on the exact head.
- **Architecture authority:** `ARCHITECTURE_REGISTRY.yaml`, accepted ADRs, and task-relevant documents under `docs/ai_platform/portal/`.
- **Historical documents:** evidence for their recorded revision only; they do not override exact current implementation or later accepted ADRs.

A target-state architecture document must not be reported as implemented without exact implementation evidence, and a present package must not be treated as a complete user-facing capability without the required producer/consumer, integration, audit and E2E evidence.

## Upstream isolation

Do not place Portal-specific code under upstream `freqtrade/` unless a required capability is proven impossible through supported extension/API boundaries and the change receives separate review.

## Safety

- no secrets in repository files;
- no public Freqtrade listener;
- PAPER/dry-run is the only currently authorized operational trading mode;
- SHADOW is optional and purpose-bound for bounded validation;
- LIVE remains unreachable/fail-closed until a separate explicit owner-approved architecture and implementation programme;
- no private third-party UI captures or user profile data;
- no autonomous production patch path.

See `docs/ai_platform/portal/` for canonical architecture and delivery contracts, and `tools/portal_audit/ledger/index.json` for the living exact-head implementation inventory.
