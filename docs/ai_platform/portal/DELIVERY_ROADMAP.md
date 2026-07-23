# AI Trading Portal — Delivery Roadmap

## 1. Program boundary

This roadmap is a **parallel portal/platform program**, not a renumbering of the existing AI research phases.

It must not:

- alter the frozen Phase 5 thresholds;
- consume the protected final holdout iteratively;
- reopen completed Phase 6 model selection;
- change authoritative Phase 6 `selected_model = null`;
- reinterpret PyTorch/RL evidence as production approval;
- enable live capital implicitly.

Each stage lands as a bounded work package or small series of reviewable PRs. Repository, Git, PR, CI, task records and current code are the source of truth for status.

Status values:

- `planned` — declared but not started;
- `active` — currently being implemented;
- `blocked` — declared acceptance cannot progress without a real dependency or authorization;
- `done` — the stage's declared acceptance criteria are satisfied;
- `deferred` — intentionally not being implemented until a prospective trigger or measured need exists.

## 2. Canonical current status

| Stage | Status | Current repository-backed state |
| --- | --- | --- |
| P0 — Architecture and governance foundation | `done` | Architecture/program foundation merged in PR #113. |
| P1 — Domain contracts and security foundation | `done` | Contracts/security foundation merged in PR #114. |
| P2 — Control Plane core | `done` | Bounded control-plane core merged in PR #116. |
| P3 — Freqtrade execution adapter and bot orchestrator | `done` | Declared dry-run runtime lifecycle scope merged in PR #118; real order submission and portfolio/trade queries remain intentionally fail-closed. |
| P4 — Data, events and observability | `done` | Data/observability foundation merged in PR #119 and durable handoff finalized in PR #120. |
| P5 — AI/model lifecycle control integration | `done` | Model lifecycle control merged in PR #124 without changing research selection boundaries. |
| P6 — Portal web shell and core operations UI | `done` | Web shell merged in PR #135 and task closeout merged in PR #136. |
| P7 — Risk Engine and Trading Terminal | `done` | Deterministic risk core merged in PR #137 and fail-closed terminal integration merged in PR #143. |
| P8 — Post-Trade Intelligence | `done` | Bounded trade-intelligence foundation merged in PR #147. |
| P9 — Safe continual-learning workflow | `done` | Safe continual-learning workflow merged in PR #158. |
| P10 — Deterministic exchange simulator and universal E2E | `done` | Deterministic simulator/universal E2E merged in PR #171 and task closeout in PR #176. |
| P11 — Cloudflare production-like staging | `blocked` | Repository-side staging contract/verifier/workflows/runbooks are complete; real protected external ingress acceptance is still deferred and unproven. |
| P12 — Autonomous diagnosis and bounded repair | `done` | Simulation-first foundation and seeded non-security repair acceptance completed; this does not satisfy P11. |
| P13 — Scale and service extraction | `deferred` | Measured-need assessment completed in PR #224 with NO-GO: no bottleneck/SLO evidence justifies extraction or new scale infrastructure. |
| P14 — Live-small readiness | `blocked` | Requires explicit owner approval plus separate lifecycle, security and operations evidence. This program does not authorize live capital. |

## 3. Current execution reality

The implemented manual intent path is:

```text
Browser
  -> same-origin Portal BFF/API
  -> tenant-scoped Control Plane lookup
  -> trusted server-side RiskEvaluationSnapshot provider
  -> deterministic Risk Engine
  -> ApprovedExecutionIntent | RejectedExecutionIntent
  -> ApprovedIntentSubmitter boundary
```

The current concrete Freqtrade path stops fail-closed at the final boundary:

```text
ApprovedExecutionIntent
  -> FreqtradeExecutionAdapter.submit_approved_intent(...)
  -> ORDER_SUBMISSION_NOT_IMPLEMENTED
```

Current facts:

