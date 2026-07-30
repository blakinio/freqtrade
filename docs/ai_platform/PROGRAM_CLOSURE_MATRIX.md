# AI Platform / AI Trading Portal Program Closure Matrix

Gate 0 branch: `agent/program-closure-preflight`  
Evidence anchor: `develop@1d347a785eddc900f4484c30e06c3ab4e8851b29` after normal merge of PR #759.  
Target: `repository-complete-paper-shadow`.

## Decision rules

Each item has exactly one status: `PROVEN_COMPLETE`, `REAL_GAP`, `DUPLICATE_OR_SUPERSEDED`, `EXTERNAL_OWNER_ACTION`, `DEFERRED_BY_POLICY` or `BLOCKED`. An unchecked checkbox is a hypothesis until code, tests, merged PRs and CI are inspected.

Status totals: `DEFERRED_BY_POLICY`=1, `DUPLICATE_OR_SUPERSEDED`=1, `EXTERNAL_OWNER_ACTION`=2, `PROVEN_COMPLETE`=50, `REAL_GAP`=34.

## Live repository and ownership snapshot

| Item | State and evidence |
|---|---|
| PR #759 | Merged normally as `1d347a785eddc900f4484c30e06c3ab4e8851b29` after exact-head Freqtrade CI and workflow-security success; zero unresolved review threads. |
| PR #753 | Open WickHunter production market-evidence package; owns WickHunter collector, market-evidence Portal, BFF, UI, deployment and tests. |
| PR #758 | Open read-only real-target Portal preflight; external owner lane, not P11 acceptance. |
| PR #761 | Open Liquid20 OKX runtime and Portal source work; owns liquidation source catalog, runtime, read model, deployment and tests. |
| PR #762 | Open Liquidations monitoring and Portal restart-contract repair; owns named workflows, alert code and deployment proof paths. |
| PR #763 | Merged into PR #753 feature branch as exact-head validation support. |
| Repository visibility | GitHub metadata reports `public`; owner must change it to private. |
| Protected boundaries | Thresholds `0.006/-0.009`, final holdout `20260801-20260930`, Phase 6 `selected_model = null`, paper, shadow and dry-run only. |

## P0.1 Domain contracts

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| FeatureRecord | `PROVEN_COMPLETE` | `none` | `domain/models.py`; schema and unit tests; PR #584. |
| SignalEvent | `PROVEN_COMPLETE` | `none` | `domain/models.py`; schema and unit tests; PR #584. |
| StrategyDefinition | `PROVEN_COMPLETE` | `none` | v1 model and schema exist and validate; PR #584. |
| Experiment | `PROVEN_COMPLETE` | `none` | Portal P1 experiment identity plus durable Strategy Lab experiment store; PRs #114 and #679. |
| ValidationReport | `PROVEN_COMPLETE` | `none` | `domain/models.py` and `dsl/validator.py`; PR #584. |
| JSON Schema publishing | `PROVEN_COMPLETE` | `none` | Versioned repository schemas under `ai_strategy_engine/schemas/`; PR #584. |
| idempotency | `PROVEN_COMPLETE` | `none` | Feature and signal keys, Strategy Lab tenant idempotency and ASE-03 append-only conflict tests; PRs #584, #679 and #748. |

## P0.2 Timestamp-safe Feature Engine

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| closed-bar scheduler | `REAL_GAP` | `closure-time-leakage` | Closed and confirmed-bar behavior exists inside simulators, but no reusable scheduler module or boundary and replay suite exists. |
| UTC validation | `PROVEN_COMPLETE` | `none` | `_require_utc` and timezone-aware feature and pivot tests. |
| event_time/detected_at/available_at | `PROVEN_COMPLETE` | `none` | Canonical fields and ordering validators in `domain/models.py`. |
| HTF confirmation | `PROVEN_COMPLETE` | `none` | Registry confirmation policy, validator guard and leakage tests. |
| point-in-time feature snapshots | `PROVEN_COMPLETE` | `none` | FeatureRecord snapshots and ASE-00 and ASE-03 parity evidence. |
| append-only replay | `PROVEN_COMPLETE` | `none` | Leakage replay stability plus ASE-03 append-only evidence and idempotency. |

