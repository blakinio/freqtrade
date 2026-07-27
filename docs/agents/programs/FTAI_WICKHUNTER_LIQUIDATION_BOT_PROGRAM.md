# FTAI WickHunter Liquidation AI Bot Program

Program ID: `FTAI-20260727-wickhunter-liquidation-ai-bot`

Status: `active`

## 1. Mission

Build a source-aware, dynamic-universe, liquidation-driven long/short research bot that preserves this authority chain:

```text
accepted liquidation and market evidence
  -> deterministic availability-time features
  -> deterministic WickHunter candidate
  -> optional bounded AI score
  -> versioned TradeIntent
  -> deterministic Risk Engine allow/reject
  -> shadow/paper simulation evidence
```

The program ends at shadow/paper readiness. It does not authorize live capital, private exchange credentials, unrestricted order submission, automatic model promotion, or direct browser control of Freqtrade.

## 2. Repository state and integration decisions

The program consumes existing contracts instead of replacing them:

- canonical liquidation events from `ai_platform/research/liquidations/`;
- provider-neutral historical liquidation contracts from `ai_platform/research/liquidations/historical/`;
- instrument catalog and deterministic universe inputs from `ai_platform/market_data/`;
- FreqAI model-extension, registry and validation conventions from `ai_platform/`;
- the portal deterministic Risk Engine as the future authoritative integration target;
- BM-00 bot-management contracts as the future bot-instance/configuration boundary.

The frozen `liquid20-v1` symbol set remains immutable collection and acceptance evidence. It is not the WickHunter trading universe. WickHunter uses a separate dynamic universe derived from instrument metadata and decision-time data quality.

The current portal risk service is DB-backed and currently exposes a manual-intent application flow with a smaller risk snapshot than this program requires. WickHunter therefore starts with pure, fail-closed strategy-owned risk contracts and does not modify active portal/BM paths. WH-06 will add a reviewed adapter after the required portal contract owner confirms the integration seam.

RL-v2 remains a separate experimental track. It is not eligible for promotion into this program until the supervised/replay pipeline is accepted and a later package proves incremental value under the same evaluation contract.

## 3. Protected boundaries

Every package must preserve:

- immutable accepted Liquid20 evidence;
- source labels and source-specific semantics;
- `occurred_at` and availability/receive timestamps;
- deterministic as-of joins;
- completed-candle availability rules;
- no use of the protected final holdout `20260801-20260930` before the formal one-shot decision;
- completed Phase 6 result `selected_model = null`;
- explicit model and parameter promotion;
- deterministic risk veto authority;
- `dry_run`/shadow/paper-only operation;
- fail-closed behavior for stale, missing, unhealthy or drifting dependencies;
- no direct exchange/order adapter import from strategy, scorer or shadow modules.

Automatic retraining may create a candidate model/parameter version only. It may not replace an approved version or authorize live trading.

## 4. Program-owned repository boundary

```text
ai_platform/wickhunter/**
tests/ai_platform_integration/test_wickhunter_*.py
docs/ai_platform/WICKHUNTER_*.md
docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md
docs/agents/tasks/FTAI-*-wickhunter-*.md
```

Packages may consume existing Liquid20, Market Data Fabric, registry, FreqAI and portal contracts. They must not edit their shared paths without a new ownership preflight and explicit delegation.

Reserved active work that must remain untouched includes:

- `ai_platform/portal/contracts/bot_management/**`;
- active BM feature modules and shared portal composition/migration paths;
- active Market Data Fabric source/capture paths;
- active RL-v2 provenance/Torch adapter paths;
- Synology/Oteryn deployment ownership.

## 5. Versioned domain contracts

The program converges on these records:

```text
DynamicUniverseSnapshot
LiquidationFeatureVector
CandidateLabel
WickHunterCandidate
CandidateScore
BoundedParameterSet
WickHunterTradeIntent
RiskDecision
ReplayDecisionEvidence
ShadowDecisionEvidence
ModelPromotionEvidence
ParameterPromotionEvidence
PortalObservabilitySnapshot
```

Every persisted decision binds dataset, feature, parameter, model and code identities. Decimal financial values remain decimal-safe.