- `ExecutionMode` contains only `simulated` and `dry_run`;
- P3 `FreqtradeExecutionAdapter` accepts only `dry_run` for runtime lifecycle;
- P3 can provision/start/pause/stop/inspect private Freqtrade containers with immutable runtime identity;
- P3 `submit_approved_intent`, `get_open_positions`, `get_orders` and `get_trades` remain unsupported and fail closed;
- P7 rejects risk-denied intents before execution and surfaces unsupported approved submission as terminal state `BLOCKED`;
- P10 provides a deterministic `simulated` execution path that accepts only `ApprovedExecutionIntent` and creates simulator orders/trade outcomes;
- P10 simulator evidence is not proof of a real Freqtrade order-submission path;
- no contract currently represents live-capital execution mode.

Therefore the current production-like execution chain is **not**:

```text
Portal -> Control Plane -> Risk -> ApprovedExecutionIntent -> Freqtrade -> Exchange
```

as a functional order-submission path. The first four boundaries exist, but the concrete private risk-approved submission transport into Freqtrade remains unimplemented.

Before any separately authorized real-trading work could be considered, at minimum a bounded work package would need to implement and validate:

1. a private authenticated `ApprovedExecutionIntent` submission transport to Freqtrade without public exposure;
2. real order/position/trade query and reconciliation behavior at the adapter boundary;
3. trusted runtime-derived risk snapshot inputs for the real execution path;
4. production-grade exchange credential retrieval/injection with withdrawal disabled and research isolation;
5. lifecycle eligibility and explicit live-capital authorization rather than a new default mode;
6. production-like P11 external staging acceptance, sustained dry-run evidence, monitoring, incident/kill-switch and rollback evidence required by P14.

None of those real-trading gaps are implemented by this roadmap-sync task.

## 4. P0 — Architecture and governance foundation

Status: `done`

Goal: freeze architectural boundaries and agent work ownership before implementation.

Delivered:

- portal program overview;
- system, security, AI/ML, data/observability, E2E and UI architecture;
- delivery roadmap and agent execution plan;
- portal/control-plane safety boundaries in `AGENTS.md`.

Evidence: PR #113 merged the architecture and agent-program foundation.

## 5. P1 — Domain contracts and security foundation

Status: `done`

Goal: establish fail-closed domain/API/event/security contracts before product workflows.

Delivered in PR #114:

- tenant/actor/resource identity and capability vocabulary;
- BotInstance/BotConfigRevision contracts;
- model/risk/execution contracts;
- event/audit/secret-reference boundaries;
- only `simulated` and `dry_run` execution modes;
- private `ExecutionAdapter` accepting only `ApprovedExecutionIntent` for submission;
- no live-capital default or withdrawal capability.

## 6. P2 — Control Plane core

Status: `done`

Goal: implement the first modular backend control plane without public Freqtrade coupling.

Delivered in PR #116:

- tenant-scoped control-plane persistence/service/API foundation;
- immutable revisions and desired/observed state separation;
- capability gating, audit and transactional outbox behavior;
- no raw exchange/Freqtrade credentials or public runtime route.

## 7. P3 — Freqtrade execution adapter and bot orchestrator

Status: `done`

Goal: safely manage isolated dry-run Freqtrade runtimes through a private adapter.

Declared stage acceptance delivered in PR #118:

- deterministic one-bot/one-runtime identity;
- isolated workspaces and immutable config/artifact identity;
- dry-run-only configuration enforcement;
- Docker create/start/pause/stop/inspect lifecycle;
- explicit health/error mapping and correlation metadata;
- no published Freqtrade control port.

Important boundary:

P3 completion covers runtime lifecycle, not real trading submission. `submit_approved_intent` and position/order/trade queries remain deliberately fail-closed. This is a known later execution-integration gap, not evidence that P3 lifecycle acceptance failed.

## 8. P4 — Data, events and observability

Status: `done`

Goal: make cross-plane activity attributable and safely consumable.

Delivered through PR #119 with durable handoff in PR #120:

- outbox publication and idempotent inbox/consumer foundation;
- correlation/causation propagation;
- structured observability/redaction foundations;
- no deployment claim for external NATS/Prometheus/Grafana infrastructure.

## 9. P5 — AI/model lifecycle control integration

Status: `done`

