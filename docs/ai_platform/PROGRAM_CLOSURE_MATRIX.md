# AI Platform / AI Trading Portal Program Closure Matrix

## Gate 0 snapshot

- branch: `agent/program-closure-preflight`;
- evidence anchor: `develop@0208666d98849386e2f2d9acf534b13891e4afa2`;
- normal synchronization: PR #768 merged into this branch as `6515346ca1e2a44b059cb1e7c2585285e1fc0c17`;
- PR #759: merged normally as `1d347a785eddc900f4484c30e06c3ab4e8851b29`;
- live adjacent work: PR #761, PR #762 and PR #758 are open; PR #753 is merged in current `develop`;
- target: `repository-complete-paper-shadow`;
- private boundary means private runtime/API reachability: the browser has no direct Freqtrade, exchange or Vault path;
- thresholds `0.006/-0.009`, `selected_model = null` and protected holdout `20260801-20260930` remain frozen;
- paper/shadow/dry-run only; no live capital.

An unchecked box is a hypothesis until code, tests, merged PRs and current CI are inspected. Every unchecked P0/P1/P2 item below has exactly one allowed status.

## Every unchecked P0/P1/P2 item

| Section | Item | Status | Owner/workstream | Evidence |
|---|---|---|---|---|
| P0.1 | `FeatureRecord` | **PROVEN_COMPLETE** | `none` | Canonical model, schema and tests in `domain/models.py`; PR #584. |
| P0.1 | `SignalEvent` | **PROVEN_COMPLETE** | `none` | Canonical model, schema, examples and tests; PR #584. |
| P0.1 | `StrategyDefinition` | **PROVEN_COMPLETE** | `none` | Frozen v1 model and schema; PR #584. |
| P0.1 | `Experiment` | **PROVEN_COMPLETE** | `none` | Tenant-scoped durable Strategy Lab experiment/result store; PR #679. |
| P0.1 | `ValidationReport` | **PROVEN_COMPLETE** | `none` | UTC-aware model and validator tests; PR #584. |
| P0.1 | `JSON Schema publishing` | **PROVEN_COMPLETE** | `none` | Versioned schemas under `ai_strategy_engine/schemas/**`; PRs #584/#741. |
| P0.1 | `idempotency` | **PROVEN_COMPLETE** | `none` | Feature/signal keys, tenant idempotency and append-only admission; PRs #584/#679/#748. |
| P0.2 | `closed-bar scheduler` | **REAL_GAP** | `closure-time-leakage` | Closed/confirmed checks exist inside simulators, but no reusable Feature Engine scheduler boundary with availability/replay acceptance exists. |
| P0.2 | `UTC validation` | **PROVEN_COMPLETE** | `none` | `_require_utc` and timezone-aware tests. |
| P0.2 | `event_time/detected_at/available_at` | **PROVEN_COMPLETE** | `none` | Canonical fields and monotonic validators. |
| P0.2 | `HTF confirmation` | **PROVEN_COMPLETE** | `none` | Confirmed-HTF record builder and leakage guard. |
| P0.2 | `point-in-time feature snapshots` | **PROVEN_COMPLETE** | `none` | FeatureRecord provenance/version snapshots and ASE parity evidence. |
| P0.2 | `append-only replay` | **PROVEN_COMPLETE** | `none` | `assert_replay_stable` and ASE-03 append-only evidence. |
| P0.3 | `ATR RMA/SMA` | **PROVEN_COMPLETE** | `none` | `features/common.py::atr`, registry and tests. |
| P0.3 | `SMA/EMA` | **PROVEN_COMPLETE** | `none` | Independent SMA/EMA modes in `features/trend.py`. |
| P0.3 | `BB/KC` | **PROVEN_COMPLETE** | `none` | `features/squeeze.py`, fixtures and tests. |
| P0.3 | `Squeeze corrected` | **PROVEN_COMPLETE** | `none` | Corrected compatibility mode and tests. |
| P0.3 | `Squeeze legacy comparison` | **PROVEN_COMPLETE** | `none` | Explicit legacy-bug-compatible research mode and tests. |
| P0.3 | `linreg momentum` | **PROVEN_COMPLETE** | `none` | Rolling linear-regression momentum in squeeze implementation. |
| P0.3 | `Supertrend` | **PROVEN_COMPLETE** | `none` | `features/supertrend.py`, registry/tests and Strategy Lab. |
| P0.3 | `MACD SMA/EMA signal` | **PROVEN_COMPLETE** | `none` | `features/macd.py` supports both signal MA types. |
| P0.3 | `candle geometry` | **PROVEN_COMPLETE** | `none` | `features/candles.py` and tests. |
| P0.3 | `robust volume` | **PROVEN_COMPLETE** | `none` | Robust z-score and volume oscillator in `features/volume.py`. |
| P0.3 | `confirmed pivots` | **PROVEN_COMPLETE** | `none` | Delayed right-bar confirmation and availability in `features/pivots.py`. |
| P0.3 | `support/resistance` | **REAL_GAP** | `closure-feature-engine` | No canonical implementation, registry entry or focused test exists. |
| P0.4 | `timestamp order` | **PROVEN_COMPLETE** | `none` | Model validators and `FEATURE_AFTER_DECISION`. |
| P0.4 | `HTF guard` | **PROVEN_COMPLETE** | `none` | `HTF_BAR_NOT_CLOSED` negative tests. |
| P0.4 | `pivot guard` | **PROVEN_COMPLETE** | `none` | `PIVOT_BEFORE_CONFIRMATION` negative tests. |
| P0.4 | `future-shift guard` | **PROVEN_COMPLETE** | `none` | `FUTURE_SHIFT` negative tests. |
| P0.4 | `target leakage guard` | **PROVEN_COMPLETE** | `none` | `TARGET_LEAKAGE` negative tests. |
| P0.5 | `fee model` | **PROVEN_COMPLETE** | `none` | Strategy Lab deterministic entry/exit fees. |
| P0.5 | `slippage model` | **PROVEN_COMPLETE** | `none` | Next-bar-open slippage model and tests. |
| P0.5 | `latency model` | **REAL_GAP** | `closure-simulator` | No configurable deterministic scenario latency model found. |
| P0.5 | `gap stop` | **REAL_GAP** | `closure-simulator` | No deterministic gap-through-stop fill semantics found. |
| P0.5 | `funding` | **REAL_GAP** | `closure-simulator` | No simulator funding-accrual model found. |
| P0.5 | `deterministic replay` | **PROVEN_COMPLETE** | `none` | P10, Strategy Lab hashes/IDs and ASE replay parity. |
| P1.1 | `JSON Schema` | **PROVEN_COMPLETE** | `none` | Versioned v1 schema and validation tests. |
| P1.1 | `typed AST` | **REAL_GAP** | `closure-contracts` | Strategy condition groups remain `dict[str, JsonValue]`; no typed recursive AST exists. |
| P1.1 | `validator` | **PROVEN_COMPLETE** | `none` | Schema/registry/operator/HTF/risk validator exists. |
| P1.1 | `compiler` | **DUPLICATE_OR_SUPERSEDED** | `none` | The deterministic evaluator/simulator is the canonical safe execution of validated DSL; a source-code compiler would duplicate it and conflict with the no-eval/no-exec boundary. |
| P1.1 | `Freqtrade adapter contract` | **PROVEN_COMPLETE** | `none` | ASE-03 private paper/shadow adapter and parity gate; PR #748. |
| P1.2 | `artifact storage` | **PROVEN_COMPLETE** | `none` | Immutable experiment JSON/hashes/trades/equity/signals and registry artifacts. |
| P1.2 | `comparison API` | **PROVEN_COMPLETE** | `none` | Strategy Lab compare API/UI and registry comparison tooling. |
| P1.4 | `liquidation aggregation` | **PROVEN_COMPLETE** | `none` | Source-separated Liquid20/WickHunter aggregation and Portal read models. |
| P1.4 | `OI alignment` | **REAL_GAP** | `closure-research-data` | No point-in-time OI as-of alignment implementation/tests found. |
| P1.4 | `funding alignment` | **REAL_GAP** | `closure-research-data` | No point-in-time funding as-of alignment implementation/tests found. |
| P1.4 | `deduplication` | **PROVEN_COMPLETE** | `none` | Deterministic event/source identities and dedup tests. |
| P1.4 | `latency metadata` | **PROVEN_COMPLETE** | `none` | Occurred/received timestamps and ingest latency are explicit. |
| P1.4 | `cross-exchange confirmation` | **PROVEN_COMPLETE** | `none` | Binance/Bybit source-separated evidence exists; PR #761 is an additive OKX extension. |
| P1.5 | `clean-room BOS/CHoCH` | **REAL_GAP** | `closure-research-data` | `features/market_structure.py` is a clean-room stub raising `NotImplementedError`. |
| P1.5 | `HH/HL/LH/LL` | **REAL_GAP** | `closure-research-data` | The market-structure module is an unimplemented clean-room stub. |
| P1.5 | `EQH/EQL` | **REAL_GAP** | `closure-research-data` | The market-structure module is an unimplemented clean-room stub. |
| P1.5 | `confirmed FVG` | **REAL_GAP** | `closure-research-data` | The market-structure module is an unimplemented clean-room stub. |
| P1.5 | `own zone heuristic` | **REAL_GAP** | `closure-research-data` | The market-structure module is an unimplemented clean-room stub. |
| P1.5 | `no LuxAlgo code copy` | **PROVEN_COMPLETE** | `none` | Module/license boundaries explicitly prohibit proprietary copying. |
| P2.2 | `trend/range` | **REAL_GAP** | `closure-ai-routing-ranking` | No canonical Regime Router implementation/tests. |
| P2.2 | `high/low volatility` | **REAL_GAP** | `closure-ai-routing-ranking` | No canonical Regime Router implementation/tests. |
| P2.2 | `liquidation regime` | **REAL_GAP** | `closure-ai-routing-ranking` | No canonical Regime Router implementation/tests. |
| P2.2 | `drift monitoring` | **REAL_GAP** | `closure-ai-routing-ranking` | No canonical Regime Router implementation/tests. |
| P2.3 | `correlation penalties` | **REAL_GAP** | `closure-ai-routing-ranking` | No canonical Ensemble Ranker implementation/tests; ASE-02 evidence is only an input. |
| P2.3 | `OOS stability` | **REAL_GAP** | `closure-ai-routing-ranking` | No canonical Ensemble Ranker implementation/tests. |
| P2.3 | `drawdown contribution` | **REAL_GAP** | `closure-ai-routing-ranking` | No canonical Ensemble Ranker implementation/tests. |
| P2.3 | `calibration` | **REAL_GAP** | `closure-ai-routing-ranking` | No canonical Ensemble Ranker implementation/tests. |
| P2.4 | `feature selection` | **REAL_GAP** | `closure-ui-signal-wizard` | Current wizard records advisory signal evidence only. |
| P2.4 | `parameter constraints` | **REAL_GAP** | `closure-ui-signal-wizard` | Current wizard records advisory signal evidence only. |
| P2.4 | `leakage warnings` | **REAL_GAP** | `closure-ui-signal-wizard` | Current wizard records advisory signal evidence only. |
| P2.4 | `strategy preview` | **REAL_GAP** | `closure-ui-signal-wizard` | Current wizard records advisory signal evidence only. |
| P2.4 | `experiment submit` | **REAL_GAP** | `closure-ui-signal-wizard` | Current wizard records advisory signal evidence only. |
| P2.5 | `version history` | **REAL_GAP** | `closure-ui-strategy-catalog` | Current catalog is a static summary table. |
| P2.5 | `approvals` | **REAL_GAP** | `closure-ui-strategy-catalog` | Current catalog is a static summary table. |
| P2.5 | `deployments` | **REAL_GAP** | `closure-ui-strategy-catalog` | Current catalog is a static summary table. |
| P2.5 | `rollback` | **REAL_GAP** | `closure-ui-strategy-catalog` | Current catalog is a static summary table. |
| P2.5 | `provenance` | **REAL_GAP** | `closure-ui-strategy-catalog` | Current catalog is a static summary table. |