## 6. Dynamic universe contract

A target instrument is eligible only when all required decision-time gates pass:

- active instrument metadata;
- supported derivative market and settlement/quote semantics;
- adequate liquidation source coverage;
- fresh liquidation events/source state;
- completed and fresh candle history;
- sufficient feature history;
- minimum quote volume;
- acceptable spread when available;
- no symbol-specific risk block.

Eligibility is recomputed from snapshots and produces explicit exclusion reasons. No BTC/ETH-only or manually maintained trading list is permitted.

Liquid20 may be used as an immutable evidence profile or comparison cohort, but never as a hidden permanent universe restriction.

## 7. Feature availability and leakage policy

Every feature stores or derives an availability timestamp. A feature is invalid when its availability exceeds the decision timestamp.

Required rules:

- live events use collector receive time as availability;
- vendor historical arrival time retains separate provenance;
- a candle close feature is unavailable before the candle closes;
- funding, OI, spread and order-flow values use their own publication/receive time;
- cross-symbol and market-wide values use only events available by the decision timestamp;
- no random split across overlapping time periods;
- purging/embargo is applied where labels overlap;
- the final holdout remains untouched until promotion review.

## 8. Baseline strategy hypotheses

The deterministic baseline evaluates two independently reportable hypotheses:

1. `reversal`: liquidation exhaustion followed by a counter-direction setup;
2. `continuation`: liquidation cascade and displacement followed by momentum continuation.

Both hypotheses require liquidation size/burst evidence, price displacement, VWAP/VWMA distance, wick/volatility context, liquidity, freshness, cooldown and duplicate protection.

Liquidation direction alone never creates a candidate.

## 9. AI contract

The first model package uses a tabular supervised LightGBM baseline. The common benchmark later compares:

- deterministic WickHunter score;
- LightGBM;
- XGBoost;
- an existing PyTorch-compatible model when the same dataset contract is supported;
- RL-v2 only after supervised/replay acceptance.

Permitted model outputs are advisory fields such as calibrated TP-before-SL probability, expected return after costs, MFE, MAE, no-trade confidence and a bounded risk multiplier.

A model never submits orders and never bypasses candidate or risk rules.

## 10. Controlled parameter optimization

All tunable values have immutable hard bounds. The initial WickHunter values are compatibility/research priors only.

The optimizer uses rolling walk-forward evaluation and may produce global, regime-specific or symbol-cluster-specific parameter candidates. Sparse symbols inherit a broader cluster/global parameter set instead of receiving independently overfit parameters.

A candidate parameter set records:

- parameter version and canonical hash;
- hard-bound contract version;
- dataset hash;
- code SHA;
- model hash where applicable;
- walk-forward windows and metrics;
- reproducibility seed/configuration;
- promotion state.

Retraining or optimization cannot directly mutate the running approved set.

## 11. Risk authority

The deterministic Risk Engine evaluates every TradeIntent and returns explicit allow/reject evidence. Required gates include:

- global kill switch and circuit breaker;
- stale/unavailable liquidation, candle, OI and funding data;
- source health;
- model promotion and drift;
- confidence threshold;
- base risk, leverage and effective exposure;
- DCA count, total DCA exposure and setup validity;
- concurrent, per-symbol, correlated and directional exposure;
- daily loss, drawdown and consecutive-loss cooldown;
- symbol cooldown;
- spread and liquidity.

Any missing required dependency fails closed.

DCA is a bounded plan and each actual DCA action is a new TradeIntent. No indefinite averaging, martingale or silent leverage expansion is allowed.

## 12. Replay and evaluation contract

Replay and shadow use the same pure decision functions and identities. Evaluation includes fees and realistic slippage and reports at least:

- net return and trade count;
- win rate, profit factor and expectancy;
- Sharpe/Sortino where meaningful;
- maximum drawdown and exposure;
- turnover and holding time;
- TP/SL/time outcomes;
- long/short results;
- source, symbol/liquidity and regime slices;
- walk-forward stability;
- probability calibration;
- comparison with the deterministic baseline.

A candidate is rejected when it has negligible unexplained activity, depends on one symbol/short interval, collapses after costs, worsens drawdown materially, or fails stability/data-quality gates.

