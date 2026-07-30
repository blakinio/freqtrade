---
task_id: FTAI-20260730-ai-program-closure-orchestration
status: ready
branch: agent/ai-program-closure-orchestration
base_branch: develop
created: 2026-07-30
updated: 2026-07-30
related_pr: null
program: FTAI-PROGRAM-AI-TRADING-PORTAL
goal_state: repository-complete-paper-shadow
required_reads:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/ARCHITECTURE.md
  - docs/ai_platform/ROADMAP.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
search_first:
  - current develop HEAD and open PRs
  - active task records and overlapping owned paths
  - implementation and tests for every unchecked backlog item
  - current portal and ASE completion evidence
owned_paths:
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
---

# AI platform program closure orchestration

## Goal

Close all remaining **autonomous repository work** required for a secure, complete paper/shadow AI trading product with its user-facing portal, without reopening completed work, duplicating canonical services, exposing Freqtrade publicly, consuming protected holdout data iteratively, or enabling live capital.

The task is designed for several agents working in parallel. Parallel implementation starts only after a serialized repository preflight proves the real gaps and freezes shared ownership.

## Closure target

This program has three distinct closure lanes:

1. **Repository closure — autonomous and in scope**
   - reconcile stale backlog entries against current code, tests, merged PRs and current architecture;
   - implement only proven software gaps;
   - complete user-facing paper/shadow workflows;
   - pass contract, backend, browser, integration, security and deterministic E2E validation;
   - leave authoritative backlog and program status accurate.

2. **Production-like staging acceptance — owner-managed**
   - real Cloudflare, protected GitHub environment, Synology, Authentik, Vault, DNS/TLS, test identity and restore evidence;
   - may be prepared by agents, but cannot be represented as complete without real owner-approved resources and external evidence.

3. **Live-capital enablement — excluded**
   - no live exchange credentials, live mode, withdrawal capability, unrestricted order authority or production promotion;
   - requires a separate explicit work package and owner approval.

Repository closure must not be blocked by lanes 2 or 3, but the final report must label those lanes accurately.

## Source-of-truth rule

The live repository, open PRs, active task ownership and exact-head CI are authoritative. The unchecked entries in `ai_strategy_engine/TASKS.md` are hypotheses until the preflight classifies them.

For every backlog item, the preflight must record exactly one state:

- `PROVEN_COMPLETE` — implementation and acceptance evidence already exist;
- `REAL_GAP` — bounded implementation is absent or acceptance is incomplete;
- `DUPLICATE_OR_SUPERSEDED` — another canonical service/package already owns the capability;
- `EXTERNAL_OWNER_ACTION` — repository code is ready but real target evidence requires owner resources;
- `DEFERRED_BY_POLICY` — intentionally outside the current closure target;
- `BLOCKED` — a concrete unresolved dependency prevents safe work.

No agent may implement an unchecked checkbox solely because it is unchecked.

## Agent topology

### Agent 0 — closure orchestrator and integration owner

Exclusive responsibilities:

- perform the serialized preflight;
- create and maintain `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- freeze exact child task IDs, dependencies and owned paths;
- own updates to `ai_strategy_engine/TASKS.md`, roadmap/program status and shared integration documentation;
- coordinate shared contract changes;
- sequence merges and synchronize downstream branches normally;
- verify exact-head CI and zero unresolved review threads;
- produce the final terminal program checkpoint.

Agent 0 must not absorb implementation that has a safe disjoint owner.

### Child workstreams

The following are launch candidates, not automatic declarations of missing work. Agent 0 creates only the child tasks that remain `REAL_GAP` after preflight.

| Workstream | Child task ID | Expected primary ownership | Parallel rule | Completion evidence |
|---|---|---|---|---|
| Shared domain/API contracts | `FTAI-20260730-closure-contracts` | `ai_strategy_engine/src/strategy_engine/domain/**`, `ai_platform/portal/contracts/**`, published schemas and contract tests | single exclusive contract owner; merges first | versioned models/schemas, compatibility tests, idempotency and tenant-scope evidence |
| Timestamp and leakage correctness | `FTAI-20260730-closure-time-leakage` | feature timestamp, closed-bar, HTF, pivot and leakage-guard implementation/tests | may research immediately; production integration after contract freeze | deterministic point-in-time tests, negative lookahead/leakage cases and replay evidence |
| Core feature engine | `FTAI-20260730-closure-feature-engine` | missing approved feature implementations, registry entries, fixtures and parity tests | disjoint feature modules only; registry shared files assigned explicitly | numerical fixtures, timestamp semantics, registry approval and deterministic parity |
| Simulator fidelity | `FTAI-20260730-closure-simulator` | deterministic simulator fee/slippage/latency/funding/gap/replay modules and tests | parallel after simulator contracts are frozen | deterministic replay, execution-cost cases, gap-stop and versioned evidence |
| Research data and market structure | `FTAI-20260730-closure-research-data` | proven gaps in liquidation/OI/funding alignment and clean-room structure research | must not overlap active Liquid20 ownership; clean-room only | deduplication/time metadata, alignment tests, provenance and no proprietary-code copying |
| AI routing and ranking | `FTAI-20260730-closure-ai-routing-ranking` | Regime Router, Ensemble Ranker and related research services/tests | uses immutable experiment/feature contracts; no promotion authority | OOS/stability/correlation/calibration evidence and fail-closed behavior |
| Signal Wizard frontend | `FTAI-20260730-closure-ui-signal-wizard` | wizard-specific routes, components, state and browser tests under portal web | mock-only work may begin after preflight; production client after contract freeze | feature selection, constraints, leakage warnings, preview, submit flow and denied/error states |
| Strategy Catalog frontend | `FTAI-20260730-closure-ui-strategy-catalog` | catalog-specific routes, components, state and browser tests under portal web | disjoint from wizard paths; shared shell/client remains integration-owned | version history, approvals, deployment state, rollback, provenance and authorization states |
| Full-platform integration and quality | `FTAI-20260730-closure-integration-e2e` | integration/E2E harness, evidence bundles, security and responsive acceptance | harness may start early; final assertions run after all real-gap PRs merge | critical browser journeys, deterministic exchange simulation, reconciliation, audit, security and failure bundle |
| External staging acceptance | `FTAI-20260730-closure-external-staging` | Cloudflare/protected environment runbooks and real acceptance evidence | blocked until explicit owner resources/authorization | five-probe external acceptance, direct-origin denial and protected E2E evidence |

Expected roots are guidance only. Every child task must declare exact, non-overlapping `owned_paths` after live repository inspection.

## Execution waves

### Wave 0 — serialized preflight

Only Agent 0 edits authoritative closure documents.

Deliverables:

- live `develop` HEAD and open-PR/task ownership snapshot;
- closure matrix covering every unchecked P0/P1/P2 backlog entry and every program completion requirement;
- proof links to existing source/tests/PR/CI for completed items;
- exact real-gap list;
- exact child task records with disjoint paths;
- dependency graph and merge order;
- shared contract freeze decision;
- external-owner action list separated from autonomous repository work.

Gate 0 passes only when no backlog item is ambiguous and no two child tasks own the same mutable path.

### Wave 1 — foundations and parallel scaffolding

After Gate 0:

- the contract agent implements any real shared-contract gap;
- time/leakage, feature, simulator, research-data and AI agents may implement inside frozen disjoint paths;
- frontend agents may build route-local UI against generated/mock clients derived from the frozen contract proposal;
- the E2E agent may prepare fixtures, page objects and deterministic harness extensions without changing feature implementation.

No downstream agent may redefine shared models, event envelopes, API schemas, generated-client inputs or common lifecycle enums.

### Wave 2 — contract convergence

After the contract PR merges:

- downstream agents rebase or merge `develop` normally;
- mock clients converge on canonical generated clients;
- backend/API integrations are completed;
- contract tests must prove no browser-to-Freqtrade path and no secret leakage.

### Wave 3 — integration and closure

After all real-gap implementation PRs merge:

- integration/E2E agent runs cross-layer acceptance;
- Agent 0 repairs only integration conflicts or creates bounded repair tasks;
- exact-head Linux CI, browser E2E, security analysis and deterministic simulation must pass;
- Agent 0 updates the closure matrix, backlog and program status from evidence;
- final checkpoint distinguishes repository closure from external staging and live-capital exclusion.

## Ownership and conflict protocol

The following files/areas are exclusive unless Agent 0 records an explicit transfer:

- `ai_strategy_engine/TASKS.md` — Agent 0 only;
- program/roadmap status documents — Agent 0 only;
- shared domain/API/event schemas — contract agent only;
- shared generated API client inputs — contract agent until freeze, then integration owner;
- shared portal shell/navigation — integration owner unless a route-local task declares exact files;
- CI workflow files — integration owner after coordination;
- package export/index files touched by multiple workstreams — assigned explicitly in the matrix.

If a child agent discovers a required shared-contract change, it must:

1. stop downstream modification;
2. record the first incompatible requirement in its checkpoint;
3. notify through the durable task/PR state;
4. let Agent 0 assign a bounded contract-change slice;
5. continue only after the contract change merges.

No force push, history rewrite, check bypass or direct commit to `develop` is allowed.

## Child task contract

Every child task must:

- use a dated task record under `docs/agents/tasks/`;
- inspect current `develop`, open PRs and active ownership before edits;
- declare exact `owned_paths`, dependencies and authoritative source;
- keep exactly one compact `## Context checkpoint`;
- remain inside its paths unless ownership is formally transferred;
- add tests at its layer;
- run narrow validation first and broader required gates next;
- open a focused PR against `develop`;
- record exact implementation head, workflow IDs/results and unresolved review-thread count;
- merge normally only after required checks pass;
- leave exactly one concrete next action for its successor or Agent 0.

Recommended branch format:

```text
agent/<child-task-id-without-FTAI-date-prefix>
```

## Non-negotiable boundaries

- Freqtrade remains private and is never a public browser backend.
- Browser traffic cannot reach Freqtrade, exchanges or Vault directly.
- All trading remains paper/shadow/dry-run for this closure program.
- `submit_approved_intent` and private dry-run transport may be tested only inside existing deterministic safety boundaries; no live-capital expansion.
- No exchange secrets, private endpoints, tokens or personal UI captures are committed.
- Frozen thresholds `0.006/-0.009` remain unchanged.
- Protected final holdout `20260801-20260930` is not reused iteratively.
- Completed Phase 6 and authoritative `selected_model = null` are not reopened.
- AI candidates, post-trade insights and autonomous repair cannot directly promote or mutate a production model.
- Repository/simulated evidence cannot be described as real external staging acceptance.
- Third-party closed/proprietary strategy code is not copied.

## Program acceptance criteria

Repository closure is complete only when all of the following are proven:

1. Every unchecked backlog item is classified in the closure matrix.
2. Every `REAL_GAP` has a merged bounded PR or an explicit blocker accepted by policy.
3. No completed ASE, BM or portal package was duplicated or silently reopened.
4. Shared contracts are versioned, tested and owned by one workstream at a time.
5. Timestamp/leakage and deterministic replay invariants pass where applicable.
6. Required frontend journeys are usable, responsive and cover loading, empty, denied and failure states.
7. Browser clients have no direct Freqtrade, exchange or secret-store authority.
8. Deterministic risk, immutable attribution, idempotency and tenant isolation remain enforced.
9. Full-platform critical E2E passes through the supported paper/shadow path.
10. Exact-head required CI and security checks pass for every merged child PR.
11. The authoritative backlog, roadmap and program status match repository evidence.
12. The terminal checkpoint contains no autonomous repository next step, while separately listing owner-managed external acceptance and excluded live-capital work.

## Validation requirements

Per child task, select the narrowest applicable set and then the required repository gates:

- Python compile, Ruff, mypy and targeted tests;
- JSON Schema and contract compatibility tests;
- deterministic fixtures/replay/parity tests;
- portal backend/API integration tests;
- portal web unit/type/build checks;
- Chromium critical E2E and responsive/denied/error-state coverage;
- AI Platform CI, AI Strategy Engine CI, Portal Web CI, Universal E2E, Freqtrade CI and workflow security where affected;
- checkpoint validation with `python tools/agents/checkpoint.py <task-path> --require-checkpoint`.

Agent 0 must record why any normally relevant gate is not applicable.

## External owner action lane

Agents may prepare runbooks and validation workflows, but they must stop before mutating real external infrastructure without explicit authorization. Real production-like staging closure requires owner-provided or owner-approved:

- Cloudflare account, Tunnel, DNS, Access, WAF and rate-limit configuration;
- protected GitHub environments, variables and secrets;
- reachable Synology staging target and isolated restore target;
- Authentik test users, MFA devices and recovery material;
- Vault target and scoped credentials;
- private Freqtrade staging runtime;
- dedicated external E2E identity/service credentials.

This lane is reported as `EXTERNAL_OWNER_ACTION` until real evidence exists.

## Context checkpoint

```yaml
checkpoint_version: 1
updated_at: 2026-07-30T09:14:00+02:00
head: 7240762e134d8db42b83030491ae52ec0d02cad6
branch: agent/ai-program-closure-orchestration
pr: null
status: ready
context_routes:
  - AGENTS.md
  - docs/agents/CONTEXT_HANDOFF.md
  - docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md
  - docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md
  - ai_strategy_engine/ARCHITECTURE.md
  - ai_strategy_engine/TASKS.md
owned_paths:
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
  - docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md
proven:
  - ASE-00, ASE-01, ASE-FR-01, ASE-02 and ASE-03 are recorded complete.
  - Portal repository work has progressed through P12 simulation-first acceptance and BM-09 browser convergence.
  - The portal program records real P11 external staging as owner-resource blocked and live capital as separately authorized.
  - Repository governance requires dedicated branches, exact ownership, durable checkpoints and normal PR/CI gates.
derived:
  - Unchecked ai_strategy_engine backlog entries cannot safely be treated as missing implementation without repository reconciliation.
  - Maximum safe parallelism requires a serialized preflight and one exclusive shared-contract owner.
  - Frontend route-local work can run against frozen mocks while backend contracts converge.
unknown:
  - Which unchecked P0/P1/P2 items are genuine gaps versus implemented, superseded or stale documentation.
  - Exact disjoint source paths for each child task after current-code ownership inspection.
  - Whether any new open PR or task advances overlapping paths before child-task declaration.
conflicts: []
first_failure:
  marker: STALE_BACKLOG_RISK
  evidence: The strategy-engine checklist contains unchecked items while the program record proves substantial overlapping portal and ASE capabilities are already complete; direct implementation from checkbox state would risk duplication.
rejected_hypotheses:
  - Launch one agent per unchecked checkbox without inventory.
  - Let multiple agents independently edit shared contracts or backlog status.
  - Treat repository fixtures as real Cloudflare, Synology, Authentik or Vault acceptance.
  - Include live-capital activation in this closure program.
changed_paths:
  - docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md
validation:
  - command: Repository-backed architecture and program-state review on develop 7240762e134d8db42b83030491ae52ec0d02cad6
    result: PASS
    evidence: Current governance, portal program state, execution plan, ASE architecture and backlog were reconciled into a bounded orchestration design.
  - command: Open branch and PR ownership search for program closure task
    result: PASS
    evidence: No existing program-closure branch or matching open PR was found before declaration.
blockers: []
next_action: Agent 0 must create FTAI-20260730-program-closure-preflight from current develop, build the evidence-backed closure matrix, freeze shared contracts and exact child-task ownership, then launch only the child tasks classified as REAL_GAP.
```
