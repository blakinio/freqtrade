# AI Platform / AI Trading Portal Program Closure Matrix

## Current coordinator snapshot

- repository: `blakinio/freqtrade`;
- base branch: `develop`;
- coordinator evidence anchor: `develop@20b4ca6e1341061a9ebe98a8415ff18501a11557`;
- target: `repository-complete-paper-shadow`;
- merged producers:
  - Shared contracts PR #781 -> `6e489f7e10199120424cbcd01b3e125711630243`;
  - Time/Leakage PR #777 -> `979744f1143246bd42e42fc2213c7e79fc68ea57`;
  - Simulator PR #787 -> `34b36157312d79fe3d6b22e6e1ab9a5b5bd97ae9`;
  - Liquid20/OKX source PR #761 -> `141e59a3c7da441432b3990a54903e5fcfc935c8`;
  - Research Data PR #821 -> `38f7ad50cfe1b03fdf7a6e9ee4a9b73ebbebe7de`, terminal PR #823 -> `087456dc23c9c198744b8cae7822c88a97d5abff`;
- merged adjacent monitoring: PR #762 -> `e73de2c7a080c79486141cdafa4d2bb41afdd80e`;
- merged Feature Engine: PR #780 -> `09bc139a766034840ac01898f8b68cd5c76fb7a2`;
- merged Strategy Catalog implementation PR #819 -> `d8ae3f5775500dda8259f415a84f77b59ab1b8ac`, terminal PR #822 -> `0e3c98086344904c852ecb2b8c5c201353df29ab`;
- merged Signal Wizard blocker PR #818 -> `94e15dde23e0a2402b580ef263d51af689e989b6`, terminal PR #820 -> `18881d8847c765e939509a0f34b9dc327c5c9270`;
- merged Signal Wizard backend PR #825 -> `0bc35521debd33312820dfad9f010e22aa651610`;
- merged Signal Wizard correlation blocker PR #832 -> `28fb301db2c575d610c73143e44bd68c40b46ec7`;
- merged coordinator closure: PR #808 -> `a256dc59ad896a21f593c098bcc8c076858790d9`;
- merged coordinator terminal checkpoint: PR #812 -> `e03c00ce9824fdf467108780387b52c58659c01b`;
- active repository PRs include WickHunter request-only PRs #816/#842, WickHunter recovery #833, AI routing/ranking #829 and Signal Wizard correlation repair #844;
- backend branch synchronization PRs #824, #826 and #828 merged normally;
- coordinator branch: `agent/program-closure-signal-wizard-context-repair-dispatch`;
- active correlation task: `docs/agents/tasks/FTAI-20260731-signal-wizard-correlation-repair.md`, PR #844;
- follow-up semantic task: `docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md` waits for PR #844;
- Signal Wizard frontend dispatch: `WAIT_FOR_CONTEXT_REPAIR`;
- thresholds `0.006/-0.009`, `selected_model = null` and protected holdout `20260801-20260930` remain frozen;
- paper/shadow/dry-run only; no live capital.