Goal: connect portal control to immutable model lifecycle metadata without bypassing validation.

Delivered in PR #124:

- immutable tenant-scoped model registration;
- promotion/rollback history and explicit eligibility checks;
- separation between registration and activation;
- BotConfigRevision remains the immutable concrete model assignment;
- no automatic model activation, research retuning or protected-holdout use.

Authoritative Phase 6 `selected_model = null` remains unchanged.

## 10. P6 — Portal web shell and core operations UI

Status: `done`

Goal: deliver the first modern user-facing dry-run control surface.

Delivered in PR #135 with closeout PR #136:

- responsive Next.js/React/TypeScript shell;
- same-origin BFF boundary;
- dashboard/bot/create-bot/runtime surfaces in the declared shell scope;
- environment visibility and browser security boundaries;
- Chromium E2E for the declared critical journey.

The browser still has no direct Freqtrade or exchange path.

## 11. P7 — Risk Engine and Trading Terminal

Status: `done`

Goal: put deterministic policy between every manual/AI trade intent and execution.

Delivered:

- P7.1 deterministic risk core in PR #137;
- P7.2 terminal API/UI integration in PR #143.

Acceptance state:

- rejected intents cannot reach execution;
- approved intents can reach only an injected `ApprovedIntentSubmitter` boundary;
- browser-supplied risk snapshots are rejected;
- kill-switch and policy gates are deterministic and attributable;
- the default real execution submitter remains fail-closed with `ORDER_SUBMISSION_NOT_IMPLEMENTED`.

P7 completion therefore proves the risk-gated terminal flow, not real Freqtrade/exchange order submission.

## 12. P8 — Post-Trade Intelligence

Status: `done`

Goal: capture decision evidence and explain outcomes without overclaiming causality.

Delivered in PR #147:

- immutable DecisionSnapshot/TradeOutcome separation;
- tenant-scoped evidence and analysis persistence;
- deterministic diagnosis before optional AI synthesis;
- evidence-linked analysis that cannot mutate execution state.

## 13. P9 — Safe continual-learning workflow

Status: `done`

Goal: turn validated observations into reproducible learning candidates without automatic promotion.

Delivered in PR #158:

- durable Insight -> Hypothesis -> Experiment -> Candidate provenance;
- explicit autonomy levels;
- protected-holdout exclusion;
- durable negative experiments;
- candidate creation that does not mutate active model assignment or imply promotion.

## 14. P10 — Deterministic exchange simulator and universal E2E

Status: `done`

Goal: test the integrated portal/risk/intelligence/learning flow with deterministic simulated capital.

Delivered in PR #171 with closeout PR #176:

- deterministic market/exchange simulator;
- scenario manifests and failure evidence;
- universal backend scenario;
- Chromium portal journey;
- simulated trade, synchronized PNL outcome, P8 analysis and bounded P9 candidate;
- proof that candidate creation does not change the active model;
- explicit readiness and first-failure preservation.

Important boundary:

The P10 simulator directly implements the `ApprovedExecutionIntent` submitter contract for deterministic simulated orders. It does not make `FreqtradeExecutionAdapter.submit_approved_intent` functional and does not prove real external ingress.

## 15. P11 — Cloudflare production-like staging

Status: `blocked`

Goal: validate the platform through the real protected external ingress path while execution remains simulated by default.

### A. Repository-side foundation — delivered

Merged in PR #180 and preserved by durable blocker/handoff records in PRs #181, #203, #204, #205 and #215:

- fail-closed machine-readable staging ingress policy;
- Tunnel-required contract;
- direct public origin and direct public Freqtrade forbidden by policy;
- explicit Access and WAF/rate-limit coverage families;
- read-only external verifier for five real probes;
- protected GitHub `Portal Staging External E2E` workflow contract;
- static staging-policy validation workflow;
- staging secret-rotation runbook;
- staging incident/kill-switch runbook;
- execution fixed to simulated mode for staging acceptance.

The verifier is designed to prove:

1. public portal reachability through the protected route;
2. anonymous denial on Access-protected privileged surfaces;
3. successful authorized staging service-identity access;
4. direct-origin denial;
5. direct-Freqtrade denial.

