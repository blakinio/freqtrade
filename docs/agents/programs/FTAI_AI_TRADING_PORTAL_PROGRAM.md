# FTAI AI Trading Portal Program

## Program ID

`FTAI-PROGRAM-AI-TRADING-PORTAL`

## Status

`production-like-staging-blocked`

## Mission

Build a secure, modern and extensible portal above the existing Freqtrade AI Platform that can manage dry-run bot runtimes, model lifecycle, deterministic risk, post-trade intelligence, safe continual learning, Cloudflare-protected access and autonomous full-platform validation.

## Current program state

Repository-backed implementation has progressed through P12 simulation-first acceptance and the remaining software-addressable portal product surfaces merged in PR #232.

Canonical stage status is maintained in `docs/ai_platform/portal/DELIVERY_ROADMAP.md`:

- P0-P10 are complete for their declared bounded acceptance criteria;
- P11 repository-side staging contracts, verifier, workflows and runbooks are complete, but real Cloudflare/protected GitHub External E2E remains blocked/deferred and production-like staging is not accepted;
- P12 simulation-first autonomous diagnosis/repair acceptance is complete and is not a substitute for P11;
- P13 measured-need assessment completed with NO-GO, so scale/service extraction is deferred until evidence demonstrates a need;
- P14 remains separately blocked and this program does not authorize live capital.

The remaining authoritative-source, private-runtime, identity, observability and provider integrations are canonically ordered in `docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md` as PI-01 through PI-08. PI-01 and PI-03 are complete; PI-04 is the active bounded package. Other packages remain planning-only until separately declared.

Current execution is also intentionally incomplete for real trading: the deterministic risk-gated terminal exists, but the concrete `FreqtradeExecutionAdapter.submit_approved_intent` path remains fail-closed with `ORDER_SUBMISSION_NOT_IMPLEMENTED`. P10 provides deterministic simulated execution only.

## Source of truth

In order:

1. current repository/Git/PR/CI state;
2. `AGENTS.md`;
3. existing AI Platform lifecycle/evidence records;
4. portal architecture documents under `docs/ai_platform/portal/`;
5. active bounded task record and its context checkpoint.

Chat history and private UI captures are not durable program state.

## Required reads

- `AGENTS.md`
- `docs/agents/CONTEXT_HANDOFF.md`
- `docs/ai_platform/ARCHITECTURE.md`
- `docs/ai_platform/ROADMAP.md`
- `docs/ai_platform/portal/README.md`
- `docs/ai_platform/portal/SYSTEM_ARCHITECTURE.md`
- `docs/ai_platform/portal/SECURITY_ARCHITECTURE.md`
- `docs/ai_platform/portal/DELIVERY_ROADMAP.md`
- `docs/ai_platform/portal/POST_P12_INTEGRATION_BACKLOG.md`
- `docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md`

Task-specific agents read additional portal documents only when relevant.

## Program invariants

- Freqtrade is an internal execution engine, not a public portal backend.
- Browser traffic never talks directly to Freqtrade or exchanges.
- Portal execution reaches Freqtrade only through a controlled private adapter boundary.
- AI predictions are not unrestricted execution authority.
- Every execution intent is subject to deterministic risk gates before it may reach an execution submitter.
- Exchange credentials are stored behind a secret boundary and never committed.
- Withdrawal permission remains disabled.
- Research workers cannot access production exchange credentials.
- Models/configs/strategies/risk policies used for decisions are immutable and attributable.
- Post-trade analysis may create insights/experiments/candidates, not immediate production mutation.
- Autonomous repair creates regression tests, branches and PRs; it does not patch production.
- Live capital requires a separate explicit reviewed work package.
- Repository or simulated P11 evidence cannot be represented as real Cloudflare production-like staging acceptance.
- A planned PI package is not active and cannot be used as completion evidence until its separate task and acceptance gates pass.

## Protected existing AI boundaries

This program cannot change:

- frozen `entry_prediction_threshold = 0.006`;
- frozen `exit_prediction_threshold = -0.009`;
- protected final holdout v2 `20260801-20260930` or its authorization date;
- completed Phase 6 candidates/policy/evidence;
- authoritative Phase 6 `selected_model = null`;
- historical PyTorch/RL evidence status.

Any future work affecting those boundaries requires a separately declared research work package governed by the existing AI Platform lifecycle.

## Program architecture

Six planes:

