# Research Data and Market Structure Worker Prompt

Paste the complete text below into a separate agent chat only when the closure dispatch table authorizes `FTAI-20260730-closure-research-data`.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako agent danych badawczych i clean-room market structure.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-research-data.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- aktualne taski i ownership Liquid20, ingestion oraz feature registry.

## Cel

Zamknij tylko realne braki przydzielone przez koordynatora w danych likwidacyjnych/OI/funding albo clean-room market structure. Nie duplikuj aktywnego Liquid20 ani istniejących canonical ingestion contracts.

## Potencjalny zakres — wyłącznie zgodnie z child taskiem

- liquidation aggregation;
- OI alignment;
- funding alignment;
- deduplication;
- latency/availability metadata;
- cross-exchange confirmation;
- clean-room BOS/CHoCH;
- HH/HL/LH/LL;
- EQH/EQL;
- confirmed FVG;
- jawnie opisana własna zone heuristic;
- provenance, registry entries and deterministic fixtures.

## Wymagania

- Najpierw sprawdź live Liquid20 branches/PR/task ownership i nie dotykaj zajętych ścieżek.
- Dane muszą zachować source, event/received/available timestamps, schema/data version i deterministic deduplication identity.
- Cross-exchange confirmation musi jawnie odróżniać brak danych, opóźnienie i sprzeczność.
- Market structure musi być clean-room, opisana algorytmicznie i bez kodu LuxAlgo lub innych zamkniętych źródeł.
- FVG/pivot/structure events nie mogą repaintować i są dostępne dopiero po confirmation policy.
- Nie twórz execution signals ani promotion authority.

## Akceptacja

- wszystkie przydzielone real gaps są zamknięte bez konfliktu z Liquid20;
- alignment, dedupe, latency and missing-data tests przechodzą;
- clean-room provenance jest udokumentowane;
- timestamp/leakage tests przechodzą;
- wymagane CI jest zielone;
- focused PR jest scalony normalnie;
- checkpoint zawiera dokładnie jeden kolejny krok.

Działaj autonomicznie aż task będzie kompletny lub pojawi się konkretny konflikt ownership, który zapiszesz jako blocker.
