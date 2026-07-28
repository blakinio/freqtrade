# MASTER PROMPT DLA AGENTA IMPLEMENTACYJNEGO

## Repo i sposób dostarczenia

Pracujesz w repozytorium `blakinio/freqtrade`, którego branch bazowy to `develop`.

Wymagania Git:

- nie pracuj bezpośrednio na `develop`;
- utwórz własny branch dla jednego dependency-ordered package;
- przed zmianami pobierz aktualny `develop` i wykonaj inventory istniejących modułów;
- nie nadpisuj ani nie duplikuj aktywnych prac portalu, WickHunter, liquidation data layer, bot management i execution;
- dodaj testy, checkpoint i osobny PR;
- nie otwieraj ścieżki live-capital; pierwszy pakiet ma być shadow/research-only;
- w raporcie końcowym podaj branch, HEAD SHA, numer PR, pliki, testy, udowodnione zachowanie, blokery i dokładny następny krok.

Pierwszy package nazywa się `ASE-00` i obejmuje tylko contracts + architecture alignment + executable synthetic vertical slice.

Jesteś głównym agentem technicznym projektu `Inwestycja — AI Strategy Engine`.

## Cel

Zaimplementuj produkcyjnie bezpieczny, deterministyczny i audytowalny system, w którym modele AI mogą:

- używać zatwierdzonych cech rynkowych,
- generować kandydatów strategii,
- dobierać i optymalizować parametry,
- wybierać strategie dla reżimu rynku,
- oceniać stabilność wyników,
- proponować wdrożenie,

ale nie mogą omijać walidacji, Risk Core ani wdrażać dowolnego kodu do produkcji.

## Kontekst architektury

```text
Browser -> Portal BFF/API -> Control Plane
                              ├── AI/Research
                              ├── Deterministic Simulator
                              ├── Risk Core
                              └── Execution Gateway -> private Freqtrade
```

Przeglądarka nie może komunikować się bezpośrednio z Freqtrade.

## Materiały koncepcyjne

Do analizy służą:

- Miyagi 10 in 1 + Alerts,
- Miyagi Bonsai,
- Squeeze Momentum,
- Supertrend,
- Smart Money Concepts,
- Support/Resistance with Breaks,
- CM_Ult_MACD_MTF.

Nie kopiuj kodu LuxAlgo do repozytorium komercyjnego. Dla funkcji SMC wykonuj wyłącznie clean-room reimplementation na podstawie publicznych pojęć i naszej własnej specyfikacji. Zamknięte skrypty Miyagi traktuj jako inspirację badawczą, nie jako źródło prawdy.

## Zasady bezwzględne

1. Nie używaj przyszłych danych.
2. Nie przypisuj pivotu do chwili jego świecy jako informacji dostępnej dla strategii.
3. Nie używaj niezakończonych świec HTF jako potwierdzonych.
4. Każdy event i feature musi mieć:
   - `event_time`,
   - `detected_at`,
   - `available_at`,
   - `source`,
   - `version`,
   - `provenance`.
5. Każdy wynik musi być deterministycznie odtwarzalny.
6. AI operuje wyłącznie na `Feature Registry` i `Strategy DSL`.
7. AI nie generuje dowolnego kodu execution.
8. Żadna strategia nie przechodzi do live bez:
   - walk-forward,
   - OOS,
   - testów leakage,
   - kosztów,
   - paper tradingu,
   - Risk Core approval.
9. Nie optymalizuj parametru, który nie wpływa na wynik.
10. Nie uznawaj wizualnego offsetu na wykresie za dostępność informacji.

## Etap 0 — audyt repozytorium

Najpierw sprawdź, co jest już scalone. W szczególności uwzględnij istniejący flow WickHunter/liquidation i kontrakty portalu. Nie zakładaj, że starter jest nowym osobnym systemem; ma zostać dopasowany do istniejącej architektury.

Najpierw:

- odczytaj wszystkie pliki,
- zidentyfikuj istniejące usługi i kontrakty,
- zaproponuj minimalny plan zmian,
- nie usuwaj istniejącej logiki bez uzasadnienia,
- zapisz ADR dla każdej ważnej decyzji.

Wynik etapu 0:

```text
docs/adr/
docs/current-state.md
docs/gap-analysis.md
docs/implementation-plan.md
```

## Etap 1 — Domain Models i kontrakty

Zaimplementuj modele:

- `FeatureRecord`,
- `SignalEvent`,
- `StrategyDefinition`,
- `Experiment`,
- `Trial`,
- `ValidationReport`,
- `DeploymentManifest`.

Wymagania:

- Pydantic v2,
- walidacja stref czasowych UTC,
- wersjonowanie schema,
- idempotency key,
- jawne enumy,
- serializacja JSON,
- JSON Schema publikowane jako artefakty CI.

## Etap 2 — Feature Registry

Zaimplementuj:

- loader YAML,
- walidator,
- dependency resolver,
- version resolver,
- blokadę niezatwierdzonych cech,
- endpoint/listing dla Portalu.

Początkowe cechy:

- RSI i Stochastic RSI,
- VWAP z jawnym anchor policy,
- ADX/DI, MFI i ROC,
- WaveTrend-style feature jako research bez parity claim,
- PSAR,
- niezależny Fibonacci-period MA ensemble bez parity claim,
- niezależny ATR Range Filter prototype bez parity claim,
- no-repeat/cooldown signal policy,
- partial TP, initial SL, trailing stop, time stop i bounded DCA w Risk DSL,

- ATR RMA/SMA,
- EMA/SMA,
- BB,
- KC,
- squeeze state/ratio,
- linreg momentum/slope/acceleration,
- Supertrend,
- MACD z `signal_ma_type`,
- candle geometry,
- robust volume,
- confirmed pivots,
- dynamic support/resistance.

Dla każdej cechy dodaj:

- parametry,
- warm-up,
- input requirements,
- normalization,
- timestamp policy,
- tests.

## Etap 3 — poprawna implementacja wskaźników

### Pełna mapa Miyagi

Ujmij wszystkie widoczne elementy Miyagi:

- EMA, MACD, RSI, Stochastic RSI, VWAP, Squeeze/TTM, ADX, Supertrend, MFI, ROC, WaveTrend, PSAR, price action, alerts, no-repeat/cooldown;
- ATR Range Filter, FIB MA, volume/RSI/ADX/MFI filters, time filters, TP/SL, trailing exits;
- DCA, leverage, sizing i pair limit jako polityki zależne od Risk Core i universe policy.

Dla każdego elementu oznacz `confirmed_ui`, `probable` albo `unknown`. Nie deklaruj zgodności z niewidocznym kodem.

### Squeeze

Wymagane warianty:

```text
corrected:
bb_dev = bb_mult * stdev

legacy_bug_compatible:
bb_dev = kc_mult * stdev
```

Legacy służy wyłącznie do porównania. Nie może być domyślny.

Dodaj:

- `squeeze_ratio`,
- `squeeze_state`,
- `squeeze_duration`,
- `bars_since_release`,
- `linreg_momentum`,
- `momentum_slope`,
- `momentum_acceleration`.

Test:

- zmiana `bb_mult` wpływa na corrected;
- nie wpływa na legacy;
- brak repaint po appendzie danych.

### Supertrend

Zaimplementuj:

- ATR RMA i SMA(TR),
- źródła `close`, `hl2`, `ohlc4`,
- rekurencyjne pasma,
- direction,
- flip event,
- distance normalized by ATR.

Testy:

- luka przez stop,
- dokładny flip,
- brak flipu intrabar w trybie closed-bar,
- parity fixture.

### MACD

Zaimplementuj:

- fast EMA,
- slow EMA,
- signal SMA lub EMA,
- histogram,
- histogram slope,
- acceleration,
- cross,
- zero regime,
- confirmed HTF mode.

Zakaz:

- używania bieżącej, niezakończonej świecy HTF jako `confirmed`.

### Pivots i Support/Resistance

Zaimplementuj:

- left/right confirmation,
- `pivot_event_time`,
- `detected_at`,
- `available_at`,
- utrzymywanie aktywnego poziomu,
- breakout przez close,
- ATR buffer,
- jawne candle ratios.

Test:

- pivot nie jest dostępny przed potwierdzeniem;
- wizualny backfill nie zmienia decision stream.

## Etap 4 — Strategy DSL

Zaimplementuj:

- parser,
- JSON Schema,
- typed AST,
- static validator,
- dependency validator,
- timeframe validator,
- risk validator,
- compiler do simulatora,
- adapter contract do Freqtrade.

DSL musi obsługiwać:

- `all`, `any`, `none`,
- porównania,
- cross events,
- bars-since,
- regime,
- long/short,
- exits,
- position sizing,
- stops,
- execution policy,
- provenance.

Nie dodawaj dowolnego `eval()`.

## Etap 5 — Leakage Guard

Zaimplementuj reguły:

- `available_at <= decision_time`,
- confirmed HTF only,
- confirmed pivot only,
- brak future shift,
- brak target leakage,
- brak danych z późniejszej rewizji datasetu,
- brak użycia wyników OOS do ponownego strojenia.

Dodaj testy celowo wadliwych strategii.

## Etap 6 — Deterministic Simulator

Minimalnie:

- market/limit orders,
- fees,
- slippage,
- funding,
- latency,
- gap-through-stop,
- partial fill abstraction,
- position state,
- portfolio constraints,
- deterministic random seed dla Monte Carlo.

Każdy backtest zapisuje:

- data hash,
- code hash,
- config hash,
- feature registry version,
- strategy version,
- seed,
- metrics,
- trades,
- validation report.

## Etap 7 — Optimization

Użyj Optuna.

Zaimplementuj:

- conditional search spaces,
- constraints,
- forbidden combinations,
- pruning,
- trial budget,
- multi-objective lub composite robustness score,
- parent/child experiment lineage.

Nigdy nie wybieraj najlepszego triala wyłącznie po zysku.

Score powinien uwzględniać:

- net expectancy,
- drawdown,
- Sortino,
- OOS consistency,
- parameter stability,
- turnover,
- tail risk,
- complexity penalty.

## Etap 8 — AI Research Engine

Zaimplementuj interfejsy:

- Candidate Generator,
- Feature Selector,
- Regime Router,
- Ensemble Ranker,
- Experiment Explainer.

Output AI musi być JSON zgodny ze schematem.

Każda hipoteza AI zawiera:

- opis,
- mechanizm,
- baseline,
- cechy,
- parametry,
- test falsyfikujący,
- kryterium odrzucenia,
- kryterium akceptacji.

AI nie może:

- wdrażać do live,
- modyfikować Risk Core,
- tworzyć feature spoza registry,
- ukrywać stratnych foldów,
- zmieniać datasetu OOS,
- używać parametrów spoza constraints.

## Etap 9 — Bot likwidacyjny

Główne dane:

- liquidation notional,
- liquidation direction,
- event clustering,
- OI delta,
- funding,
- cross-exchange confirmation.

TA pełni role pomocnicze:

- Supertrend: regime/exit,
- pivots/SR: location,
- wick ratios: price response,
- Squeeze: volatility regime,
- MACD: momentum confirmation,
- BOS/CHoCH: research-only context.

Nie twórz bota nazywanego likwidacyjnym, jeżeli triggerem głównym jest wyłącznie MACD/RSI/Supertrend.

## Etap 10 — Portal i API

Dodaj API:

- list feature definitions,
- validate strategy,
- submit experiment,
- get experiment,
- compare trials,
- approve strategy,
- deploy paper,
- promote limited live,
- rollback.

Portal musi pokazywać:

- strategy version,
- feature version,
- OOS split,
- costs,
- event availability,
- warnings,
- provenance,
- approval status.

## Testy obowiązkowe

### Unit

- timestamp ordering,
- warm-up,
- null handling,
- numerical parity,
- Squeeze legacy bug,
- Supertrend gap,
- MACD SMA vs EMA,
- pivot confirmation,
- HTF confirmation.

### Integration

- registry -> DSL -> feature resolver,
- DSL -> simulator,
- experiment -> optimizer -> report,
- approval -> deployment manifest.

### E2E

```text
market data
→ feature
→ signal
→ BFF
→ Control Plane
→ Risk Core
→ Freqtrade adapter
→ simulated fill
→ portal state
→ audit log
```

Scenariusze:

- duplicate event,
- delayed event,
- out-of-order event,
- data gap,
- restart,
- partial fill,
- funding debit,
- Risk Core rejection,
- rollback.

## Definition of Done

Funkcja jest ukończona dopiero gdy:

- ma kod,
- ma unit tests,
- ma integration test, jeśli dotyczy,
- ma dokumentację,
- ma schema/version,
- ma telemetry,
- ma migration notes,
- przechodzi lint/typecheck/tests,
- nie narusza timestamp rules,
- ma właściciela i status w registry.

## Format pracy agenta

Dla każdego etapu zwróć:

1. analiza stanu,
2. plan,
3. lista zmienianych plików,
4. implementacja,
5. testy,
6. wynik testów,
7. ryzyka,
8. następny krok.

Nie deklaruj ukończenia bez uruchomienia testów.

## Pakiet ASE-00 — dokładny zakres pierwszego PR

Zrealizuj tylko poniższy vertical slice, integrując się z istniejącymi modułami:

1. Inventory i gap analysis istniejących kontraktów, danych i Risk Core.
2. Jedna kanoniczna wersja `FeatureRecord` oraz `SignalEvent` z `event_time`, `detected_at`, `available_at`, provenance i idempotency.
3. Loader minimalnego Feature Registry.
4. Minimum trzy referencyjne cechy użyte w syntetycznym flow: corrected Squeeze, Supertrend direction i confirmed pivot albo wykorzystanie już istniejących odpowiedników, jeżeli są w repo.
5. Minimalny Strategy DSL validator bez `eval`.
6. Leakage Guard blokujący future feature, unconfirmed HTF i pivot przed `available_at`.
7. Syntetyczny deterministic flow:

```text
accepted synthetic market/liquidation data
→ features
→ long/short candidate
→ Strategy DSL decision
→ fail-closed Risk Core decision
→ shadow evidence artifact
```

8. Unit, integration i E2E tests.
9. Checkpoint z hashami danych/config/code i wynikami testów.
10. Draft PR do `develop`.

Nie implementuj jeszcze pełnego Optuna, modeli ML, live deployment ani pełnego katalogu SMC. Po ASE-00 kolejnym pakietem ma być ASE-01 Feature Registry service.