### B. Real external infrastructure and acceptance — still required

The repository cannot truthfully mark P11 `done` until owner-approved real infrastructure exists or is confirmed and the external workflow passes. Required external state includes:

- Cloudflare Tunnel and its origin routing;
- authoritative/proxied DNS for the staging route;
- WAF policy deployment;
- rate-limiting policy deployment;
- Cloudflare Access/Zero Trust policies for privileged surfaces;
- dedicated staging service identity/service credentials;
- origin firewall/network policy that prevents direct bypass;
- protected GitHub staging environment;
- required protected environment variables and secrets;
- a successful real `Portal Staging External E2E` run covering all five probes.

Current durable blocker:

The owner explicitly deferred real Cloudflare/protected GitHub staging provisioning and verification until the software platform is otherwise ready. Repository CI, mocks, deterministic simulation and P12 evidence cannot substitute for this gate.

## 16. P12 — Autonomous diagnosis and bounded repair

Status: `done`

Goal: let agents diagnose reproducible failures and prepare safe fixes without production authority.

Simulation-first sequencing was explicitly authorized while P11 remains externally blocked.

Delivered through the recovered foundation PR #221, seeded repair acceptance PR #222 and closeout PR #223:

- typed failure diagnosis;
- reproducibility requirement;
- regression-test-first repair policy;
- owned-path enforcement;
- unsafe-repair rejection;
- isolated repair branch/PR metadata;
- seeded deterministic simulator defect reproduced, diagnosed, regression-tested, minimally repaired and validated.

P12 completion is **simulated/non-production evidence only** and does not satisfy real P11 External E2E.

## 17. P13 — Scale and service extraction

Status: `deferred`

Goal: scale only where measured requirements justify added complexity.

Measured-need assessment completed in PR #224 with a NO-GO decision:

- no current latency, throughput, saturation, capacity, error-budget or SLO evidence demonstrates a scale bottleneck;
- no approved service-extraction decision exists;
- real P11 infrastructure provisioning alone would not prove a need for P13;
- the modular-monolith/runtime architecture remains the correct baseline.

No Kubernetes scheduling, dedicated workflow engine, shared inference service, separate trade-intelligence service, partitioned data infrastructure or multi-region design is authorized merely because earlier stages are complete.

A future P13 declaration requires a durable measurement bundle identifying the bottleneck/SLO, workload/window, quantified impact, alternatives, smallest justified change, validation and rollback criteria.

## 18. P14 — Live-small readiness

Status: `blocked`

Blocker: explicit owner approval and successful completion of the applicable AI Platform lifecycle requirements plus portal security/operations evidence.

This program does not authorize live capital.

Required before any implementation:

- a separate explicitly reviewed work package;
- withdrawal-disabled production exchange credentials separated from research;
- strict capital and loss limits;
- production security review;
- sustained dry-run evidence;
- emergency procedures and kill switches;
- rollback procedures;
- monitoring and alerting;
- independently reviewed model/strategy eligibility;
- production-like staging evidence appropriate to the change.

No work package may silently cross from `simulated`/`dry_run` into real trading.

## 19. Dependency and acceptance summary

```text
P0 -> P1 -> P2/P3/P4/P5 -> P6/P7/P8 -> P9 -> P10
                                             |
                                             v
                           P11 repository-side foundation (done)
                                             |
                                             +--> P12 simulation-first (done)
                                             |
                                             v
                           P11 real External E2E (blocked/deferred)
                                             |
                                             v
                         production-like staging acceptance

P13 -> deferred until measured need
P14 -> separately blocked pending owner approval and full lifecycle/security/operations evidence
```

P12 simulation-first does not satisfy P11. P13 NO-GO does not block P11. P11 completion does not automatically authorize P14.

## 20. Exactly one next program-level action

When the owner intentionally starts the real infrastructure phase, resume P11: provision or confirm the owner-approved Cloudflare staging resources and protected GitHub staging environment, then run `Portal Staging External E2E` until all five real ingress, Access and direct-denial probes pass.
