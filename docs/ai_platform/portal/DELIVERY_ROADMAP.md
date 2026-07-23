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
- `deferred`

## P0 — Architecture and governance foundation

Status: `done`

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

Merged evidence: architecture and agent-program foundation landed in PR #113.

## P1 — Domain contracts and security foundation

Status: `done`

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

Merged evidence: P1 contracts and security foundation landed in PR #114.

## P2 — Control Plane core

Status: `done`

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

Merged evidence: bounded P2 Control Plane core landed in PR #116.

## P3 — Freqtrade execution adapter and bot orchestrator

Status: `done`

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

Merged evidence: the declared P3 dry-run runtime-lifecycle scope landed in PR #118.

Current boundary: P3 completion does not mean real order submission exists. `FreqtradeExecutionAdapter.submit_approved_intent`, position queries, order queries and trade queries remain fail-closed; `submit_approved_intent` raises `ORDER_SUBMISSION_NOT_IMPLEMENTED`.

## P4 — Data, events and observability

Status: `done`

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

Merged evidence: P4 data/observability foundation landed in PR #119 and its durable handoff was finalized in PR #120.

## P5 — AI/model lifecycle control integration

Status: `done`

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

Merged evidence: P5 model lifecycle control landed in PR #124 without changing authoritative Phase 6 `selected_model = null` or protected research boundaries.

## P6 — Portal web shell and core operations UI

Status: `done`

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

Merged evidence: P6 web shell landed in PR #135 and its durable closeout landed in PR #136.

## P7 — Risk Engine and Trading Terminal

Status: `done`

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

Merged evidence: P7 deterministic risk core landed in PR #137 and the fail-closed terminal integration landed in PR #143.

Current boundary: the terminal sends approved decisions only to an injected `ApprovedExecutionIntent` submitter. The default concrete Freqtrade submitter still returns `ORDER_SUBMISSION_NOT_IMPLEMENTED`, surfaced as terminal state `BLOCKED`; P7 therefore proves the deterministic risk-gated terminal flow, not real Freqtrade/exchange order submission.

## P8 — Post-Trade Intelligence

Status: `done`

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

Merged evidence: bounded P8 trade-intelligence foundation landed in PR #147.

## P9 — Safe continual-learning workflow

Status: `done`

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

Merged evidence: bounded P9 safe continual-learning workflow landed in PR #158.

## P10 — Deterministic exchange simulator and universal E2E

Status: `done`

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

Merged evidence: P10 deterministic simulator/universal E2E landed in PR #171 and its closeout landed in PR #176.

Current boundary: P10's deterministic simulator implements the approved-intent submitter for simulated orders. It does not make `FreqtradeExecutionAdapter.submit_approved_intent` functional and is not evidence of real Freqtrade order submission.

## P11 — Cloudflare production-like staging

Status: `blocked`

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

Repository-side P11 contracts, verifier, workflow and runbooks are complete while this stage remains blocked on real owner-approved external infrastructure. The owner explicitly deferred provisioning/verification of the real Cloudflare and protected GitHub staging environment until the software platform is otherwise ready. This deferral does not waive any P11 acceptance criterion.

Repository-side evidence: PR #180 merged the fail-closed staging policy, five-probe external verifier, protected staging workflow and runbooks. Durable P11 blocker/handoff records were subsequently maintained through PRs #181, #203, #204, #205 and #215.

Exact remaining external gate: provision or confirm the owner-approved Cloudflare Tunnel, proxied DNS, WAF, rate limiting, Access/Zero Trust, staging service identity and direct-origin network denial; configure the protected GitHub staging environment variables/secrets; then pass real `Portal Staging External E2E` for public portal reachability, anonymous Access denial, service-identity access, direct-origin denial and direct-Freqtrade denial.

## P12 — Autonomous diagnosis and bounded repair

Status: `done`

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

Simulation-first sequencing is authorized once deterministic P10 failure evidence bundles and repository-side P11 staging/security contracts are stable. This mode may use local, simulator and CI evidence, but it must label that evidence as simulated/non-production and cannot claim that real Cloudflare ingress or production-like staging acceptance has been proven.

Acceptance:

- agent can repair a seeded non-security defect and produce a passing PR;
- agent cannot weaken a mandatory safety assertion;
- agent cannot deploy production or access production exchange secrets;
- all actions are attributable to task/agent identity.

Simulation-first P12 acceptance completed through the recovered fail-closed foundation and a seeded deterministic simulator repair exercise. The temporary defect was reproduced, diagnosed, regression-tested before repair, minimally fixed and validated through required CI; only durable regression/evidence artifacts were merged. This completion does not satisfy or replace the deferred real P11 External E2E gate.

## P13 — Scale and service extraction

Status: `deferred`

Goal: scale only where measured requirements justify complexity.

Possible work:

- Kubernetes runtime scheduling;
- dedicated workflow engine;
- shared inference service;
- separate trade-intelligence service;
- partitioned event/data infrastructure;
- multi-region design.

Acceptance is defined prospectively from observed bottlenecks/SLOs. This stage must not be implemented merely for architectural fashion.

The measured-need assessment completed in PR #224 with a NO-GO decision: current repository evidence contains no qualifying latency, throughput, saturation, capacity, error-budget or SLO bottleneck that justifies service extraction or additional scale infrastructure. P13 remains deferred until a durable measurement bundle identifies a specific bottleneck or unmet SLO, quantified impact, alternatives, the smallest justified change, and validation/rollback criteria.

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

P3 + P4 + P6 + P7 + P8 + P10 ----> P11 repository-side staging contract
P10 deterministic evidence + P11 repository-side contract ----> P12 simulation-first
P11 real External E2E ------------------------------------------> production-like staging acceptance

P13 only after measured need
P14 remains separately blocked/authorized
```

Parallel work is allowed only where owned paths and contracts are disjoint and dependencies are satisfied. Simulation-first P12 does not satisfy or replace the later real P11 external acceptance gate.

## Next program-level action

When the owner intentionally starts the real infrastructure phase, resume P11 and run the real protected `Portal Staging External E2E` path until all five ingress, Access and direct-denial probes pass. Do not start P14 or enable live capital as part of that work.
