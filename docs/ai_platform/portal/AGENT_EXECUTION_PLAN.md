# AI Trading Portal — Agent Execution Plan

## 1. Purpose

Divide the portal program into bounded, resumable and mostly disjoint workstreams that autonomous agents can execute without consuming unrelated repository context or conflicting with the existing AI research program.

Repository/Git/PR/CI state is always source of truth. Every substantial implementation task follows `AGENTS.md` and `docs/agents/CONTEXT_HANDOFF.md`.

## 2. Global agent rules

Every portal agent must:

1. read `AGENTS.md`;
2. read `docs/agents/CONTEXT_HANDOFF.md`;
3. read `docs/ai_platform/portal/README.md`;
4. read only the architecture document(s) relevant to its workstream;
5. inspect current `develop`, open PRs and overlapping active tasks before editing;
6. work on a dedicated branch;
7. stay inside declared `owned_paths` unless a contract change is separately coordinated;
8. keep one compact `## Context checkpoint` in its task record;
9. run narrow validation first, then required broader gates;
10. open a PR against `develop` unless live repository state says otherwise.

All agents inherit these protected boundaries:

- do not alter frozen thresholds `0.006/-0.009`;
- do not use protected final holdout `20260801-20260930` for iterative work;
- do not reopen completed Phase 6 or change `selected_model = null`;
- do not treat PyTorch/RL evidence as promotion authorization;
- do not enable live capital;
- do not expose Freqtrade publicly;
- do not commit exchange secrets/private UI captures.

## 3. Workstream map

| Workstream | Task ID | Primary ownership | Depends on | Parallelizable after |
|---|---|---|---|---|
| Contracts + security | `FTAI-portal-p1-contracts-security` | `ai_platform/portal/contracts/**`, security contracts/docs | P0 | immediately |
| Control Plane | `FTAI-portal-p2-control-plane-core` | `ai_platform/portal/control_plane/**` | P1 core contracts | P1 contracts frozen |
| Execution adapter | `FTAI-portal-p3-execution-adapter` | `ai_platform/portal/execution/**` | P1 | P1 contracts frozen |
| Data/observability | `FTAI-portal-p4-data-observability` | `ai_platform/portal/events/**`, `ai_platform/portal/observability/**` | P1 | P1 event envelope frozen |
| Model lifecycle control | `FTAI-portal-p5-model-control` | `ai_platform/portal/model_control/**` | P1, existing registry semantics | P1 |
| Web portal | `FTAI-portal-p6-web-shell` | `ai_platform/portal/web/**` | P1 API contracts, partial P2 | stable mock contracts |
| Risk + terminal | `FTAI-portal-p7-risk-terminal` | `ai_platform/portal/risk/**` + terminal API/UI slices by coordination | P2, P3 | P2/P3 contracts |
| Trade intelligence | `FTAI-portal-p8-trade-intelligence` | `ai_platform/portal/intelligence/**` | P4, execution evidence contracts | P4 contracts |
| Learning loop | `FTAI-portal-p9-learning-loop` | `ai_platform/portal/learning/**` | P5, P8 | P5/P8 contracts |
| Simulator + universal E2E | `FTAI-portal-p10-universal-e2e` | `ai_platform/portal/simulator/**`, `ai_platform/portal/e2e/**` | P1; expands with P2-P9 | simulator can start early |
| Cloudflare staging | `FTAI-portal-p11-cloudflare-staging` | `ai_platform/portal/deploy/cloudflare/**`, staging runbooks | P3, P6, P10 | core portal deployable |
| Autonomous repair | `FTAI-portal-p12-autonomous-repair` | `ai_platform/portal/quality_agent/**`, bounded agent tooling | P10 deterministic evidence bundles, P11 repository-side contracts | deterministic evidence bundle stable |

Task IDs in individual task records should add a date prefix when declared, e.g. `FTAI-20260722-portal-p1-contracts-security`.

## 4. Recommended execution waves

### Wave A — contracts first

Run one lead agent on P1.

Do not start backend/execution implementation against unstable contracts unless work is explicitly mock-only.

P1 freezes:

- tenant/actor identifiers;
- BotInstance/BotConfigRevision schemas;
- event envelope;
- capability names;
- secret-reference contract;
- audit-event contract;
- environment/lifecycle enums.

### Wave B — parallel platform foundations

After P1 merge, run in parallel:

- P2 Control Plane;
- P3 Execution adapter;
- P4 Data/observability;
- P5 Model lifecycle control;
- P10 simulator core.

These workstreams have disjoint primary paths. Shared contract changes require a dedicated coordination PR or explicit handoff to the P1 contract owner.

### Wave C — user and policy surfaces

After stable APIs:

- P6 Web portal;
- P7 Risk + terminal;
- P8 Trade intelligence;
- expand P10 E2E.

P6 may use generated/mock API clients before all backend endpoints are complete, but production code must converge on the canonical contracts.

### Wave D — learning and production-like validation

- P9 safe continual-learning loop;
- P11 Cloudflare staging;
- complete cross-browser/security/AI E2E.

### Wave E — autonomous repair

Owner-approved sequencing exception (2026-07-23): P12 may begin in **simulation-first mode** once deterministic P10 failure evidence bundles and the repository-side P11 staging/security contracts are stable. Simulation-first P12 may diagnose seeded or reproducible local/CI defects and prepare bounded regression-test-first fixes, but simulated Cloudflare behavior is not evidence that real P11 staging acceptance passed.

Real `Portal Staging External E2E` against owner-approved Cloudflare resources remains mandatory before production-like staging can be declared complete or used as real-environment promotion evidence. P12 simulation-first work must not deploy production, mutate real external infrastructure, access production exchange secrets or enable live capital.

## 5. Agent task template

Each implementation task record should contain:

```yaml
---
task_id: FTAI-YYYYMMDD-portal-...
status: planned|active|blocked|done
branch: ...
base_branch: develop
created: YYYY-MM-DD
updated: YYYY-MM-DD
related_pr: null
owned_paths:
  - ...
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/ai_platform/portal/README.md
  - relevant architecture doc
search_first:
  - current develop and open PRs
  - overlapping active portal tasks
optional_reads:
  - only task-relevant files
---
```

Then:

```text
# Task title

## Goal
## Deliverables
## Non-negotiable boundaries
## Acceptance criteria
## Validation
## Context checkpoint
```

## 6. P1 agent brief — contracts and security

Goal:

Create machine-readable domain/security contracts and tests only. Do not implement a public portal or Freqtrade runtime management yet.

Required outputs:

- domain IDs/enums;
- BotInstance/BotConfigRevision schemas;
- capability/RBAC vocabulary;
- event envelope;
- audit schema;
- opaque SecretReference;
- environment/lifecycle enums;
- serialization tests proving secret exclusion and required tenant scope.

First acceptance gate:

> A valid tenant-owned bot command cannot be constructed without tenant, actor, target resource and environment context.

## 7. P2 agent brief — Control Plane

Goal:

Implement the smallest FastAPI modular control plane that persists tenant-scoped BotInstances and immutable revisions.

Do not integrate real exchange credentials or public Freqtrade calls.

Acceptance:

- tenant isolation;
- capability enforcement;
- immutable revisions;
- audit record;
- outbox write;
- OpenAPI/contract parity.

## 8. P3 agent brief — Freqtrade execution adapter

Goal:

Implement dry-run-only private Freqtrade runtime lifecycle behind `ExecutionAdapter`.

Acceptance:

- provision/start/pause/stop/health;
- one bot -> one isolated runtime baseline;
- explicit readiness;
- no public port;
- runtime identity/correlation;
- deterministic failure state.

Do not change upstream Freqtrade core unless extension points are proven insufficient.

## 9. P4 agent brief — data and observability

Goal:

Implement event/outbox/correlation/telemetry foundations without owning bot business logic.

Acceptance:

- versioned event envelope;
- idempotent consumer reference;
- secret redaction tests;
- correlation propagation;
- basic metrics/log/trace instrumentation.

## 10. P5 agent brief — model lifecycle control

Goal:

Expose immutable model metadata and controlled assignment/promotion workflow without performing new model research.

Acceptance:

- exact ModelVersion identity;
- candidate cannot silently replace active version;
- promotion/rollback are audited;
- protected historical boundaries remain unchanged.

## 11. P6 agent brief — web portal

Goal:

Build the application shell and core dry-run operations UX using canonical APIs.

Acceptance:

- modern responsive shell;
- environment visibility;
- dashboard/bot/create-bot basics;
- loading/empty/error/denied states;
- browser has no direct Freqtrade path;
- critical Chromium E2E.

Do not copy third-party product assets or private captures.

## 12. P7 agent brief — risk and terminal

Goal:

Introduce deterministic TradeIntent gating and an audited terminal surface.

Acceptance:

- explicit approve/reject reason codes;
- kill switch;
- exposure/loss/health gates;
- no direct browser execution;
- unauthorized terminal actions denied.

## 13. P8 agent brief — trade intelligence

Goal:

Create DecisionSnapshot/TradeOutcome attribution and evidence-based post-trade analysis.

Acceptance:

- decision-time evidence separated from outcome;
- deterministic diagnosis runs before AI synthesis;
- losing trade is not automatically model error;
- analysis cannot affect execution availability;
- insight links evidence.

## 14. P9 agent brief — learning loop

Goal:

Turn validated observations into bounded experiment/training candidates.

Acceptance:

- Insight -> Hypothesis -> Experiment provenance;
- new DatasetVersion/ModelVersion identity;
- candidate creation does not promote;
- autonomy defaults at or below L4;
- protected holdout cannot enter iterative dataset resolution.

## 15. P10 agent brief — simulator and E2E

Goal:

Create a deterministic exchange/market simulator and full user-journey E2E harness.

Acceptance:

- browser creates and starts a dry-run AI bot;
- deterministic simulated trade executes through the `ApprovedExecutionIntent` simulator submitter boundary;
- portal PNL reconciles;
- post-trade analysis appears;
- audit trail exists;
- failure bundle contains cross-layer evidence;
- no arbitrary sleep-based readiness.

P10 simulation does not prove or require a functional `FreqtradeExecutionAdapter.submit_approved_intent` order-submission path. Real private Freqtrade submission remains a separate bounded integration concern.

## 16. P11 agent brief — Cloudflare staging

Goal:

Deploy production-like staging through Cloudflare-protected ingress.

Acceptance:

- Tunnel-based origin connectivity;
- origin/Freqtrade direct public reachability denied;
- WAF/rate-limit baseline;
- Access protects privileged surfaces;
- E2E uses dedicated staging identity/service credentials;
- no test-only security bypass.

Infrastructure changes require explicit owner approval where they affect a real external account.

## 17. P12 agent brief — autonomous repair

Goal:

Use E2E evidence to reproduce defects and prepare regression-test-first fixes.

Simulation-first execution is authorized before real P11 external infrastructure is provisioned, provided the input is deterministic P10/local/CI evidence and every result is labeled as simulated/non-production evidence. This mode cannot claim real Cloudflare ingress validation or production-like staging acceptance.

Acceptance:

- seeded defect diagnosed;
- regression test created;
- minimal patch on isolated branch;
- required validation passes;
- PR contains evidence;
- unsafe repair attempt is rejected.

The agent never self-deploys production.

## 18. Shared contract change protocol

If an agent discovers that a frozen shared contract must change:

1. stop modifying downstream modules;
2. record the first incompatible requirement in task checkpoint;
3. open/declare a bounded contract-change task;
4. update contract tests and migration/versioning policy;
5. merge contract change;
6. downstream agents rebase/continue from live state.

Do not let two implementation agents independently redefine the same event/API/domain schema.

## 19. Agent handoff quality

Every handoff ends with exactly one concrete `next_action`.

Good:

> Verify PR #NN is merged and CI green, then implement the Freqtrade adapter health/readiness contract in `ai_platform/portal/execution/` without changing shared domain schemas.

Bad:

> Continue working on the portal.

## 20. Program success condition

The architecture program is successfully delegated when a new agent can start any workstream from repository state alone, know its owned paths and non-negotiable boundaries, and complete the task without needing the chat transcript that created this plan.
