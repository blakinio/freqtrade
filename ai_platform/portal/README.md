# AI Trading Portal implementation boundary

This directory is reserved for future AI Trading Portal implementation owned by the project-specific layer of this fork.

No portal runtime is implemented by the architecture-foundation work package.

## Planned package layout

```text
ai_platform/portal/
  contracts/       # shared versioned domain/API/event contracts
  control_plane/   # future FastAPI modular backend and persistence
  execution/       # Freqtrade adapter and runtime orchestration
  events/          # outbox/inbox/event transport abstractions
  observability/   # telemetry contracts and instrumentation helpers
  risk/            # deterministic risk policy evaluation
  model_control/   # model/dataset/feature lifecycle control-plane integration
  intelligence/    # DecisionSnapshot, TradeOutcome and post-trade analysis
  learning/        # insight -> hypothesis -> experiment/training workflow
  simulator/       # deterministic exchange/market simulator
  e2e/             # full-platform scenario definitions/harness
  web/             # future Next.js/React portal (tooling boundary to be declared)
  deploy/          # production-like deployment manifests/runbooks, including Cloudflare
  quality_agent/   # bounded autonomous diagnosis/repair integration
```

Directories should be created by their owning bounded implementation tasks rather than populated with speculative code in advance.

## Dependency direction

Preferred high-level dependency direction:

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
web depends on portal APIs/contracts, never on Freqtrade internals.
```

Avoid circular imports between domain packages. Shared concepts move into versioned contracts only through an explicit contract-change task.

## Upstream isolation

Do not place portal-specific code under upstream `freqtrade/` unless a required capability is proven impossible through supported extension/API boundaries and the change receives separate review.

## Security

- no secrets in repository files;
- no public Freqtrade listener;
- dry-run by default;
- no private third-party UI captures or user profile data;
- no autonomous production patch path.

See `docs/ai_platform/portal/` for the canonical architecture and delivery plan.