## P0.3 Core features

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| ATR RMA/SMA | `PROVEN_COMPLETE` | `none` | `features/common.py`, registry `atr.v1` and tests in PR #584. |
| SMA/EMA | `PROVEN_COMPLETE` | `none` | Moving-average implementations and Fibonacci MA modes in `features/trend.py`. |
| BB/KC | `PROVEN_COMPLETE` | `none` | `features/squeeze.py` and squeeze fixtures. |
| Squeeze corrected | `PROVEN_COMPLETE` | `none` | Registry corrected mode and unit tests. |
| Squeeze legacy comparison | `PROVEN_COMPLETE` | `none` | Explicit `legacy_bug_compatible` research-only mode and validator guard. |
| linreg momentum | `PROVEN_COMPLETE` | `none` | Squeeze momentum implementation and Strategy Lab use. |
| Supertrend | `PROVEN_COMPLETE` | `none` | `features/supertrend.py`, tests and Strategy Lab definition. |
| MACD SMA/EMA signal | `PROVEN_COMPLETE` | `none` | `features/macd.py`, registry enum and tests. |
| candle geometry | `PROVEN_COMPLETE` | `none` | `features/candles.py`, validated registry entry and tests. |
| robust volume | `PROVEN_COMPLETE` | `none` | `features/volume.py`, validated robust-z and EMA oscillator entries and tests. |
| confirmed pivots | `PROVEN_COMPLETE` | `none` | `features/pivots.py` delayed detection and availability plus tests. |
| support/resistance | `REAL_GAP` | `closure-feature-engine` | No implementation, test or registry entry exists; only confirmed pivots are available. |

## P0.4 Leakage Guard

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| timestamp order | `PROVEN_COMPLETE` | `none` | FeatureRecord and SignalEvent validators plus leakage negative test. |
| HTF guard | `PROVEN_COMPLETE` | `none` | `HTF_BAR_NOT_CLOSED` negative test. |
| pivot guard | `PROVEN_COMPLETE` | `none` | `PIVOT_BEFORE_CONFIRMATION` negative test. |
| future-shift guard | `PROVEN_COMPLETE` | `none` | `FUTURE_SHIFT` negative test. |
| target leakage guard | `PROVEN_COMPLETE` | `none` | `TARGET_LEAKAGE` negative test. |

## P0.5 Deterministic Simulator

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| fee model | `PROVEN_COMPLETE` | `none` | Strategy Lab deterministic entry and exit fees and reconciliation. |
| slippage model | `PROVEN_COMPLETE` | `none` | Strategy Lab next-bar-open slippage model and tests. |
| latency model | `REAL_GAP` | `closure-simulator` | Canonical P10 simulator has no scenario latency model. |
| gap stop | `REAL_GAP` | `closure-simulator` | No deterministic gap-through-stop fill semantics exist. |
| funding | `REAL_GAP` | `closure-simulator` | No simulator funding accrual model exists. |
| deterministic replay | `PROVEN_COMPLETE` | `none` | P10 universal scenario, Strategy Lab hashes and ASE-03 simulator and shadow parity. |

## P1.1 Strategy DSL

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| JSON Schema | `PROVEN_COMPLETE` | `none` | `strategy-definition.v1.schema.json` and schema tests. |
| typed AST | `REAL_GAP` | `closure-contracts` | Condition groups remain `dict[str, JsonValue]`; validator and evaluator parse raw mappings. |
| validator | `PROVEN_COMPLETE` | `none` | `StrategyValidator` enforces schema, registry, HTF, risk and operators. |
| compiler | `PROVEN_COMPLETE` | `none` | Canonical deterministic `StrategyEvaluator` plus Strategy Lab simulator consume validated DSL; a second compiler service would duplicate the bounded path. |
| Freqtrade adapter contract | `DUPLICATE_OR_SUPERSEDED` | `none` | Portal `ExecutionAdapter` and ASE-03 private paper and shadow controller are canonical; direct DSL or browser-to-Freqtrade compilation is excluded. |

