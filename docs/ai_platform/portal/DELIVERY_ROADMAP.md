# AI Trading Portal — Delivery Roadmap

## 1. Program boundary

This roadmap is a **parallel portal/platform program**, not a renumbering of the existing AI research phases.

It must not:

- alter the frozen Phase 5 thresholds;
- consume the protected final holdout iteratively;
- reopen completed Phase 6 model selection;
- reinterpret PyTorch/RL evidence as production approval;
- enable live capital implicitly.

Each stage lands as a bounded work package or small series of reviewable PRs.

Status values:

- `planned`
- `active`
- `blocked`
- `done`

## P0 — Architecture and governance foundation

Status: `active`

Goal: freeze architectural boundaries and agent work ownership before implementation.

Deliverables:

- portal program overview;
- system architecture;
- security architecture;
- AI/ML learning architecture;
- data/observability architecture;
- E2E/autonomous validation architecture;
- UI information architecture;
- delivery roadmap;
- agent execution plan.

Acceptance:

- no runtime behavior changed;
- no research evidence or holdout consumed;
- boundaries are linked from canonical AI Platform docs;
- first implementation work packages have disjoint ownership.

## P1 — Domain contracts and security foundation

Status: `planned`

Goal: establish fail-closed domain/API/event/security contracts before building product workflows.

Deliverables:

- tenant/actor/resource identity contracts;
- capability/RBAC model;
- BotInstance/BotConfigRevision contracts;
- ModelVersion/RiskPolicyVersion references;
- event envelope and schema versioning;
- secret-reference abstraction;
- audit event contract;
- Cloudflare/Zero Trust deployment contract and threat model;
- security architecture tests that are possible without a full portal.

Acceptance:

- no secret values can appear in serializable public/event contracts;
- tenant scope is mandatory on tenant-owned domain objects;
- Freqtrade is explicitly private in network/deployment contracts;
- live-capital state cannot be selected by default.

## P2 — Control Plane core

Status: `planned`

Goal: implement the first modular backend control plane without public Freqtrade coupling.

Deliverables:

- FastAPI application boundary;
- PostgreSQL migrations;
- tenant context;
- bot CRUD and immutable revisions;
- strategy/model/risk references;
- desired/observed state model;
- audit persistence;
- outbox foundation;
- OpenAPI/contract tests.

Acceptance:

- server-side tenant isolation tests pass;
- bot changes create immutable revisions;
- privileged operations are capability-gated;
- no direct exchange or Freqtrade credentials are exposed to API consumers.

## P3 — Freqtrade execution adapter and bot orchestrator

Status: `planned`

Goal: safely manage isolated dry-run Freqtrade runtimes through a private adapter.

Deliverables:

- `ExecutionAdapter` interface;
- Freqtrade adapter;
- runtime provision/start/pause/stop/health reconciliation;
- private runtime addressing;
- readiness gates;
- runtime credential injection abstraction;
- per-runtime correlation/log identity;
- dry-run-only initial policy.

Acceptance:

- one test BotInstance can reconcile to one isolated dry-run runtime;
- browser/public route cannot reach Freqtrade;
- restart does not change pinned config/model/strategy identity;
- readiness uses explicit health/state, not fixed sleeps;
- failure produces machine-readable observed state.

## P4 — Data, events and observability

Status: `planned`

Goal: make cross-plane activity attributable and queryable.

Deliverables:

- NATS JetStream event transport;
- transactional outbox/inbox patterns;
- correlation/causation IDs;
- OpenTelemetry instrumentation;
- structured log/redaction policy;
- normalized trade mirror/reconciliation;
- object-storage artifact interface;
- baseline metrics/dashboards.

Acceptance:

- a bot lifecycle flow is traceable end-to-end by correlation ID;
- duplicate event delivery is safe;
- secrets are absent from telemetry;
- mirrored trade data exposes staleness/reconciliation state.

## P5 — AI/model lifecycle control integration

Status: `planned`

Goal: connect the portal to immutable research/model lifecycle metadata without creating a shortcut around validation.

Deliverables:

- ModelVersion registry API/read model;
- DatasetVersion/FeatureSchemaVersion metadata contracts;
- training request/job metadata;
- validation-gate representation;
- model assignment to BotConfigRevision;
- explicit promotion/rollback workflow skeleton;
- model health status API.

Acceptance:

- running bot references one immutable model version;
- candidate training cannot mutate active assignment;
- promotion is audited and capability-gated;
- protected holdout and completed Phase 6 boundaries remain unchanged.

## P6 — Portal web shell and core operations UI

Status: `planned`

Goal: deliver the first modern user-facing control surface.

Deliverables:

- Next.js/React application shell;
- authentication/session integration;
- dashboard;
- bot list/detail;
- Create Bot wizard for dry-run-supported templates;
- exchange connection metadata management;
- runtime health/log views;
- profile/security/notifications shell;
- responsive design system.

Acceptance:

- browser communicates only with portal API;
- environment badge is always visible;
- dry-run is the only deployable trading state in this stage;
- critical user journey passes Chromium E2E;
- tenant/RBAC denial states are rendered correctly.

## P7 — Risk Engine and Trading Terminal

