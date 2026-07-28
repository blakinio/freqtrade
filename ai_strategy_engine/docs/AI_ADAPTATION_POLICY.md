
# Polityka adaptacji i optymalizacji przez AI

## Dozwolone

Model może:

- wybierać cechy oznaczone `approved_for_ai: true`;
- proponować kombinacje warunków w Strategy DSL;
- dobierać parametry w wersjonowanych search spaces;
- proponować osobne konfiguracje dla instrumentu, interwału i reżimu;
- rankować kandydatów według wyników OOS, stabilności i kosztów;
- proponować ponowny eksperyment po wykryciu driftu.

## Zabronione

Model nie może:

- użyć cechy przed `available_at`;
- aktywować niepotwierdzonej świecy HTF;
- zmienić Risk Core ani maksymalnej ekspozycji;
- wdrożyć strategii bez walidacji, paper tradingu i approval;
- optymalizować na zablokowanym final holdout;
- generować dowolnego kodu wykonawczego do produkcji;
- traktować ustawień domyślnych Miyagi jako rekomendowanych;
- kopiować kodu LuxAlgo lub prywatnego skryptu.

## Adaptacja

Adaptacja nie oznacza ciągłego strojenia live. Jest wersjonowanym cyklem:

```text
frozen dataset manifest
→ candidate generation
→ constrained optimization
→ walk-forward
→ final holdout once
→ paper/shadow
→ approval
→ immutable deployment manifest
```

Każde ponowne strojenie tworzy nową wersję strategii i eksperymentu. Działający bot nie zmienia parametrów in-place.

## Kryterium promocji

Kandydat musi wykazać:

- dodatni wynik netto po fee, slippage, funding i latency;
- spójność w wielu foldach, instrumentach i reżimach;
- stabilność w sąsiedztwie parametrów;
- brak leakage i pełny deterministic replay;
- akceptowalny drawdown i tail risk;
- przejście shadow/paper bez rozbieżności względem simulatora.