The current snapshot and manual dispatch table below supersede the original Gate 0 dispatch state. An unchecked backlog box remains a hypothesis until code, tests, merged PRs and current CI are inspected. WickHunter operational request PR numbers may rotate without changing child-workstream ownership or dependencies.

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
| P0.3 | `support/resistance` | **MERGED_COMPLETE** | `closure-feature-engine` | PR #780 merged as `09bc139a766034840ac01898f8b68cd5c76fb7a2`; exact head `6bb0d434c709481e283b398fbe2e4e89b7f701a5` passed required CI. |
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
| P1.4 | `OI alignment` | **MERGED_COMPLETE** | `closure-research-data` | PR #821 merged as `38f7ad50cfe1b03fdf7a6e9ee4a9b73ebbebe7de` with point-in-time alignment and deterministic source identity. |
| P1.4 | `funding alignment` | **MERGED_COMPLETE** | `closure-research-data` | PR #821 merged with aligned, missing, delayed and stale observation states. |
| P1.4 | `deduplication` | **PROVEN_COMPLETE** | `none` | Deterministic event/source identities and dedup tests. |
| P1.4 | `latency metadata` | **PROVEN_COMPLETE** | `none` | Occurred/received timestamps and ingest latency are explicit. |
| P1.4 | `cross-exchange confirmation` | **PROVEN_COMPLETE** | `none` | Binance/Bybit plus merged OKX source PR #761. |
| P1.5 | `clean-room BOS/CHoCH` | **MERGED_COMPLETE** | `closure-research-data` | PR #821 added close-confirmed non-repainting structure events. |
| P1.5 | `HH/HL/LH/LL` | **MERGED_COMPLETE** | `closure-research-data` | PR #821 added confirmed pivot classification. |
| P1.5 | `EQH/EQL` | **MERGED_COMPLETE** | `closure-research-data` | PR #821 added tolerance-bounded equal-high/equal-low classification. |
| P1.5 | `confirmed FVG` | **MERGED_COMPLETE** | `closure-research-data` | PR #821 added third-closed-bar confirmation. |
| P1.5 | `own zone heuristic` | **MERGED_COMPLETE** | `closure-research-data` | PR #821 added documented `pre-break-extreme-body-v1` zones. |
| P1.5 | `no LuxAlgo code copy` | **PROVEN_COMPLETE** | `none` | Module/license boundaries explicitly prohibit proprietary copying. |
| P2.2 | `trend/range` | **READY** | `closure-ai-routing-ranking` | Feature Engine and Research Data implementations are merged. |
| P2.2 | `high/low volatility` | **READY** | `closure-ai-routing-ranking` | Feature Engine and Research Data implementations are merged. |
| P2.2 | `liquidation regime` | **READY** | `closure-ai-routing-ranking` | Research Data PR #821 is merged. |
| P2.2 | `drift monitoring` | **READY** | `closure-ai-routing-ranking` | Research Data PR #821 is merged. |
| P2.3 | `correlation penalties` | **READY** | `closure-ai-routing-ranking` | Research Data PR #821 is merged. |
| P2.3 | `OOS stability` | **READY** | `closure-ai-routing-ranking` | Research Data PR #821 is merged. |
| P2.3 | `drawdown contribution` | **READY** | `closure-ai-routing-ranking` | Research Data PR #821 is merged. |
| P2.3 | `calibration` | **READY** | `closure-ai-routing-ranking` | Research Data PR #821 is merged. |
| P2.4 | `feature selection` | **WAIT_FOR_CONTEXT_REPAIR** | `closure-signal-wizard-context-hardening` | PR #825 drops disabled selections; semantic hardening must validate and preserve every approved selection. |
| P2.4 | `parameter constraints` | **WAIT_FOR_CONTEXT_REPAIR** | `closure-signal-wizard-context-hardening` | Numeric bounds on nonnumeric values must fail closed. |
| P2.4 | `leakage warnings` | **WAIT_FOR_CONTEXT_REPAIR** | `signal-wizard-correlation-repair` | PR #844 must expose stable bounded conflict reasons before semantic hardening proceeds. |
| P2.4 | `strategy preview` | **IMPLEMENTING** | `signal-wizard-correlation-repair` | PR #844 binds trusted correlation but must address Agent 0 review and complete exact-head CI. |
| P2.4 | `experiment submit` | **WAIT_FOR_CONTEXT_REPAIR** | `closure-signal-wizard-context-hardening` | Submit still needs complete persisted actor/target/environment/execution-mode binding and exact derived version identity. |
| P2.5 | `version history` | **MERGED_COMPLETE** | `closure-ui-strategy-catalog` | Implementation PR #819 and terminal PR #822 merged. |
| P2.5 | `approvals` | **MERGED_COMPLETE** | `closure-ui-strategy-catalog` | Implementation PR #819 and terminal PR #822 merged. |
| P2.5 | `deployments` | **MERGED_COMPLETE** | `closure-ui-strategy-catalog` | Paper/dry-run/shadow lifecycle evidence merged without live authority. |
| P2.5 | `rollback` | **MERGED_COMPLETE** | `closure-ui-strategy-catalog` | Same-origin guarded rollback intent/evidence merged. |
| P2.5 | `provenance` | **MERGED_COMPLETE** | `closure-ui-strategy-catalog` | Immutable tenant-scoped provenance merged. |

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
| Signal Wizard research workflow | **WAIT_FOR_CONTEXT_REPAIR** | `signal-wizard-correlation-repair` + `closure-signal-wizard-context-hardening` | PR #844 must finish the active correlation/router lane, then disjoint semantic hardening must merge before frontend restart. |
| Strategy Catalog lifecycle workflow | **MERGED_COMPLETE** | `closure-ui-strategy-catalog` | PR #819 and terminal PR #822 merged with exact-head browser/platform/security evidence. |
| Full closure E2E and first-failure observability | **WAIT_FOR_IMPLEMENTATION_MERGES** | `closure-integration-e2e` | Signal Wizard frontend and AI routing/ranking must merge. |
| Backlog/roadmap/program terminal freshness | **BLOCKED** | `Agent 0` | Update only after remaining implementation and integration merges provide terminal evidence. |
| Real P11 protected external acceptance | **EXTERNAL_OWNER_ACTION** | `owner-managed lane` | Requires owner-approved resources; operational preflight remains a separate lane. |
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
  ├─> Signal Wizard backend MERGED through PR #825
  │     └─> correlation/router repair IMPLEMENTING in PR #844
  │            └─> semantic/persistence hardening WAIT_FOR_CORRELATION_REPAIR
  │                   └─> Signal Wizard frontend WAIT_FOR_CONTEXT_REPAIR
  └─> Strategy Catalog COMPLETED

time/leakage MERGED
simulator MERGED
Feature Engine MERGED
Research Data COMPLETED through PRs #821/#823
  └─> AI routing/ranking READY
