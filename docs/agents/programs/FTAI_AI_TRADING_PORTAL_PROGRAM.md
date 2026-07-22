# FTAI AI Trading Portal Program

## Program ID

`FTAI-PROGRAM-AI-TRADING-PORTAL`

## Status

`architecture-foundation-active`

## Mission

Build a secure, modern and extensible portal above the existing Freqtrade AI Platform that can manage dry-run bot runtimes, model lifecycle, deterministic risk, post-trade intelligence, safe continual learning, Cloudflare-protected access and autonomous full-platform validation.

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
- `docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md`

Task-specific agents read additional portal documents only when relevant.

## Program invariants

- Freqtrade is an internal execution engine, not a public portal backend.
- Browser traffic never talks directly to Freqtrade or exchanges.
- AI predictions are not unrestricted execution authority.
- Deterministic risk gates can veto trade intent.
- Exchange credentials are stored behind a secret boundary and never committed.
- Withdrawal permission remains disabled.
- Research workers cannot access production exchange credentials.
- Models/configs/risk policies used for decisions are immutable and attributable.
- Post-trade analysis may create insights/experiments/candidates, not immediate production mutation.
- Autonomous repair creates regression tests, branches and PRs; it does not patch production.
- Live capital requires a separate explicit reviewed work package.

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

Canonical stage order is defined in `docs/ai_platform/portal/DELIVERY_ROADMAP.md`.

First implementation task after architecture merge:

`FTAI-YYYYMMDD-portal-p1-contracts-security`

It must freeze machine-readable domain/security contracts before downstream control/execution implementation.

## Parallelization policy

After P1 contracts merge, P2/P3/P4/P5 and simulator-core work may proceed in parallel if owned paths remain disjoint.

Shared contract changes are serialized through a dedicated contract-change task.

## Quality policy

Every implementation workstream adds tests at its layer. Full-platform acceptance eventually includes:

- unit/contract/integration;
- security E2E;
- Playwright browser E2E;
- deterministic exchange simulator;
- AI learning-loop E2E;
- visual/responsive acceptance;
- chaos/recovery scenarios;
- bounded autonomous diagnosis/repair.

## Security posture

Target ingress:

```text
Internet -> Cloudflare -> Tunnel -> Portal
```

Privileged surfaces add Zero Trust/Access policy. Freqtrade remains private.

Staging E2E traverses the real protected ingress path without a hidden security bypass and uses simulated capital by default.

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

## Next action

After this architecture package is reviewed and merged, declare and execute `FTAI-YYYYMMDD-portal-p1-contracts-security` from current `develop`, using the ownership and boundaries in `AGENT_EXECUTION_PLAN.md`.
