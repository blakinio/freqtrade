# GUI information architecture

## 1. Application shell

Desktop-first shell:

```text
+----------------+-------------------------------------------+----------------+
|                | TOP BAR                                   |                |
|                +-------------------------------------------+                |
| LEFT SIDEBAR   |                 WORKSPACE                 | CONTEXT        |
|                |                                           | INSPECTOR      |
|                |                                           | / SUMMARY      |
+----------------+-------------------------------------------+----------------+
| Runtime | Market Data | Synology | Training PC | Ollama | system status   |
+----------------------------------------------------------------------------+
```

The right inspector is contextual rather than globally permanent. It is sticky for configuration, comparison and review workflows and may collapse on smaller screens.

## 2. Primary navigation

```text
Overview

TRADING
  Bots
  Positions
  Orders
  Markets
  Alerts

RESEARCH
  Strategies
  Backtests
  Replays
  Experiments
  Comparisons

ML / MODELS
  Model Registry
  Training Jobs
  Features
  Datasets

AI LAB
  Ollama
  Research Agent
  Experiment Analysis
  Research History

PLATFORM
  Infrastructure
  Logs
  Integrations
  Settings
  Audit
```

Navigation should show at most one expanded domain at a time. Avoid a flat list of twenty-plus links.

## 3. Overview / Command Center

The opening screen must answer within seconds:

- Are runtime and market data healthy?
- Which bots are active/degraded/stopped?
- What is the simulated PnL and drawdown?
- Which model is ACTIVE and which CHALLENGER is under evaluation?
- Are there alerts requiring attention?
- Are Synology, training PC and Ollama reachable?

Suggested blocks: global health, simulated PnL/equity, active bots, alerts, model lifecycle summary, infrastructure summary and freshness indicators.

## 4. Bot list and Bot Detail

A bot is a first-class platform object, not merely a Freqtrade config. List cards/rows show identity, market, strategy revision, model identity, runtime location, state, recent simulated performance and last-decision freshness.

Bot Detail tabs:

- Overview
- Decisions
- Positions
- Performance
- Strategy
- Model
- Runtime
- Events
- Logs
- History

The **Decision Inspector** must reconstruct the causal view:

`market snapshot -> features/model output -> strategy evaluation -> gates/risk -> TRADE or NO_TRADE -> simulated outcome`

NO_TRADE is a first-class decision and must be inspectable like TRADE.

## 5. Create Bot v2

Replace the giant single-page form with a structured wizard:

1. General
2. Market
3. Strategy
4. Simulation capital/exposure
5. Entry
6. Position management / DCA / scaling
7. Take Profit / Stop Loss / exits
8. Filters / universe selection
9. Model
10. Runtime
11. Review

A sticky right summary shows bot identity, selected market, runtime, model, maximum simulated exposure, validation state, warnings and available actions.

Drafting and previewing are distinct from creating/activating runtime state. Validation errors should be local to the relevant step and summarized globally.

## 6. Market workspace

The market screen combines:

- candle/price chart and time-frame controls;
- decision/event overlays;
- market regime and volatility context;
- public market-data freshness;
- optional model probabilities/confidence;
- latest WickHunter/strategy decision and reason chain.

The user should be able to understand why a signal was accepted or rejected without jumping between logs and unrelated pages.

## 7. Model Registry

Every model version is a first-class immutable artifact with:

- identity/version;
- lifecycle state `BASELINE | CHALLENGER | ACTIVE | ARCHIVED`;
- dataset identity/hash;
- feature schema identity;
- parameters/training metadata;
- replay/out-of-sample/simulation metrics;
- provenance and creation time;
- activation history.

The primary comparison screen puts ACTIVE and CHALLENGER side-by-side, including regime slices rather than only global aggregates. Activation remains a deliberate, attributable action.

## 8. Training Center

Show training-node availability, queued/running/completed jobs, model family, dataset, progress, resource utilization when available, experiment count and terminal outcome. The normal heavy-training target may be the local workstation; persistent platform operation must not depend on that workstation being online.

## 9. AI Lab / Ollama

AI Lab is a research cockpit, not a direct execution surface. Users select bounded context such as an experiment, backtest, model, dataset or bot and ask the local LLM to explain results, identify degradation, compare experiments or propose a new hypothesis.

The LLM may create a proposed experiment/draft, but it must not implicitly activate a model, strategy or trading authority.

## 10. Datasets and experiments

Datasets are immutable/versioned first-class records with source, time range, schema/features, row count, content identity and consumers.

Experiments capture hypothesis, baseline, variant, dataset, evaluation plan, results, status and links to resulting model artifacts. The UI should make provenance obvious enough that filenames such as `final_final_v2.parquet` are never the primary identity.

## 11. Infrastructure

One operational screen covers:

- Synology persistent runtime;
- local training PC;
- Ollama service;
- market-data services;
- workers/collectors;
- storage/freshness;
- service health and restart/recovery state.

Infrastructure controls must remain clearly separated from research/model controls.