coordinator registry repair COMPLETED through PR #808
terminal coordinator checkpoint MERGED through PR #812
remaining repository child PRs -> Integration/E2E

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
| Coordinator registry repair | **COMPLETED** | `docs/agents/tasks/FTAI-20260730-closure-feature-registry-repair.md` | `agent/program-closure-coordinator-terminal` | — | PR #780 absorbed the dynamic-count repair; PR #808 merged closure ownership and PR #812 merged the terminal checkpoint. |
| Feature Engine | **COMPLETED** | `docs/agents/tasks/FTAI-20260730-closure-feature-engine.md` | `agent/closure-feature-engine` | `docs/agents/prompts/ai-program-closure/FEATURE-ENGINE-AGENT-PROMPT.md` | PR #780 merged; do not start a duplicate chat. |
| Research Data | **COMPLETED** | `docs/agents/tasks/FTAI-20260730-closure-research-data.md` | `agent/closure-research-data-terminal` | `docs/agents/prompts/ai-program-closure/RESEARCH-DATA-AGENT-PROMPT.md` | PR #821 and terminal PR #823 merged; do not start a duplicate chat. |
| Signal Wizard backend/API | **MERGED_REQUIRES_REPAIR** | `docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md` | `agent/closure-signal-wizard-unblock` | `docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-BACKEND-AGENT-PROMPT.md` | PR #825 merged as `0bc35521debd33312820dfad9f010e22aa651610`; do not restart the original task. |
| Signal Wizard correlation/router repair | **IMPLEMENTING** | `docs/agents/tasks/FTAI-20260731-signal-wizard-correlation-repair.md` | `agent/signal-wizard-correlation-repair-20260731` | — | Continue PR #844; address Agent 0 review 4826262200 and merge only after final exact-head green CI. |
| Signal Wizard semantic/persistence hardening | **WAIT_FOR_CORRELATION_REPAIR** | `docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md` | `agent/closure-signal-wizard-semantic-hardening` | `docs/agents/prompts/ai-program-closure/SIGNAL-WIZARD-CONTEXT-HARDENING-AGENT-PROMPT.md` | Start only after PR #844 merges; owned paths are disjoint from PR #844. |
| Signal Wizard frontend | **WAIT_FOR_CONTEXT_REPAIR** | `docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md` | `agent/closure-ui-signal-wizard` | `docs/agents/prompts/ai-program-closure/UI-SIGNAL-WIZARD-AGENT-PROMPT.md` | Both repair lanes must merge normally with green exact-head CI and zero unresolved review threads. |
| Strategy Catalog | **COMPLETED** | `docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md` | `agent/closure-ui-strategy-catalog-terminal` | `docs/agents/prompts/ai-program-closure/UI-STRATEGY-CATALOG-AGENT-PROMPT.md` | PR #819 and terminal PR #822 merged; do not start a duplicate chat. |
| AI routing/ranking | **READY** | `docs/agents/tasks/FTAI-20260730-closure-ai-routing-ranking.md` | `agent/closure-ai-routing-ranking` | `docs/agents/prompts/ai-program-closure/AI-ROUTING-RANKING-AGENT-PROMPT.md` | Research Data implementation and terminal checkpoints are merged. |
| Integration/E2E | **WAIT_FOR_IMPLEMENTATION_MERGES** | `docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md` | `agent/closure-integration-e2e` | `docs/agents/prompts/ai-program-closure/INTEGRATION-E2E-AGENT-PROMPT.md` | Remaining repository child PRs merged and develop green. |
| External P11 | **BLOCKED** | `docs/agents/tasks/FTAI-20260730-closure-external-staging.md` | `owner/closure-external-staging` | `docs/agents/prompts/ai-program-closure/EXTERNAL-STAGING-AGENT-PROMPT.md` | Explicit owner authorization/resources and terminal external evidence. |
| Live capital/P14 | **DO_NOT_START** | — | — | — | No authorization exists. |

## Coordinator repair ownership

The coordinator repair task records the stale-count ownership decision. PR #780 merged the exact dynamic-count behavior before a standalone repair PR opened, PR #808 merged closure ownership and dispatch evidence, and PR #812 merged the terminal checkpoint without a duplicate test diff.

Signal Wizard repair is split by live ownership. PR #844 exclusively owns router.py, the existing Signal Wizard test and its task while fixing trusted correlation and public error behavior. The follow-up semantic task owns only service/persistence/model/migration paths and a new disjoint test file after PR #844 merges. Frozen contracts and frontend paths remain untouched.

## Closure acceptance

- all original unchecked P0/P1/P2 items remain classified;
- merged workstreams record exact merge commits;
- every READY or COMPLETED workstream has disjoint owned paths and no active duplicate PR;
- Signal Wizard frontend remains explicitly `WAIT_FOR_CONTEXT_REPAIR` until PR #844 and the disjoint semantic-hardening task merge with exact-head evidence;
- final E2E waits for all remaining repository implementation merges;
- P11 cannot be proven by fixtures;
- P13 and live capital remain outside autonomous closure.