## P1.2 Experiment Store

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| artifact storage | `PROVEN_COMPLETE` | `none` | Strategy Lab persists immutable result JSON with trades, equity, signals and hashes. |
| comparison API | `PROVEN_COMPLETE` | `none` | ASE-01 create, list, detail, trades, equity, signals and compare API plus E2E. |

## P1.4 Liquidation data layer

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| liquidation aggregation | `PROVEN_COMPLETE` | `none` | Liquid20 source-separated ingestion and aggregation plus Portal read model. |
| deduplication | `PROVEN_COMPLETE` | `none` | Accepted import and runtime identities plus dedup tests in Liquid20 and WickHunter. |
| latency metadata | `PROVEN_COMPLETE` | `none` | Exchange event, receive, heartbeat and Portal read times are explicit. |
| cross-exchange confirmation | `PROVEN_COMPLETE` | `none` | Bounded Binance USD-M and Bybit Linear source-separated evidence; OKX extension is active PR #761. |
| OI alignment | `REAL_GAP` | `closure-research-data` | No point-in-time OI as-of alignment implementation or tests found. |
| funding alignment | `REAL_GAP` | `closure-research-data` | No point-in-time funding as-of alignment implementation or tests found. |

## P1.5 Market structure research

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| clean-room BOS/CHoCH | `REAL_GAP` | `closure-research-data` | `features/market_structure.py` is a clean-room stub that raises `NotImplementedError`. |
| HH/HL/LH/LL | `REAL_GAP` | `closure-research-data` | `features/market_structure.py` is a clean-room stub that raises `NotImplementedError`. |
| EQH/EQL | `REAL_GAP` | `closure-research-data` | `features/market_structure.py` is a clean-room stub that raises `NotImplementedError`. |
| confirmed FVG | `REAL_GAP` | `closure-research-data` | `features/market_structure.py` is a clean-room stub that raises `NotImplementedError`. |
| own zone heuristic | `REAL_GAP` | `closure-research-data` | `features/market_structure.py` is a clean-room stub that raises `NotImplementedError`. |
| no LuxAlgo code copy | `PROVEN_COMPLETE` | `none` | License boundary and module docstring explicitly prohibit proprietary implementation copying. |

## P2.2 Regime Router

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| trend/range | `REAL_GAP` | `closure-ai-routing-ranking` | Roadmap Phase 7 remains planned; no canonical Regime Router implementation or tests found. |
| high/low volatility | `REAL_GAP` | `closure-ai-routing-ranking` | Roadmap Phase 7 remains planned; no canonical Regime Router implementation or tests found. |
| liquidation regime | `REAL_GAP` | `closure-ai-routing-ranking` | Roadmap Phase 7 remains planned; no canonical Regime Router implementation or tests found. |
| drift monitoring | `REAL_GAP` | `closure-ai-routing-ranking` | Roadmap Phase 7 remains planned; no canonical Regime Router implementation or tests found. |

## P2.3 Ensemble Ranker

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| correlation penalties | `REAL_GAP` | `closure-ai-routing-ranking` | No canonical Ensemble Ranker implementation or tests found; ASE-02 robustness evidence is an input, not this service. |
| OOS stability | `REAL_GAP` | `closure-ai-routing-ranking` | No canonical Ensemble Ranker implementation or tests found; ASE-02 robustness evidence is an input, not this service. |
| drawdown contribution | `REAL_GAP` | `closure-ai-routing-ranking` | No canonical Ensemble Ranker implementation or tests found; ASE-02 robustness evidence is an input, not this service. |
| calibration | `REAL_GAP` | `closure-ai-routing-ranking` | No canonical Ensemble Ranker implementation or tests found; ASE-02 robustness evidence is an input, not this service. |