Status: `planned`

Goal: put deterministic policy between every manual/AI trade intent and execution.

Deliverables:

- versioned risk policy model;
- TradeIntent/ApprovedTradeIntent/RejectedTradeIntent contracts;
- initial exposure/loss/drawdown/health gates;
- terminal intent API/UI;
- kill switches;
- audit and reason codes.

Acceptance:

- AI/manual intent cannot bypass risk evaluation;
- denied intents are attributable and visible;
- kill switch blocks new exposure;
- terminal has no direct exchange/Freqtrade path;
- security E2E covers unauthorized terminal actions.

## P8 — Post-Trade Intelligence

Status: `planned`

Goal: capture decision black-box evidence and explain trade outcomes without overclaiming causality.

Deliverables:

- DecisionSnapshot;
- TradeOutcome normalization;
- evidence assembler;
- deterministic diagnosis layer;
- AI-assisted synthesis boundary;
- Trade Analysis UI;
- Insights UI;
- counterfactual offline analysis framework;
- Trading Knowledge Base schema.

Acceptance:

- loss is not automatically classified as model error;
- every diagnosis links evidence and versions;
- LLM output cannot overwrite deterministic evidence;
- analysis failure cannot affect execution;
- no analysis automatically mutates production bot/model configuration.

## P9 — Safe continual-learning workflow

Status: `planned`

Goal: allow live/dry-run evidence to create reproducible learning candidates.

Deliverables:

- curated learning dataset pipeline;
- insight -> hypothesis -> experiment workflow;
- scheduled/triggered training request policy;
- champion/challenger comparison workflow;
- candidate registration;
- explicit autonomy levels L0-L4;
- Learning History UI.

Acceptance:

- bad trade can trigger experiment proposal, not direct model mutation;
- candidate creation never implies promotion;
- evidence windows are declared and protected-boundary aware;
- negative experiments remain durable.

## P10 — Deterministic exchange simulator and universal E2E

Status: `planned`

Goal: test the complete system with realistic user and exchange behavior without real capital.

Deliverables:

- deterministic market/exchange simulator;
- scenario manifest format;
- Playwright full-platform harness;
- critical browser journey;
- AI learning-loop scenario;
- security E2E;
- failure evidence bundle;
- visual acceptance baseline.

Acceptance:

- E2E creates bot, executes simulated trade, reconciles PNL and produces trade analysis;
- candidate training test proves active model does not change automatically;
- first failure evidence is preserved;
- test system uses explicit readiness gates.

## P11 — Cloudflare production-like staging

Status: `planned`

Goal: validate the platform through the real protected external ingress path.

Deliverables:

- dedicated Cloudflare Tunnel;
- WAF/rate-limit policy set;
- Access policies for privileged surfaces;
- staging service identities;
- origin exposure verification;
- Cloudflare-path E2E;
- secret rotation runbook;
- incident/kill-switch runbooks.

Acceptance:

- origin/Freqtrade direct public access is denied;
- privileged surfaces require expected Zero Trust policy;
- automated staging E2E authenticates without a security bypass endpoint;
- exchange execution remains simulated by default.

## P12 — Autonomous diagnosis and bounded repair

Status: `planned`

Goal: let agents diagnose reproducible failures and prepare safe fixes autonomously.

Deliverables:

- failure triage schema;
- evidence-to-diagnosis workflow;
- regression-test-first repair policy;
- owned-path/task enforcement;
- isolated branch creation;
- targeted/full validation routing;
- PR generation with evidence;
- unsafe repair detection.

Acceptance:

- agent can repair a seeded non-security defect and produce a passing PR;
- agent cannot weaken a mandatory safety assertion;
- agent cannot deploy production or access production exchange secrets;
- all actions are attributable to task/agent identity.

## P13 — Scale and service extraction

Status: `planned`

Goal: scale only where measured requirements justify complexity.

Possible work:

- Kubernetes runtime scheduling;
- dedicated workflow engine;
- shared inference service;
- separate trade-intelligence service;
- partitioned event/data infrastructure;
- multi-region design.

Acceptance is defined prospectively from observed bottlenecks/SLOs. This stage must not be implemented merely for architectural fashion.

## P14 — Live-small readiness

Status: `blocked`

Blocker: explicit owner approval and successful completion of the existing AI Platform lifecycle requirements plus portal security/operations evidence.

This program does not authorize live capital.

Required before any implementation:

- separate work package;
- withdrawal-disabled production exchange credentials;
- strict capital limits;
- security review;
- sustained dry-run evidence;
- emergency procedures;
- rollback;
- monitoring/alerting;
- independently reviewed model/strategy eligibility.

## Dependency summary

```text
P0
 |
 v
P1 -----> P2 -----> P3 -----> P4
 |          |         |         |
 |          |         |         +----> P8 ----> P9
 |          |         |
 |          |         +--------------> P7
 |          |
 |          +------------------------> P6
 |
 +-----------------------------------> P10

P3 + P4 + P6 + P7 + P8 + P10 ----> P11 ----> P12

P13 only after measured need
P14 remains separately blocked/authorized
```

Parallel work is allowed only where owned paths and contracts are disjoint and dependencies are satisfied.
