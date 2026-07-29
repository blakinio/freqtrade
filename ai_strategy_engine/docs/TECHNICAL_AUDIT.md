
# Techniczny audyt źródeł strategii

## Zakres

Audyt obejmuje Miyagi 10-in-1, Miyagi Bonsai, Squeeze Momentum, Supertrend, Smart Money Concepts, Support/Resistance with Breaks oraz CM_Ult_MACD_MTF.

## Decyzje

| Źródło | Decyzja | Uzasadnienie |
|---|---|---|
| Squeeze Momentum | independent reimplementation | deterministyczne obliczenia; znaleziony błąd parametru BB |
| Supertrend | independent reimplementation | użyteczny jako regime/exit, nie jako samodzielny edge |
| MACD MTF | independent reimplementation | confirmed HTF i jawny SMA/EMA signal |
| Pivot S/R | independent reimplementation | poziom aktywny dopiero po potwierdzeniu |
| SMC | clean-room research only | opóźnione pivoty, chart backfill, MTF lookahead risk, licencja LuxAlgo |
| Miyagi | research hypothesis source | brak kodu, brak parity i repaint proof |
| TradingView alerts | benchmark/research only | nie są produkcyjnym execution backbone |

## Squeeze Momentum

- `BB MultFactor` jest zadeklarowany, ale w dostarczonym kodzie nie jest używany.
- Odchylenie BB jest mnożone przez `multKC`, co sprzęga szerokość BB i KC.
- Implementacja utrzymuje dwa warianty: `corrected` i wyłącznie testowy `legacy_bug_compatible`.
- `legacy_bug_compatible` jest zabroniony w produkcji.
- `sqzOn` oznacza pełne zawarcie BB w KC; `sqzOff` pełne wyjście; częściowe przecięcie jest osobnym stanem.

Test falsyfikujący: poprawiony squeeze musi przewyższyć time-matched baseline po kosztach na zamrożonym OOS i nie może opierać wyniku na jednym ostrym optimum parametrów.

## Supertrend

- Stanowe pasma są rekurencyjne.
- Flip jest dostępny po potwierdzeniu świecy w baseline.
- Gap przez pasmo nie może być wypełniany po idealnej cenie pasma.
- ATR RMA i SMA są osobnymi wersjami algorytmu.

Test falsyfikujący: porównać brak filtra, filtr direction oraz trailing exit; zaakceptować tylko poprawę risk-adjusted OOS po realistycznym gap/slippage modelu.

## MACD MTF

- Dostarczony kod używa SMA jako signal line, nie EMA.
- Bieżąca świeca HTF może zmieniać wartość do zamknięcia.
- Nasz feature publikuje HTF wyłącznie jako confirmed i dopiero po jego `available_at`.

Test falsyfikujący: LTF baseline kontra confirmed HTF, z opóźnieniem i bez wykorzystania bieżącego HTF.

## Pivot Support/Resistance

- Pivot wymaga `rightBars` przyszłych świec do potwierdzenia.
- Ujemny offset cofa rysunek, nie moment wiedzy.
- `fixnan` utrzymuje poziom i zaciera moment jego aktywacji.
- Warunki knotów zostały zastąpione jawnymi `body_ratio`, `upper_wick_ratio`, `lower_wick_ratio`.

Test falsyfikujący: breakout może używać poziomu dopiero po `available_at`; wynik musi przetrwać dodatkowe opóźnienie i koszty.

## Smart Money Concepts

- BOS/CHoCH są heurystykami opartymi o potwierdzone pivoty i bias.
- Order block w kodzie jest algorytmicznie wybraną ekstremalną świecą, a nie dowodem instytucjonalnego order flow.
- Backfill boxów może wizualnie sugerować wiedzę ex ante.
- MTF FVG oraz poziomy wymagają niezależnego testu granic timeframe i braku lookahead.
- Kod LuxAlgo nie jest kopiowany ani portowany.

Test falsyfikujący: clean-room BOS/CHoCH/FVG musi mieć incremental edge ponad prosty confirmed-pivot breakout i zachować replay stability.

## Miyagi

Potwierdzone są tylko elementy widoczne w materiałach. Dokładne wzory, kolejność filtrów, repaint, MTF, exits i alert parity pozostają nieznane. W systemie mapujemy koncepcje do własnych komponentów, a `Miyagi` zapisujemy jedynie w provenance eksperymentu.

## Semantyka czasu

Każdy event przechowuje:

- `event_time` — czas świecy lub zdarzenia rynkowego;
- `detected_at` — pierwszy moment, gdy obliczenie było możliwe;
- `available_at` — pierwszy moment użycia przez strategię.

Decyzja jest ważna tylko, gdy `available_at <= decision_time`.
