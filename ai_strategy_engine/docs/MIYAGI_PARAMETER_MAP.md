
# Miyagi — mapa parametrów do komponentów wewnętrznych

Pełny kod Miyagi nie został udostępniony. Mapa nie jest implementacją zgodności. Rozdziela fakty widoczne w UI/opisie od niezależnych komponentów, które można badać w naszym systemie.

## Klasy pewności

- `confirmed_ui` — parametr lub funkcja widoczna w materiałach użytkownika.
- `probable` — prawdopodobna rola, ale brak kodu uniemożliwia potwierdzenie.
- `unknown` — dokładna formuła, kolejność albo semantyka pozostaje nieznana.

## Miyagi 10-in-1 + Alerts

| Element | Status | Reprezentacja u nas | Rola | Decyzja |
|---|---|---|---|---|
| EMA | confirmed_ui | `ema` dependency / trend features | trend, regime | BUILD generic |
| MACD | confirmed_ui | `macd.v1` | momentum, trigger | BUILD |
| RSI | confirmed_ui | `rsi.v1` | momentum, filter | BUILD |
| Stochastic RSI | confirmed_ui | `stoch_rsi.v1` | oscillator state | BUILD |
| VWAP | confirmed_ui | `vwap.v1` | location, regime | BUILD |
| TTM/Squeeze | confirmed_ui | `squeeze_ratio.v1`, `linreg_momentum.v1` | volatility regime | BUILD corrected |
| ADX | confirmed_ui | `adx.v1` | trend strength | BUILD |
| Supertrend | confirmed_ui | `supertrend_direction.v1` | regime, exit | BUILD |
| MFI | confirmed_ui | `mfi.v1` | price-volume momentum | BUILD |
| ROC | confirmed_ui | `roc.v1` | momentum | BUILD |
| WaveTrend | confirmed_ui | `wavetrend.v1` | research oscillator | RESEARCH |
| PSAR | confirmed_ui | `psar.v1` | trend/exit | RESEARCH |
| price action | confirmed_ui | `candle_geometry.v1`, confirmed pivots | confirmation | BUILD |
| no-repeat signals | confirmed_ui | `no_repeat_signals` policy | dedup/cooldown | BUILD |
| alerty | confirmed_ui | `SignalEvent` contract | integration | BUILD internally |
| weighted voting | probable | `ensemble_score.v1` | ensemble | RESEARCH |
| kolejność filtrów | unknown | jawna w Strategy DSL | strategy semantics | do ustalenia eksperymentalnie |
| repaint/HTF | unknown | closed-bar / confirmed-HTF only | safety | nie ufać źródłu |

## Miyagi Bonsai

| Element | Status | Reprezentacja u nas | Rola | Decyzja |
|---|---|---|---|---|
| ATR Range Filter | confirmed_ui | `atr_range_filter.v1` | regime/trigger | RESEARCH independent |
| FIB MA | confirmed_ui | `fib_ma_ensemble.v1` | trend ensemble | RESEARCH; brak parity claim |
| volume filter | confirmed_ui | `volume_ema_osc.v1`, `volume_robust_z.v1` | confirmation | BUILD |
| RSI | confirmed_ui | `rsi.v1` | filter | BUILD |
| ADX | confirmed_ui | `adx.v1` | trend strength | BUILD |
| MFI | confirmed_ui | `mfi.v1` | volume/momentum | BUILD |
| time filter | confirmed_ui | `time_window` DSL/policy | eligibility | BUILD |
| TP/SL | confirmed_ui | Risk DSL | exit/risk | BUILD |
| trailing exit | confirmed_ui | Risk DSL | exit | BUILD |
| partial take profit | probable | `TakeProfitLevel` plan | position management | BUILD guarded |
| DCA | visible in related backtester | `DcaLevel` plan | position management | BUILD guarded |
| leverage | visible in related backtester | Risk Core constraint | exposure | BUILD deterministic |
| sizing | visible in related backtester | risk-fraction sizing | exposure | BUILD deterministic |
| dokładna FIB MA | unknown | brak | unknown | nie kopiować nazwy jako parity |
| dokładny ATR filter | unknown | brak | unknown | własna hipoteza, nie zgodność |

## Zasada dla AI

AI może używać wyłącznie naszych feature IDs, parametrów i wersji. Nazwa `Miyagi` pozostaje w provenance hipotezy, nigdy jako źródło wykonawcze ani gwarancja zgodności.
