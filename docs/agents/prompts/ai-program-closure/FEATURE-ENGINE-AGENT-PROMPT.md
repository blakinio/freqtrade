# Core Feature Engine Worker Prompt

Paste the complete text below into a separate agent chat only when the closure dispatch table authorizes `FTAI-20260730-closure-feature-engine`.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako agent domknięcia Feature Engine.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-feature-engine.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- Feature Registry architecture, canonical feature interfaces and parity fixtures.

## Cel

Zaimplementuj wyłącznie brakujące, zatwierdzone cechy sklasyfikowane jako `REAL_GAP`, z deterministycznymi fixture’ami, timestamp semantics i wpisami registry. Nie twórz nowych strategii ani execution logic.

## Potencjalny zakres — wyłącznie z child tasku

- ATR RMA/SMA;
- SMA/EMA;
- Bollinger Bands/Keltner Channels;
- corrected Squeeze and legacy comparison;
- linear-regression momentum;
- Supertrend;
- MACD with SMA/EMA signal;
- candle geometry;
- robust volume;
- confirmed pivots;
- support/resistance events;
- wymagane registry definitions, dependency metadata and parity fixtures.

## Wymagania

- Sprawdź, czy dana cecha nie jest już zaimplementowana pod inną canonical nazwą.
- Używaj jednego referencyjnego algorytmu, jawnej wersji i jawnych parametrów.
- Każda cecha ma warm-up, required inputs, normalization, timestamp/confirmation policy i leakage risk.
- AI może używać jej tylko po jawnej registry approval.
- Potwierdzone pivoty i support/resistance nie mogą repaintować ani używać przyszłych świec przed `available_at`.
- Nie kopiuj kodu z zamkniętych skryptów TradingView/LuxAlgo ani innych proprietary źródeł.
- Nie zmieniaj shared registry schema bez kontraktowego ownership transfer.

## Akceptacja

- wszystkie przydzielone real gaps mają implementację, registry record i testy;
- numerical fixtures pokrywają edge cases oraz warianty parametrów;
- parity/replay jest deterministyczne;
- timestamp/leakage invariants przechodzą;
- Ruff, mypy, compile i wymagane CI są zielone;
- focused PR jest scalony normalnie;
- checkpoint kończy się dokładnie jedną akcją.

Działaj autonomicznie do pełnego zamknięcia przydzielonego zakresu.
