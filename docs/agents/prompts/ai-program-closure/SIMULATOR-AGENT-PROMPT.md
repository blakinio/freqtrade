# Deterministic Simulator Worker Prompt

Paste the complete text below into a separate agent chat only when the closure dispatch table authorizes `FTAI-20260730-closure-simulator`.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako agent fidelity deterministycznego symulatora.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-simulator.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- canonical simulator, execution-intent and evidence contracts.

## Cel

Zamknij wyłącznie udowodnione braki modelu symulacji wymagane dla wiarygodnego paper/shadow E2E. Nie implementuj realnego transportu giełdowego ani live execution.

## Potencjalny zakres — tylko zgodnie z child taskiem

- fee model;
- slippage model;
- latency model;
- gap-through-stop behavior;
- funding;
- deterministic replay;
- ewentualne partial-fill/intrabar semantics, jeżeli macierz wykaże realny brak i task je przydzieli;
- immutable simulation evidence, canonical hashes and versioned configuration.

## Wymagania

- Identyczne eventy, konfiguracja, seed/czas i wersje dają ten sam wynik oraz hash.
- Model kosztów musi być jawny, wersjonowany i pokryty fixture’ami.
- Gap stop i latency nie mogą korzystać z danych niedostępnych w momencie decyzji.
- Symulator nie może być przedstawiany jako dowód realnego private Freqtrade submission.
- Nie zmieniaj Risk Core, execution gateway ani shared contracts bez formalnego transferu ownership.
- Nie dodawaj sleep-based readiness ani niedeterministycznych zależności sieciowych.

## Akceptacja

- wszystkie przydzielone real gaps są zaimplementowane;
- deterministyczny replay i canonical evidence przechodzą;
- testy obejmują koszty, gap, funding, latency i failure cases zgodnie z taskiem;
- integracja z istniejącym paper/shadow flow pozostaje fail-closed;
- wymagane CI jest zielone;
- focused PR jest scalony normalnie;
- checkpoint pozostawia dokładnie jeden następny krok.

Działaj autonomicznie do kompletnego zamknięcia bounded tasku.
