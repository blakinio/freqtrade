# Architektura AI Strategy Engine

## 1. Kontekst systemu

```text
Browser / Portal UI
        │
        ▼
Portal BFF / API
        │
        ├── Strategy Catalog
        ├── Signal Wizard
        ├── Experiment UI
        ├── Bot Management
        └── Terminal API/UI
        │
        ▼
Control Plane
        │
        ├── Strategy Compiler
        ├── Deployment Manager
        ├── Approval Workflow
        └── Version Registry
        │
        ├─────────────────────┐
        ▼                     ▼
AI / Research Layer      Risk Core
        │                     │
        ▼                     ▼
Deterministic Simulator  Execution Gateway
        │                     │
        ▼                     ▼
Experiment Store         Private Freqtrade
        │                     │
        ▼                     ▼
Data / Feature Layer     Exchange APIs
```

Przeglądarka nigdy nie komunikuje się bezpośrednio z Freqtrade. Wszystkie operacje przechodzą przez Portal BFF/API, Control Plane i Risk Core.

## 2. Warstwy

### 2.1 Data Ingestion

Źródła:

- OHLCV,
- trades,
- order book snapshots lub aggregated order flow,
- likwidacje,
- Open Interest,
- funding,
- exchange metadata,
- fees,
- instrument constraints.

Każdy rekord musi mieć:

- `event_time`,
- `received_at`,
- `available_at`,
- `source`,
- `symbol`,
- `schema_version`,
- `data_version`.

### 2.2 Feature Engine

Odpowiada za deterministyczne obliczanie cech.

P0:

- ATR,
- SMA/EMA,
- Bollinger Bands,
- Keltner Channels,
- Squeeze state,
- linreg momentum,
- Supertrend,
- MACD z SMA lub EMA signal,
- candle geometry,
- confirmed pivots,
- support/resistance events,
- robust volume features.

P1 research:

- BOS/CHoCH,
- HH/HL/LH/LL,
- equal highs/lows,
- FVG bez lookahead,
- clean-room market structure,
- order-block-like zones jako własna, opisana heurystyka.


### 2.2.1 Katalog komponentów inspirowanych materiałami TradingView

Komponenty zatwierdzone do implementacji referencyjnej:

- RSI i Stochastic RSI,
- VWAP z jawnym anchor policy,
- ADX/DI, MFI, ROC,
- WaveTrend-style oscillator jako research feature bez parity claim,
- PSAR,
- niezależny Fibonacci-period MA ensemble,
- niezależny ATR Range Filter prototype,
- no-repeat/cooldown signal policy,
- partial take profit, trailing stop, time stop, DCA i sizing jako polityki Risk DSL.

Nazwy Miyagi są przechowywane tylko w provenance hipotezy. Żaden komponent nie deklaruje zgodności 1:1 z zamkniętym skryptem.

### 2.3 Feature Registry

Registry jest źródłem prawdy o cechach. Dla każdej cechy przechowuje:

- identyfikator i wersję,
- wzór,
- parametry,
- warm-up,
- wymagane dane,
- normalizację,
- timestamp semantics,
- confirmation policy,
- dozwolone role,
- ryzyko leakage/repaint,
- ownera i status.

AI może używać wyłącznie cech oznaczonych `approved_for_ai: true`.

### 2.4 Strategy DSL

Strategia nie jest dowolnym plikiem Python generowanym przez model.

DSL opisuje:

- universe,
- features,
- regime,
- entry long/short,
- exit,
- risk,
- execution,
- provenance.

DSL jest walidowany, kompilowany do simulatora oraz adaptera Freqtrade.

### 2.5 AI Research Engine

Podmoduły:

1. `Candidate Generator`
2. `Feature Selector`
3. `Parameter Optimizer`
4. `Regime Router`
5. `Ensemble Ranker`
6. `Experiment Explainer`

AI nie ma prawa:

- pisać bezpośrednio do produkcyjnego repo execution,
- pomijać walidacji czasu,
- zmieniać limitów Risk Core,
- wdrażać strategii bez zatwierdzenia,
- używać niepotwierdzonych danych HTF,
- używać funkcji spoza registry.

### 2.6 Deterministic Simulator

Wymagania:

- event-driven,
- point-in-time correct,
- jawny model bar-close/intrabar,
- fees,
- slippage,
- funding,
- latency,
- partial fills,
- gap-through-stop,
- deterministic replay,
- data and code versioning.

### 2.7 Risk Core

Twarde limity:

- leverage,
- risk per trade,
- portfolio exposure,
- max daily loss,
- max drawdown,
- max open positions,
- symbol concentration,
- cooldown,
- kill switch,
- strategy health checks.

AI może proponować parametry ryzyka tylko w dozwolonym zakresie. Risk Core pozostaje deterministyczny.

### 2.8 Execution

Freqtrade pozostaje prywatnym silnikiem wykonawczym. Otrzymuje wyłącznie:

- zatwierdzoną wersję strategii,
- podpisany deployment manifest,
- signal/event lub skompilowaną logikę,
- limity Risk Core,
- konfigurację execution.

## 3. Semantyka czasu

Każdy feature/event:

```text
event_time    — czas zdarzenia rynkowego
detected_at   — kiedy system mógł je ustalić
available_at  — kiedy strategia mogła je wykorzystać
decision_time — czas decyzji strategii
sent_at       — wysłanie do execution
exchange_at   — potwierdzenie giełdy
```

Reguła:

```text
available_at <= decision_time <= sent_at <= exchange_at
```

Pivot:

```text
event_time   = świeca ekstremum
detected_at  = zamknięcie świecy po right_bars
available_at = detected_at + processing_latency
```

HTF:

```text
event_time   = zamknięcie świecy HTF
available_at = po potwierdzeniu zamknięcia HTF
```

## 4. Przepływ strategii

```text
User/AI proposal
      ↓
Strategy DSL
      ↓
JSON Schema validation
      ↓
Static constraints
      ↓
Timestamp/leakage guard
      ↓
Feature dependency resolution
      ↓
Deterministic backtest
      ↓
Walk-forward / OOS
      ↓
Robustness ranking
      ↓
Approval
      ↓
Paper trading
      ↓
Limited deployment
      ↓
Production monitoring
```

## 5. Podział repozytoriów

Rekomendowane granice:

```text
portal/
control-plane/
strategy-engine/
feature-engine/
simulator/
risk-core/
execution-gateway/
freqtrade-private/
data-platform/
quality-e2e/
```

Ten pakiet dotyczy `strategy-engine` z kontraktami do pozostałych usług.

## 6. Najważniejsze decyzje implementacyjne

- Python 3.12.
- Pydantic v2 dla modeli kontraktów.
- JSON Schema dla integracji między usługami.
- Polars lub Pandas dla badań; jedna implementacja referencyjna.
- Event store lub append-only PostgreSQL/ClickHouse dla provenance.
- MLflow lub własny Experiment Store.
- Optuna dla constrained optimization.
- OpenTelemetry dla śledzenia przepływu sygnału.
- Każda cecha i strategia wersjonowana.
- Żadnego `lookahead_on` lub odpowiednika bez formalnego dowodu poprawności.

## 7. Granice integracji z istniejącym repo

Pakiet nie może duplikować już istniejących komponentów portalu, WickHunter, liquidation data ingestion ani adaptera wykonawczego. Integracja zaczyna się od inventory i gap analysis. Pierwszy vertical slice pozostaje shadow-only i fail-closed:

```text
accepted market/liquidation data
→ point-in-time features
→ Strategy DSL decision
→ Leakage Guard
→ deterministic Risk Core decision
→ shadow evidence
```

Nie wolno otwierać zleceń live ani bezpośredniego Browser → Freqtrade.