## P2.4 Signal Wizard

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| feature selection | `REAL_GAP` | `closure-ui-signal-wizard` | Current `signal-wizard-form.tsx` only records a manual advisory signal and explicitly triggers no experiment or execution. |
| parameter constraints | `REAL_GAP` | `closure-ui-signal-wizard` | Current `signal-wizard-form.tsx` only records a manual advisory signal and explicitly triggers no experiment or execution. |
| leakage warnings | `REAL_GAP` | `closure-ui-signal-wizard` | Current `signal-wizard-form.tsx` only records a manual advisory signal and explicitly triggers no experiment or execution. |
| strategy preview | `REAL_GAP` | `closure-ui-signal-wizard` | Current `signal-wizard-form.tsx` only records a manual advisory signal and explicitly triggers no experiment or execution. |
| experiment submit | `REAL_GAP` | `closure-ui-signal-wizard` | Current `signal-wizard-form.tsx` only records a manual advisory signal and explicitly triggers no experiment or execution. |

## P2.5 Strategy Catalog

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| version history | `REAL_GAP` | `closure-ui-strategy-catalog` | Current catalog is a static two-entry summary tuple and table with no lifecycle detail or action flow. |
| approvals | `REAL_GAP` | `closure-ui-strategy-catalog` | Current catalog is a static two-entry summary tuple and table with no lifecycle detail or action flow. |
| deployments | `REAL_GAP` | `closure-ui-strategy-catalog` | Current catalog is a static two-entry summary tuple and table with no lifecycle detail or action flow. |
| rollback | `REAL_GAP` | `closure-ui-strategy-catalog` | Current catalog is a static two-entry summary tuple and table with no lifecycle detail or action flow. |
| provenance | `REAL_GAP` | `closure-ui-strategy-catalog` | Current catalog is a static two-entry summary tuple and table with no lifecycle detail or action flow. |

## Portal and program completion

| Item | Status | Owner or workstream | Evidence |
|---|---|---|---|
| Repository authentication and session boundary | `PROVEN_COMPLETE` | `none` | PI-06 repository identity and session implementation and tests; real IdP acceptance remains external. |
| Tenant-scoped dry-run bot creation | `PROVEN_COMPLETE` | `none` | P2 and BM control-plane plus browser journeys. |
| Private isolated Freqtrade runtime provisioning | `PROVEN_COMPLETE` | `none` | P3, PI-08 and BM-07 private adapter; no public browser path. |
| Deterministic simulated trade through risk | `PROVEN_COMPLETE` | `none` | P10 universal simulator and Risk Core path. |
| PNL and execution reconciliation | `PROVEN_COMPLETE` | `none` | P8, P10 and BM evidence plus explicit unproven transport handling. |
| Post-trade analysis and insight | `PROVEN_COMPLETE` | `none` | P8 deterministic diagnosis and evidence-linked insight. |
| Bounded learning candidate without promotion | `PROVEN_COMPLETE` | `none` | P9 and ASE-02 candidate flow; active model remains immutable. |
| Autonomous repair PR from deterministic evidence | `PROVEN_COMPLETE` | `none` | P12 simulation-first bounded repair package. |
| No browser-to-Freqtrade, exchange or Vault authority | `PROVEN_COMPLETE` | `none` | Portal security contracts, BM-09 browser request evidence and private adapter boundary. |
| Full closure E2E after new gaps merge | `REAL_GAP` | `closure-integration-e2e` | Existing BM-09 and P10 E2E predates the new closure workstreams. |
| Closure observability and first-failure bundle | `REAL_GAP` | `closure-integration-e2e` | New scheduler, simulator, router and frontend paths do not yet have cross-layer closure telemetry evidence. |
| Authoritative backlog, roadmap and program freshness | `REAL_GAP` | `Agent 0 final integration` | `TASKS.md` still contains stale unchecked items; update only after child evidence merges. |
| Repository visibility private | `EXTERNAL_OWNER_ACTION` | `owner` | GitHub repository metadata currently reports `public`; changing visibility is an owner-controlled setting. |
| Real P11 protected external acceptance | `EXTERNAL_OWNER_ACTION` | `closure-external-staging` | Cloudflare, Synology, Authentik, Vault and protected-environment evidence is absent; PR #758 is read-only preflight only. |
| Live-capital enablement | `DEFERRED_BY_POLICY` | `none` | P14 and live-small require a separate explicit owner-approved work package; no current authorization. |