## Portal and program completion

| Requirement | Status | Owner | Evidence |
|---|---|---|---|
| Authentication/session boundary | **PROVEN_COMPLETE** | `none` | PI-06 repository identity/session implementation and tests; real IdP acceptance remains external. |
| Tenant-scoped dry-run bot creation | **PROVEN_COMPLETE** | `none` | P2/BM control plane and browser journeys. |
| Private isolated Freqtrade runtime/API | **PROVEN_COMPLETE** | `none` | P3/PI-08/BM-07/ASE-03; no public or browser-direct runtime path. GitHub repository visibility is not this runtime boundary. |
| Deterministic simulated trade through risk | **PROVEN_COMPLETE** | `none` | P10 universal simulator and Risk Core. |
| PNL/execution reconciliation | **PROVEN_COMPLETE** | `none` | P8/P10/BM evidence and explicit unavailable states. |
| Post-trade analysis and insight | **PROVEN_COMPLETE** | `none` | P8 deterministic diagnosis and evidence-linked insight. |
| Bounded learning candidate without promotion | **PROVEN_COMPLETE** | `none` | P9/ASE-02; active model remains immutable. |
| Evidence-based seeded-defect repair | **PROVEN_COMPLETE** | `none` | P12 simulation-first bounded repair. |
| Signal Wizard research workflow | **REAL_GAP** | `closure-ui-signal-wizard` | Five missing P2.4 capabilities. |
| Strategy Catalog lifecycle workflow | **REAL_GAP** | `closure-ui-strategy-catalog` | Five missing P2.5 capabilities. |
| Full closure E2E and first-failure observability | **REAL_GAP** | `closure-integration-e2e` | Existing BM-09/P10 predates the new closure workstreams. |
| Backlog/roadmap/program terminal freshness | **BLOCKED** | `Agent 0` | Update only after implementation and integration merges provide terminal evidence. |
| Real P11 protected external acceptance | **EXTERNAL_OWNER_ACTION** | `owner-managed lane` | Requires owner-approved Cloudflare/Synology/Authentik/Vault/DNS/TLS/protected-environment resources; PR #758 is read-only preflight only. |
| P13 scale/service extraction | **DEFERRED_BY_POLICY** | `none` | Start only after a measured bottleneck or unmet SLO. |
| Live capital/P14 | **DEFERRED_BY_POLICY** | `none` | Separate unauthorized package; no credentials, withdrawals or live-capital authority. |

