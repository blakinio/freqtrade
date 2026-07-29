# Decyzje techniczne

| Obszar | Decyzja |
|---|---|
| Feature Engine | BUILD |
| Strategy DSL | BUILD |
| Leakage Guard | BUILD P0 |
| Deterministic Simulator | BUILD |
| AI Candidate Generator | BUILD po P0/P1 |
| Supertrend | niezależna reimplementacja |
| Squeeze Momentum | niezależna reimplementacja; poprawiony i legacy wariant |
| MACD MTF | reimplementacja z confirmed HTF |
| Pivot S/R | reimplementacja z opóźnioną dostępnością |
| BOS/CHoCH | clean-room research |
| Order blocks | research, niski priorytet |
| FVG | research po usunięciu lookahead |
| Miyagi | inspiracja i benchmark, nie zależność |
| Alerty TradingView | nie jako produkcyjne źródło execution |
| Kod LuxAlgo | nie kopiować do komercyjnego repo bez odrębnej zgody |
| Kolory/etykiety | UI-only |

## Rozszerzenie Miyagi

| Obszar | Decyzja |
|---|---|
| RSI/Stoch RSI/VWAP/ADX/MFI/ROC | niezależne generic implementations |
| WaveTrend/PSAR | research until OOS evidence |
| ATR Range Filter | independent research, no Bonsai parity claim |
| FIB MA | own Fibonacci-period ensemble, no Bonsai parity claim |
| no-repeat/cooldown | deterministic signal policy |
| TP/SL/trailing/time stop | deterministic Risk DSL |
| DCA | only with max levels and max exposure |
| live adaptation | forbidden; new immutable strategy version required |
