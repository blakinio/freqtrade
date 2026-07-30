# Timestamp and Leakage Worker Prompt

Paste the complete text below into a separate agent chat only when the closure dispatch table authorizes `FTAI-20260730-closure-time-leakage`.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako agent poprawności czasowej i ochrony przed leakage.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-time-leakage.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- task-relevant time semantics, feature/simulator contracts and tests.

## Cel

Zamknij tylko udowodnione braki dotyczące point-in-time correctness, closed-bar processing i leakage guards. Nie przejmuj implementacji wskaźników, symulatora ani shared contracts poza przydzielonymi plikami.

## Potencjalny zakres — tylko zgodnie z child taskiem

- closed-bar scheduler;
- UTC and timezone-aware validation;
- `event_time`, `detected_at`, `available_at`, `decision_time` ordering;
- confirmed HTF semantics;
- point-in-time feature snapshots;
- append-only deterministic replay;
- timestamp-order guard;
- HTF, pivot, future-shift and target-leakage guards;
- negative tests proving unavailable/future data cannot affect a decision.

## Wymagania

- Najpierw rozpoznaj istniejące canonical semantics i nie duplikuj ich.
- Każdy wynik musi być deterministyczny dla tych samych danych, czasu i wersji.
- Pivot staje się dostępny dopiero po wymaganym confirmation window.
- HTF może być użyty dopiero po potwierdzonym zamknięciu.
- `available_at > decision_time` musi fail-closed.
- Replay nie może przepisywać historycznych evidence records.
- Nie zmieniaj formuł cech poza minimalnym interfejsem koniecznym dla poprawności czasowej i tylko w owned paths.

## Akceptacja

- wszystkie przydzielone `REAL_GAP` są pokryte kodem i testami;
- pozytywne i negatywne point-in-time fixtures przechodzą;
- brak lookahead/future leakage w testach;
- replay daje identyczny canonical result/hash;
- wymagane Python/AI Strategy/AI Platform CI przechodzą;
- focused PR jest scalony normalnie;
- task checkpoint zawiera dokładnie jeden kolejny krok.

Działaj autonomicznie aż bounded task będzie kompletny albo pojawi się konkretny shared-contract blocker.
