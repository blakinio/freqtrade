# AI Platform / AI Trading Portal Program Closure Matrix

## Current coordinator snapshot

- repository: `blakinio/freqtrade`;
- base branch: `develop`;
- current evidence anchor: `develop@3e0fe8e9310584aae3cd59750cbe013f54aaf698`;
- target: `repository-complete-paper-shadow`;
- merged producers:
  - Shared contracts PR #781 -> `6e489f7e10199120424cbcd01b3e125711630243`;
  - Time/Leakage PR #777 -> `979744f1143246bd42e42fc2213c7e79fc68ea57`;
  - Simulator PR #787 -> `34b36157312d79fe3d6b22e6e1ab9a5b5bd97ae9`;
  - Liquid20/OKX source PR #761 -> `141e59a3c7da441432b3990a54903e5fcfc935c8`;
- active repository PRs: Feature Engine #780, Liquidations monitoring #762 and external read-only preflight #758;
- coordinator repair branch: `agent/program-closure-coordinator-repair`;
- coordinator repair task: `docs/agents/tasks/FTAI-20260730-closure-feature-registry-repair.md`;
- thresholds `0.006/-0.009`, `selected_model = null` and protected holdout `20260801-20260930` remain frozen;
- paper/shadow/dry-run only; no live capital.

