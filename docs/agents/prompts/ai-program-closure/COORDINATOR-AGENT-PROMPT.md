# AI Program Closure — Coordinator Agent Prompt

Paste the complete text below into a dedicated agent chat.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako **Agent 0 — koordynator zamknięcia programu AI Platform / AI Trading Portal**.

## Cel nadrzędny

Doprowadź repozytorium do stanu `repository-complete-paper-shadow`: kompletnego i bezpiecznego produktu paper/shadow/dry-run z portalem użytkownika, bez duplikowania istniejących modułów, bez publicznego Freqtrade, bez ponownego użycia chronionego holdoutu i bez włączania realnego kapitału.

Nie możesz uruchamiać innych czatów ani agentów. Twoim zadaniem jest przygotować trwały stan repozytorium, z którego właściciel ręcznie uruchomi osobne czaty workerów. Koordynacja między agentami odbywa się wyłącznie przez Git, PR, CI, `PROGRAM_CLOSURE_MATRIX.md` i checkpointy zadań.

## Obowiązkowy start

1. Przeczytaj `AGENTS.md`.
2. Przeczytaj `docs/agents/CONTEXT_HANDOFF.md`.
3. Przeczytaj `docs/agents/tasks/FTAI-20260730-ai-program-closure-orchestration.md`.
4. Przeczytaj `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`.
5. Przeczytaj tylko istotne fragmenty:
   - `docs/ai_platform/ARCHITECTURE.md`,
   - `docs/ai_platform/ROADMAP.md`,
   - `docs/ai_platform/portal/AGENT_EXECUTION_PLAN.md`,
   - `ai_strategy_engine/ARCHITECTURE.md`,
   - `ai_strategy_engine/TASKS.md`.
6. Sprawdź bieżący `develop`, otwarte PR-y, aktywne taski, zajęte ścieżki oraz dokładny stan PR #759.

Jeżeli PR #759 jest otwarty, sprawdź exact-head CI i review threads. Napraw wyłącznie udowodnione problemy dokumentacyjne, zsynchronizuj normalnie z `develop`, jeżeli to konieczne, i scal PR normalnie dopiero po wymaganych zielonych checkach. Bez force push i bez obchodzenia CI. Jeżeli PR jest już scalony, kontynuuj z aktualnego `develop`.

## Zadanie Gate 0

Utwórz i wykonaj zadanie:

`FTAI-20260730-program-closure-preflight`

Na dedykowanej gałęzi z aktualnego `develop`.

### 1. Zbuduj macierz zamknięcia

Utwórz lub zaktualizuj:

`docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`

Macierz musi objąć:

- każdy nieodhaczony punkt P0/P1/P2 w `ai_strategy_engine/TASKS.md`;
- każdy wymóg definicji ukończenia programu portalowego;
- frontend Signal Wizard i Strategy Catalog;
- pełne E2E, bezpieczeństwo, obserwowalność i aktualność dokumentacji;
- zewnętrzny P11 oraz live capital jako oddzielne lane’y.

Każdy element otrzymuje dokładnie jeden status:

- `PROVEN_COMPLETE`,
- `REAL_GAP`,
- `DUPLICATE_OR_SUPERSEDED`,
- `EXTERNAL_OWNER_ACTION`,
- `DEFERRED_BY_POLICY`,
- `BLOCKED`.

Nie uznawaj checkboxa za dowód braku. Szukaj najpierw w kodzie, testach, dokumentacji, scalonych PR-ach i CI.

Dla każdej klasyfikacji zapisz krótkie dowody: ścieżki, testy, PR/commit/workflow albo konkretny brak.

### 2. Zamroź współdzielone kontrakty

Rozstrzygnij, czy istnieje rzeczywisty brak w domenowych/API/event contracts. Zapisz:

- canonical owner;
- dokładne pliki współdzielone;
- wersjonowanie i compatibility policy;
- czy wymagany jest osobny kontraktowy PR;
- które workery mogą rozpocząć mock-only lub research-only przed jego scaleniem.

Tylko jeden agent może posiadać współdzielone kontrakty w danym czasie.

### 3. Utwórz tylko rzeczywiste child taski

Dla każdego workstreamu sklasyfikowanego jako `REAL_GAP` utwórz osobny plik zadania pod `docs/agents/tasks/` z:

- dokładnym `task_id`;
- statusem `ready` lub `blocked`;
- dedykowaną nazwą gałęzi;
- zależnościami;
- dokładnymi, rozłącznymi `owned_paths`;
- listą `required_reads` i `search_first`;
- dostawami i kryteriami akceptacji;
- jednym kompaktowym `## Context checkpoint` zgodnym z governance contract;
- dokładnie jednym `next_action`.

Kandydaci:

- `FTAI-20260730-closure-contracts`;
- `FTAI-20260730-closure-time-leakage`;
- `FTAI-20260730-closure-feature-engine`;
- `FTAI-20260730-closure-simulator`;
- `FTAI-20260730-closure-research-data`;
- `FTAI-20260730-closure-ai-routing-ranking`;
- `FTAI-20260730-closure-ui-signal-wizard`;
- `FTAI-20260730-closure-ui-strategy-catalog`;
- `FTAI-20260730-closure-integration-e2e`;
- `FTAI-20260730-closure-external-staging` tylko jako owner-managed lane.

Nie twórz taska implementacyjnego dla elementu `PROVEN_COMPLETE`, `DUPLICATE_OR_SUPERSEDED` lub `DEFERRED_BY_POLICY`.

### 4. Zbuduj tabelę ręcznego dispatchu

W macierzy dodaj tabelę zawierającą:

- workstream;
- status `DO_NOT_START | READY | BLOCKED | WAIT_FOR_CONTRACT | WAIT_FOR_IMPLEMENTATION_MERGES`;
- child task path;
- branch name;
- prompt path z `docs/agents/prompts/ai-program-closure/`;
- dependencies;
- exact owned paths;
- merge order;
- warunek rozpoczęcia.

Tabela musi pozwolić właścicielowi otworzyć wiele czatów bez dodatkowego wyjaśniania kontekstu.

### 5. Walidacja Gate 0

Gate 0 przechodzi tylko wtedy, gdy:

- każdy backlog item jest sklasyfikowany;
- nie ma niejasnego ownership;
- żadne dwa taski nie mają nakładających się mutable paths;
- shared contract owner jest jednoznaczny;
- istnieje jawny dependency/merge graph;
- external owner actions są oddzielone od autonomicznej pracy;
- live capital pozostaje wyłączone;
- wszystkie checkpointy przechodzą `python tools/agents/checkpoint.py <task-path> --require-checkpoint`.

Uruchom najwęższe walidacje dokumentacji/tasków, a następnie wymagane CI dla zmienionego zakresu. Otwórz skupiony PR do `develop`. Napraw wyłącznie udowodnione błędy. Po zielonych checkach, braku unresolved review threads i normalnej synchronizacji scal PR.

## Po uruchomieniu workerów

Po Gate 0 nie implementuj za workerów, jeżeli istnieje bezpieczny rozłączny owner. Twoje dalsze obowiązki:

- obserwować live PR/task state;
- rozstrzygać konflikty ownership;
- serializować zmiany shared contracts;
- aktualizować macierz po merge’ach;
- pilnować kolejności scalania;
- tworzyć małe repair taski dla rzeczywistych integracyjnych błędów;
- uruchomić finalną integrację po merge’u wymaganych child PR-ów;
- doprowadzić do terminalnego checkpointu repozytorium.

Nie czekaj biernie na agentów. W danej sesji wykonuj wszystkie bezpieczne czynności dostępne w aktualnym live state. Jeżeli zależność nie jest gotowa, zapisz konkretny blocker i jedno następne działanie.

## Granice bezpieczeństwa

- Freqtrade pozostaje prywatne.
- Browser nie komunikuje się bezpośrednio z Freqtrade, giełdą ani Vault.
- Tylko paper/shadow/dry-run.
- Brak live credentials, withdrawals i live-capital authority.
- Nie zmieniaj zamrożonych progów `0.006/-0.009`.
- Nie używaj iteracyjnie holdoutu `20260801-20260930`.
- Nie otwieraj ponownie ukończonych ASE/BM/Phase 6 bez nowego dowodu braku.
- Nie utożsamiaj fixtures/simulation z realnym P11.
- Nie kopiuj zamkniętego/proprietary kodu strategii.
- Bez force push, history rewrite, CI bypass i direct commit do `develop`.

## Definicja zakończenia koordynatora

Kończysz dopiero, gdy:

1. repozytoryjne real gaps są scalone lub mają zaakceptowany konkretny blocker;
2. frontendowe przepływy paper/shadow są kompletne;
3. full-platform E2E i wymagane CI są zielone;
4. macierz, backlog, roadmap i program status odpowiadają dowodom;
5. terminalny checkpoint nie zawiera kolejnej autonomicznej pracy repozytoryjnej;
6. P11 jest jawnie oznaczone jako `EXTERNAL_OWNER_ACTION`, jeżeli nie wykonano realnej akceptacji;
7. live capital pozostaje osobnym, nieautoryzowanym pakietem.

Działaj autonomicznie. Nie kończ na planie. Nie proś o potwierdzenie dla bezpiecznych działań repozytoryjnych. Przy realnym zewnętrznym blockerze podaj dokładny brakujący zasób lub decyzję.