## Shared contract freeze

**Exclusive owner:** `FTAI-20260730-closure-contracts` until its PR merges.

Canonical shared files are `ai_strategy_engine/src/strategy_engine/domain/models.py`, `ai_strategy_engine/src/strategy_engine/api/contracts.py`, `ai_strategy_engine/schemas/**`, `ai_platform/portal/contracts/**` and `ai_platform/portal/product/schema.py`. The proven gap is a typed recursive DSL AST plus versioned Signal Wizard/Strategy Catalog lifecycle contracts, so one contract PR is required.

Compatibility policy:

1. Existing Strategy Engine `1.0.0` and Portal v1 payloads remain readable.
2. Additive optional changes require compatibility tests; required-field removal, enum narrowing or semantic change requires a new version and migration evidence.
3. Tenant, actor, resource, environment, idempotency, provenance and secret exclusion remain fail-closed.
4. No other worker edits shared schemas, generated-client inputs, common exports or lifecycle enums.
5. Time/leakage, Feature Engine and Simulator may start after Gate 0 because their paths do not depend on the new contract.
6. AI routing/ranking and both frontend workers may perform read-only research/mock planning, but mutable implementation waits for the contract merge.

## Dependency and merge graph

```text
Gate 0
  ├─ contracts ───────────────┬─> AI routing/ranking ─┐
  │                            ├─> Signal Wizard       ├─> Integration/E2E
  │                            └─> Strategy Catalog    │
  ├─ time/leakage ────────────────────────────────────┤
  ├─ Feature Engine ───────────────> AI routing/ranking│
  ├─ Simulator ───────────────────────────────────────┤
  └─ PR #761 terminal -> Research Data -> AI routing──┘

P11 external acceptance: separate owner-managed lane
P13 scale: deferred until measured need
Live capital/P14: excluded and unauthorized
```