## Shared contract freeze

Canonical shared-contract owner until the contract PR merges: `FTAI-20260730-closure-contracts`.

Existing canonical families:

- Strategy Engine v1: `ai_strategy_engine/src/strategy_engine/domain/models.py`, `ai_strategy_engine/src/strategy_engine/api/contracts.py`, `ai_strategy_engine/schemas/*.schema.json`;
- Portal v1: `ai_platform/portal/contracts/**`;
- closure slice: typed DSL AST plus Signal Wizard and Strategy Catalog lifecycle contracts assigned exclusively to the contract child task.

Version and compatibility policy:

1. Existing Strategy Engine `schema_version = 1.0.0` and Portal `contract_version = v1` remain readable.
2. Additive optional fields are backward-compatible only when contract tests prove it.
3. Required-field removal, enum narrowing or semantic change requires a new version, migration and compatibility evidence in a dedicated contract PR.
4. Tenant, actor, resource, environment, idempotency, provenance and secret exclusion remain fail-closed.
5. The contract PR merges first. No other worker edits shared schemas, generated-client inputs, common exports or lifecycle enums.
6. Time and leakage, Feature Engine and Simulator workers may start after Gate 0 because their exact paths do not depend on the new shared contracts.
7. AI routing and ranking plus both frontend workers wait for the contract merge. Mock-only exploration outside mutable repository paths is allowed; implementation must not redefine contracts.

## Dependency and merge graph

```text
contracts ──────────────┬─> ai-routing-ranking ─┐
                        ├─> ui-signal-wizard    ├─> integration-e2e
                        └─> ui-strategy-catalog ┘
time-leakage ────────────────────────────────────┤
feature-engine ────────────────┬─────────────────┤
                               └─> ai-routing-ranking
PR #753 + PR #761 terminal ─> research-data ─> ai-routing-ranking
simulator ───────────────────────────────────────┘

external-staging: owner-managed, outside autonomous merge graph
live capital: deferred by policy, no task
```

Merge order:

1. contracts;
2. time and leakage, Feature Engine and Simulator in any conflict-free order;
3. Research Data after PR #753 and PR #761 reach terminal state;
4. AI routing and ranking after contracts, Feature Engine and Research Data;
5. Signal Wizard and Strategy Catalog after contracts, in either order;
6. Integration and E2E after all required implementation merges;
7. Agent 0 updates `TASKS.md`, roadmap, program status and terminal checkpoint from merged evidence.

## Manual dispatch table