The current snapshot and manual dispatch table below supersede the original Gate 0 dispatch state. An unchecked backlog box remains a hypothesis until code, tests, merged PRs and current CI are inspected.

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
| P0.2 | `closed-bar scheduler` | **MERGED_COMPLETE** | `closure-time-leakage` | PR #777 merged as `979744f1143246bd42e42fc2213c7e79fc68ea57`. |
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
| P0.3 | `support/resistance` | **IN_PROGRESS** | `closure-feature-engine` | PR #780 exact head `de2c2481840284b81b48b4c4d217d91336aadd26` passed required CI; coordinator repair must merge and the branch must restack. |
| P0.4 | `timestamp order` | **PROVEN_COMPLETE** | `none` | Model validators and `FEATURE_AFTER_DECISION`. |
| P0.4 | `HTF guard` | **PROVEN_COMPLETE** | `none` | `HTF_BAR_NOT_CLOSED` negative tests. |
| P0.4 | `pivot guard` | **PROVEN_COMPLETE** | `none` | `PIVOT_BEFORE_CONFIRMATION` negative tests. |
| P0.4 | `future-shift guard` | **PROVEN_COMPLETE** | `none` | `FUTURE_SHIFT` negative tests. |
| P0.4 | `target leakage guard` | **PROVEN_COMPLETE** | `none` | `TARGET_LEAKAGE` negative tests. |
| P0.5 | `fee model` | **PROVEN_COMPLETE** | `none` | Strategy Lab deterministic entry/exit fees. |
| P0.5 | `slippage model` | **PROVEN_COMPLETE** | `none` | Next-bar-open slippage model and tests. |
| P0.5 | `latency model` | **MERGED_COMPLETE** | `closure-simulator` | PR #787 merged as `34b36157312d79fe3d6b22e6e1ab9a5b5bd97ae9`. |
| P0.5 | `gap stop` | **MERGED_COMPLETE** | `closure-simulator` | PR #787 merged as `34b36157312d79fe3d6b22e6e1ab9a5b5bd97ae9`. |
| P0.5 | `funding` | **MERGED_COMPLETE** | `closure-simulator` | PR #787 merged as `34b36157312d79fe3d6b22e6e1ab9a5b5bd97ae9`. |
| P0.5 | `deterministic replay` | **PROVEN_COMPLETE** | `none` | P10, Strategy Lab hashes/IDs and ASE replay parity. |
| P1.1 | `JSON Schema` | **PROVEN_COMPLETE** | `none` | Versioned v1 schema and validation tests. |
| P1.1 | `typed AST` | **MERGED_COMPLETE** | `closure-contracts` | PR #781 merged as `6e489f7e10199120424cbcd01b3e125711630243`; freeze `549ba3afddba39ce455fce5eebbd4d67bea813a6`. |
| P1.1 | `validator` | **PROVEN_COMPLETE** | `none` | Schema/registry/operator/HTF/risk validator exists. |
| P1.1 | `compiler` | **DUPLICATE_OR_SUPERSEDED** | `none` | The deterministic evaluator/simulator is the canonical safe execution of validated DSL; a source-code compiler would duplicate it and conflict with the no-eval/no-exec boundary. |
| P1.1 | `Freqtrade adapter contract` | **PROVEN_COMPLETE** | `none` | ASE-03 private paper/shadow adapter and parity gate; PR #748. |
| P1.2 | `artifact storage` | **PROVEN_COMPLETE** | `none` | Immutable experiment JSON/hashes/trades/equity/signals and registry artifacts. |
| P1.2 | `comparison API` | **PROVEN_COMPLETE** | `none` | Strategy Lab compare API/UI and registry comparison tooling. |
| P1.4 | `liquidation aggregation` | **PROVEN_COMPLETE** | `none` | Source-separated Liquid20/WickHunter aggregation and Portal read models. |
| P1.4 | `OI alignment` | **READY** | `closure-research-data` | PR #761 is terminal; source identity/time metadata is frozen for the child worker. |
| P1.4 | `funding alignment` | **READY** | `closure-research-data` | PR #761 is terminal; source identity/time metadata is frozen for the child worker. |
| P1.4 | `deduplication` | **PROVEN_COMPLETE** | `none` | Deterministic event/source identities and dedup tests. |
| P1.4 | `latency metadata` | **PROVEN_COMPLETE** | `none` | Occurred/received timestamps and ingest latency are explicit. |
| P1.4 | `cross-exchange confirmation` | **PROVEN_COMPLETE** | `none` | Binance/Bybit plus merged OKX source PR #761. |
| P1.5 | `clean-room BOS/CHoCH` | **READY** | `closure-research-data` | Child task is unblocked after PR #761. |
| P1.5 | `HH/HL/LH/LL` | **READY** | `closure-research-data` | Child task is unblocked after PR #761. |
| P1.5 | `EQH/EQL` | **READY** | `closure-research-data` | Child task is unblocked after PR #761. |
| P1.5 | `confirmed FVG` | **READY** | `closure-research-data` | Child task is unblocked after PR #761. |
| P1.5 | `own zone heuristic` | **READY** | `closure-research-data` | Child task is unblocked after PR #761. |
| P1.5 | `no LuxAlgo code copy` | **PROVEN_COMPLETE** | `none` | Module/license boundaries explicitly prohibit proprietary copying. |
| P2.2 | `trend/range` | **WAITING** | `closure-ai-routing-ranking` | Contracts are merged; Feature Engine and Research Data must merge. |
| P2.2 | `high/low volatility` | **WAITING** | `closure-ai-routing-ranking` | Contracts are merged; Feature Engine and Research Data must merge. |
| P2.2 | `liquidation regime` | **WAITING** | `closure-ai-routing-ranking` | Research Data must merge. |
| P2.2 | `drift monitoring` | **WAITING** | `closure-ai-routing-ranking` | Feature Engine and Research Data must merge. |
| P2.3 | `correlation penalties` | **WAITING** | `closure-ai-routing-ranking` | Feature Engine and Research Data must merge. |
| P2.3 | `OOS stability` | **WAITING** | `closure-ai-routing-ranking` | Feature Engine and Research Data must merge. |
| P2.3 | `drawdown contribution` | **WAITING** | `closure-ai-routing-ranking` | Feature Engine and Research Data must merge. |
| P2.3 | `calibration` | **WAITING** | `closure-ai-routing-ranking` | Feature Engine and Research Data must merge. |
| P2.4 | `feature selection` | **READY** | `closure-ui-signal-wizard` | Frozen Signal Wizard contracts are merged and ownership is disjoint. |
| P2.4 | `parameter constraints` | **READY** | `closure-ui-signal-wizard` | Frozen Signal Wizard contracts are merged and ownership is disjoint. |
| P2.4 | `leakage warnings` | **READY** | `closure-ui-signal-wizard` | Frozen Signal Wizard contracts are merged and ownership is disjoint. |
| P2.4 | `strategy preview` | **READY** | `closure-ui-signal-wizard` | Frozen Signal Wizard contracts are merged and ownership is disjoint. |
| P2.4 | `experiment submit` | **READY** | `closure-ui-signal-wizard` | Frozen Signal Wizard contracts are merged and ownership is disjoint. |
| P2.5 | `version history` | **READY** | `closure-ui-strategy-catalog` | Frozen Strategy Catalog contracts are merged and ownership is disjoint. |
| P2.5 | `approvals` | **READY** | `closure-ui-strategy-catalog` | Frozen Strategy Catalog contracts are merged and ownership is disjoint. |
| P2.5 | `deployments` | **READY** | `closure-ui-strategy-catalog` | Frozen Strategy Catalog contracts are merged and ownership is disjoint. |
| P2.5 | `rollback` | **READY** | `closure-ui-strategy-catalog` | Frozen Strategy Catalog contracts are merged and ownership is disjoint. |
| P2.5 | `provenance` | **READY** | `closure-ui-strategy-catalog` | Frozen Strategy Catalog contracts are merged and ownership is disjoint. |