## Manual dispatch table

| Workstream | Status | Child task path | Branch | Prompt path | Dependencies | Exact owned paths | Merge order | Start condition |
|---|---|---|---|---|---|---|---:|---|
| Shared contracts | **READY** | `docs/agents/tasks/FTAI-20260730-closure-contracts.md` | `agent/closure-contracts` | `docs/agents/prompts/ai-program-closure/CONTRACTS-AGENT-PROMPT.md` | Gate 0 | `domain/models.py`; `domain/__init__.py`; `dsl/ast.py`; `dsl/__init__.py`; `dsl/validator.py`; `strategy-definition.v2.schema.json`; `test_dsl_ast.py`; `portal/contracts/strategy_closure.py`; `portal/contracts/__init__.py`; `portal/product/schema.py`; `test_strategy_closure_contracts.py`; child task | 1 | Gate 0 merged. |
| Time/leakage | **READY** | `docs/agents/tasks/FTAI-20260730-closure-time-leakage.md` | `agent/closure-time-leakage` | `docs/agents/prompts/ai-program-closure/TIME-LEAKAGE-AGENT-PROMPT.md` | Gate 0 | `strategy_engine/timing/__init__.py`; `timing/closed_bar.py`; `test_closed_bar_scheduler.py`; `test_closure_time_leakage.py`; child task | 2A | Gate 0 merged. |
| Feature Engine | **READY** | `docs/agents/tasks/FTAI-20260730-closure-feature-engine.md` | `agent/closure-feature-engine` | `docs/agents/prompts/ai-program-closure/FEATURE-ENGINE-AGENT-PROMPT.md` | Gate 0 | `features/support_resistance.py`; `feature_registry.v1.yaml`; `test_support_resistance.py`; `test_closure_support_resistance.py`; child task | 2B | Gate 0 merged. |
| Simulator | **READY** | `docs/agents/tasks/FTAI-20260730-closure-simulator.md` | `agent/closure-simulator` | `docs/agents/prompts/ai-program-closure/SIMULATOR-AGENT-PROMPT.md` | Gate 0 | `strategy_engine/simulator/{__init__,schema,latency,gap_stop,funding}.py`; three unit tests; one integration test; child task | 2C | Gate 0 merged. |
| Research Data | **BLOCKED** | `docs/agents/tasks/FTAI-20260730-closure-research-data.md` | `agent/closure-research-data` | `docs/agents/prompts/ai-program-closure/RESEARCH-DATA-AGENT-PROMPT.md` | PR #761 terminal | `features/market_structure.py`; `research/{__init__,liquidation_alignment}.py`; two unit tests; child task | 3 | PR #761 merged/closed and source contract rechecked. |
| AI routing/ranking | **WAIT_FOR_CONTRACT** | `docs/agents/tasks/FTAI-20260730-closure-ai-routing-ranking.md` | `agent/closure-ai-routing-ranking` | `docs/agents/prompts/ai-program-closure/AI-ROUTING-RANKING-AGENT-PROMPT.md` | contracts, Feature Engine, Research Data | `strategy_engine/ai/{__init__,regime_router,ensemble_ranker}.py`; two unit tests; one integration test; child task | 4 | All dependencies merged. |
| Signal Wizard | **WAIT_FOR_CONTRACT** | `docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md` | `agent/closure-ui-signal-wizard` | `docs/agents/prompts/ai-program-closure/UI-SIGNAL-WIZARD-AGENT-PROMPT.md` | contracts | exact route-local page/BFF/components/library/browser spec listed in child task | 5A | Contract PR merged. |
| Strategy Catalog | **WAIT_FOR_CONTRACT** | `docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md` | `agent/closure-ui-strategy-catalog` | `docs/agents/prompts/ai-program-closure/UI-STRATEGY-CATALOG-AGENT-PROMPT.md` | contracts | exact route-local page/BFF/component/library/browser spec listed in child task | 5B | Contract PR merged. |
| Integration/E2E | **WAIT_FOR_IMPLEMENTATION_MERGES** | `docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md` | `agent/closure-integration-e2e` | `docs/agents/prompts/ai-program-closure/INTEGRATION-E2E-AGENT-PROMPT.md` | all repository child PRs | dedicated closure workflow, backend test, browser spec, evidence document and child task | 6 | All required child PRs merged and `develop` green. |
| External P11 | **BLOCKED** | `docs/agents/tasks/FTAI-20260730-closure-external-staging.md` | `owner/closure-external-staging` | `docs/agents/prompts/ai-program-closure/EXTERNAL-STAGING-AGENT-PROMPT.md` | owner authorization/resources; PR #758 terminal | child task and `docs/ai_platform/portal/external-acceptance-evidence/**` | owner lane | Owner explicitly authorizes and supplies real resources. |
| Live capital/P14 | **DO_NOT_START** | — | — | — | separate explicit authorization | none | excluded | No authorization exists. |

The exact full mutable paths are authoritative in each child task frontmatter; they are pairwise disjoint and exclude PR #761/#762/#758 paths.

## Gate 0 acceptance

- all 73 unchecked P0/P1/P2 items are classified exactly once;
- each REAL_GAP has one child owner; P11 is an owner-managed external lane;
- shared-contract ownership and compatibility policy are explicit;
- dependency and merge order are explicit;
- P11 cannot be proven by fixtures; P13 and live capital remain outside autonomous closure;
- every checkpoint must pass `python tools/agents/checkpoint.py <task-path> --require-checkpoint` on the exact Gate 0 branch.