1. Portal / UX Plane
2. Control Plane
3. Execution Plane
4. AI / Research Plane
5. Data Plane
6. Quality & Autonomous Validation Plane

Cross-cutting:

- Security;
- Risk;
- Observability.

## Delivery sequence

Canonical stage order, current statuses and acceptance boundaries are defined in `docs/ai_platform/portal/DELIVERY_ROADMAP.md`.

The historical first implementation task after architecture merge was `FTAI-20260722-portal-p1-contracts-security`. That sequence has now progressed through completed P12 simulation-first acceptance; it is no longer the program's next software action.

Post-P12 continuation is governed by `POST_P12_INTEGRATION_BACKLOG.md`. Read-only PI-01 and aggregate-only PI-03 are complete. PI-04 Centralized Runtime Observability is active; PI-06 may run in parallel only when ownership is disjoint and shared contract changes are serialized. PI-07 must precede PI-08; neither authorizes live capital.

## Parallelization policy

Shared contract changes are serialized through a dedicated contract-change task. New work must inspect current `develop`, open PRs and active task ownership before editing shared paths.

Every PI package requires its own dated task, branch, exact owned paths, authoritative source definition, fail-closed states and acceptance evidence. Adjacent PI packages must not be silently combined because their security and capital risks differ.

P13 scale/service extraction remains deferred unless measured bottleneck/SLO evidence justifies a separately declared work package.

## Quality policy

Every implementation workstream adds tests at its layer. Full-platform acceptance includes, as applicable:

- unit/contract/integration;
- security E2E;
- Playwright browser E2E;
- deterministic exchange simulator;
- AI learning-loop E2E;
- visual/responsive acceptance;
- chaos/recovery scenarios;
- bounded autonomous diagnosis/repair.

Simulation/local/CI evidence must remain labeled as such. Real production-like staging acceptance requires the real protected external ingress path.

## Security posture

Target ingress:

```text
Internet -> Cloudflare -> Tunnel -> Portal
```

Privileged surfaces add Zero Trust/Access policy. Freqtrade remains private.

Staging E2E must traverse the real protected ingress path without a hidden security bypass and uses simulated capital by default.

The current P11 blocker is external: owner-approved Cloudflare Tunnel/DNS/Access/WAF/rate-limit/origin-denial state plus protected GitHub staging variables/secrets must be provisioned or confirmed and the real External E2E workflow must pass. Repository-side P11 implementation alone is not acceptance.

## Product surface

Canonical navigation is defined in `docs/ai_platform/portal/UI_INFORMATION_ARCHITECTURE.md` and includes:

- Dashboard;
- PNL & Performance;
- Open Positions;
- Trading Terminal;
- Bots/Create Bot/Signal Wizard/Strategy Catalog/Grid Bots;
- AI Intelligence/Trade Analysis/Insights/Model Health/Experiments/Learning History;
- Operations/Logs/Risk/Runtime Health/Audit;
- Exchange Connections/Profile/Security/Notifications/Admin.

Third-party private captures are inspiration/evidence only and must not be copied into public product code with personal data or proprietary assets.

## Completion definition

The program reaches its first major completion milestone when a production-like staging deployment can:

1. authenticate a test user through the protected ingress path;
2. create a tenant-scoped dry-run AI bot;
3. provision an isolated Freqtrade runtime privately;
4. execute a deterministic simulated trade through risk gates;
5. reconcile PNL and execution evidence;
6. produce a post-trade analysis and AI insight;
7. create a bounded learning experiment/candidate without changing the active model;
8. pass critical browser/security/AI E2E;
9. generate an autonomous evidence-based repair PR for a seeded defect;
10. prove no public Freqtrade exposure and no live-capital authorization.

Repository-side and simulation-first evidence already cover many of these software boundaries, but the milestone is **not complete** until real P11 protected external ingress acceptance passes.

## Next actions by authorization lane

Next autonomous software action: complete and merge active PI-04 with private tenant-scoped log search, explicit source availability, OpenTelemetry-compatible routing, bounded retention/query policy and no audit or execution-authority conflation. Select the next package only after PI-04 durable completion evidence is merged.

Next owner/external action: when the owner intentionally starts the real infrastructure phase, resume P11, provision or confirm the owner-approved Cloudflare staging resources and protected GitHub staging environment, then run `Portal Staging External E2E` until all five real ingress, Access and direct-denial probes pass.

Do not start P14 or enable live capital as part of either action.
