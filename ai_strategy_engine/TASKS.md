# Backlog wdrożeniowy

## P0 — poprawność i bezpieczeństwo

### P0.1 Domain contracts

- [ ] `FeatureRecord`
- [ ] `SignalEvent`
- [ ] `StrategyDefinition`
- [ ] `Experiment`
- [ ] `ValidationReport`
- [ ] JSON Schema publishing
- [ ] idempotency

### P0.2 Timestamp-safe Feature Engine

- [ ] closed-bar scheduler
- [ ] UTC validation
- [ ] `event_time/detected_at/available_at`
- [ ] HTF confirmation
- [ ] point-in-time feature snapshots
- [ ] append-only replay

### P0.3 Core features

- [x] referencyjne RSI/Stochastic RSI/ROC
- [x] referencyjne VWAP/ADX/MFI/volume features
- [x] research WaveTrend/PSAR/FIB MA/ATR Range Filter
- [x] no-repeat policy i position-management guards

- [ ] ATR RMA/SMA
- [ ] SMA/EMA
- [ ] BB/KC
- [ ] Squeeze corrected
- [ ] Squeeze legacy comparison
- [ ] linreg momentum
- [ ] Supertrend
- [ ] MACD SMA/EMA signal
- [ ] candle geometry
- [ ] robust volume
- [ ] confirmed pivots
- [ ] support/resistance

### P0.4 Leakage Guard

- [ ] timestamp order
- [ ] HTF guard
- [ ] pivot guard
- [ ] future-shift guard
- [ ] target leakage guard
- [ ] OOS freeze guard

### P0.5 Deterministic Simulator core

- [ ] fee model
- [ ] slippage model
- [ ] latency model
- [ ] gap stop
- [ ] funding
- [ ] deterministic replay

## P1 — badania i automatyzacja

### P1.1 Strategy DSL

- [ ] JSON Schema
- [ ] typed AST
- [ ] validator
- [ ] compiler
- [ ] Freqtrade adapter contract

### P1.2 Experiment Store

- [ ] data/code/config hashes
- [ ] trial lineage
- [ ] metrics
- [ ] artifact storage
- [ ] comparison API

### P1.3 Optuna service

- [ ] constrained search spaces
- [ ] forbidden combinations
- [ ] pruning
- [ ] robustness score
- [ ] stability analysis

### P1.4 Liquidation data layer

- [ ] liquidation aggregation
- [ ] OI alignment
- [ ] funding alignment
- [ ] deduplication
- [ ] latency metadata
- [ ] cross-exchange confirmation

### P1.5 Market structure research

- [ ] clean-room BOS/CHoCH
- [ ] HH/HL/LH/LL
- [ ] EQH/EQL
- [ ] confirmed FVG
- [ ] own zone heuristic
- [ ] no LuxAlgo code copy

## P2 — AI i portal

### P2.1 AI Candidate Generator

- [ ] schema-constrained output
- [ ] registry-only features
- [ ] mandatory falsification test
- [ ] complexity limits

### P2.2 Regime Router

- [ ] trend/range
- [ ] high/low volatility
- [ ] liquidation regime
- [ ] drift monitoring

### P2.3 Ensemble Ranker

- [ ] correlation penalties
- [ ] OOS stability
- [ ] drawdown contribution
- [ ] calibration

### P2.4 Signal Wizard

- [ ] feature selection
- [ ] parameter constraints
- [ ] leakage warnings
- [ ] strategy preview
- [ ] experiment submit

### P2.5 Strategy Catalog

- [ ] version history
- [ ] approvals
- [ ] deployments
- [ ] rollback
- [ ] provenance

## Dependency-ordered integration packages

### ASE-00 — inventory, contracts and synthetic vertical slice

- [x] zinwentaryzuj istniejące moduły i ownership paths;
- [x] nie duplikuj WH-00/WH-01, portalu ani liquidation contracts;
- [x] dopasuj `FeatureRecord`, `SignalEvent` i Strategy DSL do istniejących kontraktów;
- [x] uruchom syntetyczny shadow-only flow data → feature → DSL → leakage guard → fail-closed risk → evidence;
- [x] dodaj checkpoint, testy i osobny PR.

### ASE-01 — TradingView Strategy Lab

- [x] dodaj wersjonowane clean-room DSL dla Supertrend i Squeeze Momentum;
- [x] uruchom deterministyczny closed-bar / next-bar-open backtest bez lookahead;
- [x] zapisz tenant-scoped wynik eksperymentu z hashami, transakcjami i wyjaśnieniami;
- [x] wystaw bezpieczne Experiment API oraz widok `Testy / Laboratorium`;
- [x] dodaj porównanie wariantów, testy negatywne, E2E i trwały checkpoint.

### ASE-FR-01 — Feature Registry service

Nazwa została wydzielona z wcześniejszego ogólnego wpisu `ASE-01`, aby nie kolidowała z jednoznacznie zleconym pakietem TradingView Strategy Lab.

- [ ] loader, schema, dependency resolver i API listing;
- [ ] parity fixtures i append-only replay tests;
- [ ] portal read model bez execution write path.

### ASE-02 — constrained research and optimization

- [ ] immutable dataset manifest i locked final holdout;
- [ ] Optuna constraints, trial lineage i robustness score;
- [ ] AI candidate generator restricted to registry and DSL.

### ASE-03 — paper/shadow integration

- [ ] simulator parity;
- [ ] Risk Core approval;
- [ ] private Freqtrade adapter w trybie paper/shadow;
- [ ] E2E audit trail i rollback.