## 13. Dependency-ordered packages

### WH-00 — contracts and synthetic vertical slice

Status: `active`

Deliver:

- program architecture and contracts;
- dynamic universe gate using Market Data Fabric instrument snapshots;
- source-labelled deterministic feature generation;
- reversal/continuation deterministic candidates;
- deterministic baseline scorer and external-model score contract;
- bounded parameters and compatibility prior;
- versioned TradeIntent;
- fail-closed pure Risk Engine;
- shadow simulator and auditable deterministic evidence;
- synthetic tests proving the first vertical slice;
- no real dataset, training, replay performance or profitability claim.

This package is executable with synthetic evidence only because real training/replay remains gated by accepted dataset selection.

### WH-01 — liquidation dataset builder

Depends on: WH-00 and accepted historical source/import evidence.

Deliver accepted-run/import selection, deterministic source-aware event normalization, availability-time market joins, atomic feature partitions, dataset manifest/hash, dynamic-universe history snapshots, explicit split geometry and no model execution.

### WH-02 — deterministic replay and event labels

Depends on: WH-01.

Deliver replay clock and as-of joins; TP-before-SL ordering; returns after fees/slippage; MFE, MAE and time-to-outcome; purged/embargoed walk-forward support; deterministic baseline evaluation; and replay/shadow parity evidence.

### WH-03 — baseline WickHunter strategy

Depends on: WH-02.

Deliver complete configurable reversal and continuation baselines, cooldown/duplicate behavior, regime and symbol/liquidity slices, and a baseline acceptance report without AI promotion.

### WH-04 — LightGBM candidate scorer

Depends on: WH-02 and WH-03.

Deliver supervised dataset adapter, LightGBM training/calibration, identical-data baseline comparison, feature/leakage audit, candidate registry evidence, and optional benchmark declarations only when the common contract is met.

### WH-05 — walk-forward bounded optimizer

Depends on: WH-03 and, for model-aware tuning, WH-04.

Deliver immutable hard-bound spaces, rolling walk-forward search, reproducibility/local perturbation checks, global/regime/cluster parameter candidates, candidate-only retraining output and final-holdout enforcement.

### WH-06 — Risk Engine and TradeIntent integration

Depends on: WH-00, a frozen portal/BM integration seam and current path-ownership preflight.

Deliver a reviewed mapping to canonical portal risk authority, full required risk snapshot/adapters and deterministic persistence. It activates no submission adapter and changes no shared portal contract without delegation.

### WH-07 — shadow runtime

Depends on: WH-01 through WH-06.

Deliver continuous read-only data consumption, dynamic universe refresh, candidate/scoring/risk loop, simulated positions/PnL, drift/circuit-breaker state and parity against replay. No credentials or order submission.

### WH-08 — portal observability

Depends on: WH-07 and portal integration-owner delegation.

Deliver read-only bot state, mode, universe, source freshness, model/parameter identity, candidates, risk rejections, simulated positions, PnL/drawdown, retraining/validation/drift and circuit-breaker state. Add no trade buttons to the liquidation page.

### WH-09 — paper validation and promotion evidence

Depends on: WH-07 and WH-08.

Deliver sustained paper/shadow evidence, replay-to-runtime reconciliation, model/parameter promotion candidate packages, rollback identity and an explicit owner decision point. It grants no live-capital authorization.

## 14. Package discipline

Each package uses a fresh branch from then-current `develop`, one bounded task checkpoint, one reviewable PR, declared owned paths, focused tests and required CI, review-thread and changed-path audits, exact hashes/evidence and exactly one next action.

No package may merge while conflicting with active BM, portal, market-data, RL-v2 or Synology ownership.

## 15. Program completion criteria

Shadow/paper readiness is reached only when dynamic multi-symbol eligibility works on accepted current data; feature/replay evidence is reproducible and source-labelled; no look-ahead leak is found; deterministic and AI candidates are compared identically after costs; risk blocks invalid intents; optimizer outputs stay inside hard bounds; identities are auditable; replay and shadow decisions match; no direct order/live path exists; and all required CI/review gates pass.

Profitability and live-capital readiness are not program completion claims.