| Workstream | Status | Child task path | Branch | Prompt path | Dependencies | Exact owned paths | Merge order | Start condition |
|---|---|---|---|---|---|---|---:|---|
| Shared contracts | `READY` | `docs/agents/tasks/FTAI-20260730-closure-contracts.md` | `agent/closure-contracts` | `docs/agents/prompts/ai-program-closure/CONTRACTS-AGENT-PROMPT.md` | none | Exact AST, schema and product-contract files in child frontmatter. | 1 | Gate 0 PR merged. |
| Time and leakage | `READY` | `docs/agents/tasks/FTAI-20260730-closure-time-leakage.md` | `agent/closure-time-leakage` | `docs/agents/prompts/ai-program-closure/TIME-LEAKAGE-AGENT-PROMPT.md` | none | New timing scheduler package and two exact tests. | 2 | Gate 0 PR merged. |
| Feature Engine | `READY` | `docs/agents/tasks/FTAI-20260730-closure-feature-engine.md` | `agent/closure-feature-engine` | `docs/agents/prompts/ai-program-closure/FEATURE-ENGINE-AGENT-PROMPT.md` | none | Support and resistance module, exclusive registry file and two exact tests. | 2 | Gate 0 PR merged. |
| Simulator | `READY` | `docs/agents/tasks/FTAI-20260730-closure-simulator.md` | `agent/closure-simulator` | `docs/agents/prompts/ai-program-closure/SIMULATOR-AGENT-PROMPT.md` | none | Canonical simulator schema and exchange, four fidelity modules and three exact tests. | 2 | Gate 0 PR merged. |
| Research Data | `BLOCKED` | `docs/agents/tasks/FTAI-20260730-closure-research-data.md` | `agent/closure-research-data` | `docs/agents/prompts/ai-program-closure/RESEARCH-DATA-AGENT-PROMPT.md` | PR #753 and PR #761 terminal | Existing market-structure stub, new alignment module and exact tests only. | 3 | Source contracts frozen after active PRs. |
| AI routing and ranking | `WAIT_FOR_CONTRACT` | `docs/agents/tasks/FTAI-20260730-closure-ai-routing-ranking.md` | `agent/closure-ai-routing-ranking` | `docs/agents/prompts/ai-program-closure/AI-ROUTING-RANKING-AGENT-PROMPT.md` | contracts, Feature Engine, Research Data | New `strategy_engine/ai/**` and three exact tests. | 4 | All dependencies merged. |
| Signal Wizard | `WAIT_FOR_CONTRACT` | `docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md` | `agent/closure-ui-signal-wizard` | `docs/agents/prompts/ai-program-closure/UI-SIGNAL-WIZARD-AGENT-PROMPT.md` | contracts | Route-local wizard, BFF, library and one exact browser spec. | 5 | Contract freeze merged. |
| Strategy Catalog | `WAIT_FOR_CONTRACT` | `docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md` | `agent/closure-ui-strategy-catalog` | `docs/agents/prompts/ai-program-closure/UI-STRATEGY-CATALOG-AGENT-PROMPT.md` | contracts | Existing catalog page plus route-local BFF, client, library and spec only. | 5 | Contract freeze merged. |
| Integration and E2E | `WAIT_FOR_IMPLEMENTATION_MERGES` | `docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md` | `agent/closure-integration-e2e` | `docs/agents/prompts/ai-program-closure/INTEGRATION-E2E-AGENT-PROMPT.md` | all repository real-gap PRs | Dedicated closure workflow, backend test, browser spec and evidence document. | 6 | Required implementation PRs merged and adjacent open PRs terminal or excluded. |
| External staging | `DO_NOT_START` | `docs/agents/tasks/FTAI-20260730-closure-external-staging.md` | `owner/closure-external-staging` | `docs/agents/prompts/ai-program-closure/EXTERNAL-STAGING-AGENT-PROMPT.md` | owner authorization and resources, PR #758 terminal | External evidence directory only. | owner lane | Repository private and all listed real resources supplied. |
| Live capital | `DO_NOT_START` | none | none | none | separate explicit authorization package | none | excluded | No authorization exists. |

## Path-disjointness result

The exact `owned_paths` in child task frontmatter are pairwise disjoint. Shared contracts have one owner. Registry mutation belongs only to Feature Engine. Existing market-structure mutation belongs only to Research Data. Simulator shared files belong only to Simulator. Shared shell and navigation, common generated-client inputs, existing CI workflows and authoritative backlog and roadmap files are not assigned to child workers.

## Gate 0 acceptance

- Every unchecked P0, P1 and P2 item is classified exactly once.
- Every portal completion, frontend, E2E, security, observability, documentation, P11 and live-capital requirement is classified.
- Real-gap child tasks and the owner-managed external lane have compact checkpoints and exactly one next action.
- Dependency and merge order are explicit.
- External resources and repository visibility are separated from autonomous code work.
- Live capital remains disabled.