## Portal and program completion

| Requirement | Status | Owner | Evidence |
|---|---|---|---|
| Authentication/session boundary | **PROVEN_COMPLETE** | `none` | PI-06 repository identity/session implementation and tests; real IdP acceptance remains external. |
| Tenant-scoped dry-run bot creation | **PROVEN_COMPLETE** | `none` | P2/BM control plane and browser journeys. |
| Private isolated Freqtrade runtime/API | **PROVEN_COMPLETE** | `none` | P3/PI-08/BM-07/ASE-03; no public or browser-direct runtime path. |
| Deterministic simulated trade through risk | **PROVEN_COMPLETE** | `none` | P10 universal simulator and Risk Core. |
| PNL/execution reconciliation | **PROVEN_COMPLETE** | `none` | P8/P10/BM evidence and explicit unavailable states. |
| Post-trade analysis and insight | **PROVEN_COMPLETE** | `none` | P8 deterministic diagnosis and evidence-linked insight. |
| Bounded learning candidate without promotion | **PROVEN_COMPLETE** | `none` | P9/ASE-02; active model remains immutable. |
| Evidence-based seeded-defect repair | **PROVEN_COMPLETE** | `none` | P12 simulation-first bounded repair. |
| Signal Wizard research workflow | **READY** | `closure-ui-signal-wizard` | Contract dependency merged; no active overlap. |
| Strategy Catalog lifecycle workflow | **READY** | `closure-ui-strategy-catalog` | Contract dependency merged; no active overlap. |
| Full closure E2E and first-failure observability | **WAIT_FOR_IMPLEMENTATION_MERGES** | `closure-integration-e2e` | Feature Engine, Research Data, routing/ranking and both UI workers must merge. |
| Backlog/roadmap/program terminal freshness | **BLOCKED** | `Agent 0` | Update only after implementation and integration merges provide terminal evidence. |
| Real P11 protected external acceptance | **EXTERNAL_OWNER_ACTION** | `owner-managed lane` | Requires owner-approved resources; PR #758 is read-only preflight only. |
| P13 scale/service extraction | **DEFERRED_BY_POLICY** | `none` | Start only after a measured bottleneck or unmet SLO. |
| Live capital/P14 | **DEFERRED_BY_POLICY** | `none` | Separate unauthorized package; no credentials, withdrawals or live-capital authority. |

## Shared contract freeze

The exclusive producer lease ended when PR #781 merged. Downstream workers must consume the canonical imports at contract freeze commit `549ba3afddba39ce455fce5eebbd4d67bea813a6` and may not redefine shared schemas, generated-client inputs, common exports or lifecycle enums.

Compatibility remains:

1. Existing Strategy Engine `1.0.0` and Portal v1 payloads remain readable.
2. Additive optional changes require compatibility tests; breaking semantic changes require a new version and migration evidence.
3. Tenant, actor, resource, environment, idempotency, provenance and secret exclusion remain fail-closed.
4. No browser-to-Freqtrade, exchange or Vault path and no live-capital authority.

## Current dependency graph

