# Walidacja i kryteria akceptacji

## Minimalny pipeline

- unit parity,
- deterministic replay,
- leakage tests,
- walk-forward,
- purged CV + embargo,
- out-of-sample,
- multi-asset,
- multi-regime,
- costs,
- Monte Carlo,
- parameter stability,
- paper trading.

## Strategia jest odrzucana, gdy

- edge znika po kosztach,
- wynik zależy od pojedynczego instrumentu,
- wynik zależy od pojedynczego parametru,
- dawny sygnał zmienia się po dołączeniu nowych danych,
- używa danych przed `available_at`,
- ma poprawę tylko in-sample,
- drawdown przekracza Risk Core,
- liczba transakcji jest zbyt mała dla wiarygodnej oceny,
- paper trading istotnie odbiega od symulacji bez wyjaśnienia.

## Strategia może przejść dalej, gdy

- dodatnia wartość oczekiwana po kosztach w większości foldów,
- stabilność sąsiednich parametrów,
- wynik utrzymuje się na więcej niż jednym instrumencie lub reżimie,
- brak leakage,
- replay jest deterministyczny,
- paper trading potwierdza założenia execution.
