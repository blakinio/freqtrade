# Inwestycja — AI Strategy Engine Foundation

Wersjonowany pakiet architektury, kontraktów i referencyjnych implementacji dla modułu tworzenia oraz optymalizacji strategii używanego przez Portal, prywatny Freqtrade, boty klasyczne, boty likwidacyjne i AI Research Engine.

## Zasada bezpieczeństwa

Model AI nie wdraża dowolnego kodu do bota. Operuje wyłącznie na zatwierdzonym `Feature Registry`, deklaratywnym `Strategy DSL` i ograniczonych przestrzeniach parametrów. Każdy kandydat przechodzi:

```text
schema validation
→ point-in-time/leakage validation
→ deterministic replay
→ walk-forward
→ frozen out-of-sample
→ robustness and cost stress
→ shadow/paper trading
→ Risk Core approval
→ limited-capital deployment
```

## Zakres zapisany w pakiecie

- architektura Browser → Portal BFF/API → Control Plane → Risk Core → private Freqtrade;
- kontrakty `FeatureRecord`, `SignalEvent` i Strategy DSL;
- semantyka `event_time`, `detected_at`, `available_at`;
- Squeeze corrected i testowy legacy-bug-compatible;
- Supertrend, MACD SMA/EMA, confirmed pivots i geometria świec;
- RSI, Stochastic RSI, ROC, WaveTrend-style research feature;
- VWAP, ADX, PSAR i niezależny Fibonacci MA ensemble;
- MFI, wolumenowy EMA oscillator i robust volume z-score;
- niezależny ATR Range Filter research prototype;
- no-repeat/cooldown policy, partial TP i ograniczone DCA;
- pełna mapa `Miyagi UI → internal feature/policy/search space`;
- clean-room granice dla SMC/LuxAlgo;
- przykładowe strategie klasyczne, likwidacyjne, 10-in-1-inspired i Bonsai-inspired;
- backlog P0/P1/P2, testy i prompt dla kolejnego agenta.

## Czego pakiet nie robi

- nie kopiuje kodu LuxAlgo;
- nie twierdzi, że odtwarza zamknięte skrypty Miyagi 1:1;
- nie używa TradingView jako produkcyjnego execution feed;
- nie otwiera ścieżki do live capital;
- nie uznaje domyślnych parametrów za rekomendację inwestycyjną.

## Struktura

- `ARCHITECTURE.md` — docelowa architektura i granice odpowiedzialności;
- `AGENT_MASTER_PROMPT.md` — prompt wykonawczy;
- `TASKS.md` — dependency-ordered backlog;
- `docs/TECHNICAL_AUDIT.md` — audyt skryptów i pułapek;
- `docs/MIYAGI_PARAMETER_MAP.md` — mapa wszystkich widocznych elementów Miyagi;
- `docs/AI_ADAPTATION_POLICY.md` — zasady nauki, adaptacji i promocji;
- `configs/feature_registry.v1.yaml` — katalog cech;
- `configs/search_spaces.v1.yaml` — constrained optimization spaces;
- `configs/miyagi_parameter_map.v1.yaml` — mapowanie provenance;
- `schemas/` — kontrakty JSON Schema;
- `src/strategy_engine/` — referencyjne implementacje i guardrails;
- `tests/` — unit i contract E2E.

## Uruchomienie

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check .
mypy src/strategy_engine
```

## Status

Foundation/research-only. Następny agent ma najpierw wykonać inventory istniejących modułów repo i zintegrować komponenty bez duplikowania portalu, WickHunter, liquidation data layer ani istniejących kontraktów.