```text
contracts MERGED
  ├─> Signal Wizard READY
  └─> Strategy Catalog READY

time/leakage MERGED
simulator MERGED
PR #761 MERGED -> Research Data READY
coordinator registry repair -> Feature Engine #780 restack/merge
Feature Engine + Research Data -> AI routing/ranking
all repository child PRs -> Integration/E2E

P11 external acceptance: separate owner-managed lane
P13 scale: deferred until measured need
Live capital/P14: excluded and unauthorized
```

## Manual dispatch table

| Workstream | Status | Child task path | Branch | Prompt path | Start condition |
|---|---|---|---|---|---|
| Shared contracts | **COMPLETED** | `docs/agents/tasks/FTAI-20260730-closure-contracts.md` | `agent/closure-contracts-terminal` | — | PR #781 and terminal PR #790 merged. |
| Time/leakage | **COMPLETED** | `docs/agents/tasks/FTAI-20260730-closure-time-leakage.md` | `agent/closure-time-leakage-terminal` | — | PR #777 and terminal PR #792 merged. |
| Simulator | **COMPLETED** | `docs/agents/tasks/FTAI-20260730-closure-simulator.md` | `agent/closure-simulator-terminal` | — | PR #787 merged; coordinator terminal checkpoint recorded. |
| Coordinator registry repair | **IN_PROGRESS** | `docs/agents/tasks/FTAI-20260730-closure-feature-registry-repair.md` | `agent/program-closure-coordinator-repair` | — | Merge this focused repair PR, then sync PR #780. |
| Feature Engine | **IN_PROGRESS** | `docs/agents/tasks/FTAI-20260730-closure-feature-engine.md` | `agent/closure-feature-engine` | `docs/agents/prompts/ai-program-closure/FEATURE-ENGINE-AGENT-PROMPT.md` | Do not start a duplicate chat; coordinator is finishing existing PR #780. |
| Research Data | **READY** | `docs/agents/tasks/FTAI-20260730-closure-research-data.md` | `agent/closure-research-data` | `docs/agents/prompts/ai-program-closure/RESEARCH-DATA-AGENT-PROMPT.md` | PR #761 merged and no active ownership overlap exists. |
| Signal Wizard | **READY** | `docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md` | `agent/closure-ui-signal-wizard` | `docs/agents/prompts/ai-program-closure/UI-SIGNAL-WIZARD-AGENT-PROMPT.md` | PR #781 merged and no active ownership overlap exists. |
| Strategy Catalog | **READY** | `docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md` | `agent/closure-ui-strategy-catalog` | `docs/agents/prompts/ai-program-closure/UI-STRATEGY-CATALOG-AGENT-PROMPT.md` | PR #781 merged and no active ownership overlap exists. |
| AI routing/ranking | **WAIT_FOR_FEATURE_AND_RESEARCH** | `docs/agents/tasks/FTAI-20260730-closure-ai-routing-ranking.md` | `agent/closure-ai-routing-ranking` | `docs/agents/prompts/ai-program-closure/AI-ROUTING-RANKING-AGENT-PROMPT.md` | Feature Engine and Research Data PRs merged. |
| Integration/E2E | **WAIT_FOR_IMPLEMENTATION_MERGES** | `docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md` | `agent/closure-integration-e2e` | `docs/agents/prompts/ai-program-closure/INTEGRATION-E2E-AGENT-PROMPT.md` | All repository child PRs merged and develop green. |
| External P11 | **BLOCKED** | `docs/agents/tasks/FTAI-20260730-closure-external-staging.md` | `owner/closure-external-staging` | `docs/agents/prompts/ai-program-closure/EXTERNAL-STAGING-AGENT-PROMPT.md` | Explicit owner authorization/resources and PR #758 terminal. |
| Live capital/P14 | **DO_NOT_START** | — | — | — | No authorization exists. |

## Coordinator repair ownership

The repair task exclusively owns the two stale count tests until its PR merges. PR #780 must then synchronize normally from `develop`; after synchronization its effective changed paths must return to the original Feature Engine task record plus implementation and focused tests.

## Closure acceptance

- all original unchecked P0/P1/P2 items remain classified;
- merged workstreams record exact merge commits;
- every READY workstream has disjoint owned paths and no active duplicate PR;
- final E2E waits for all repository implementation merges;
- P11 cannot be proven by fixtures;
- P13 and live capital remain outside autonomous closure.
