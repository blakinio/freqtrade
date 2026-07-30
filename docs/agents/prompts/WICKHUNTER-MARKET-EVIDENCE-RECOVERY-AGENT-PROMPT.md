# WickHunter Market Evidence Recovery Agent Prompt

Wklej pełną treść poniżej do osobnego czatu agenta.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako koordynator i operator kompleksowej naprawy WickHunter Market Evidence.

Twoim zadaniem jest doprowadzić do rzeczywistego usunięcia wszystkich czerwonych stanów widocznych na stronie Market Evidence, a nie tylko zmienić etykiety w UI.

## Obowiązkowy kontekst

Najpierw przeczytaj i stosuj:

- `AGENTS.md`;
- `docs/agents/CONTEXT_HANDOFF.md`;
- `docs/agents/tasks/FTAI-20260731-wickhunter-market-evidence-recovery-v1.md`;
- `docs/agents/tasks/FTAI-20260730-wickhunter-production-market-evidence-capture-and-portal-v1.md`;
- `docs/agents/programs/FTAI_WICKHUNTER_LIQUIDATION_BOT_PROGRAM.md`;
- `docs/agents/programs/FTAI_AI_TRADING_PORTAL_PROGRAM.md`;
- `docs/ai_platform/WICKHUNTER_PRODUCTION_MARKET_EVIDENCE.md`;
- `docs/ai_platform/portal/MARKET_EVIDENCE_READ_MODEL.md`.

Repozytorium, aktualny Git, PR-y, workflow, artefakty i stan wdrożenia są źródłem prawdy. Nie opieraj decyzji na historii czatu ani samym zrzucie ekranu.

## Punkt startowy

Task: `FTAI-20260731-wickhunter-market-evidence-recovery-v1`

Branch koordynacyjny: `agent/wickhunter-market-evidence-recovery-v1`

Aktualnie raportowane problemy:

- `BLOCKED`;
- `WH-01 BLOCKED`;
- `LIQUIDATION_ARCHIVE_NOT_BOUND`;
- `OKX Swap` jako `DEGRADED`;
- brak OKX liquidation feed, candle evidence, market quality i instrument history;
- OKX `excluded`;
- `OKX_CANDLE_EVIDENCE_NOT_CONFIGURED`.

Znane istotne elementy repozytorium:

- PR #723: guarded WH-01 materialization operator;
- PR-y #753 i #766: production Market Evidence collector, WH-01 adapter, Portal i naprawa walidacji;
- PR #761: terminalny kontrakt OKX Liquid20;
- PR #816: aktywny operational request dla production evidence capture — nie duplikuj go i nigdy nie merge'uj request-only PR do `develop`.

Wszystkie te informacje ponownie zweryfikuj na żywo.

## Cel końcowy

Doprowadź system do stanu, w którym:

1. istnieje kompletne, realne, source-separated i immutable market evidence dla wszystkich wymaganych źródeł, w tym OKX;
2. zaakceptowane immutable archiwum Liquid20 jest kryptograficznie związane z dokładnym market-evidence package i prospectively frozen WH-01 split geometry;
3. guarded operator tworzy niepusty, niezależnie zweryfikowany `wickhunter-dataset-manifest-v1`;
4. Portal pokazuje stan zielony wyłącznie dlatego, że powyższe dowody są prawdziwe;
5. wszystkie authority flags pozostają false, a `orders_submitted == 0`.

## Tryb pracy

Nie zatrzymuj się na analizie lub planie. Wykonuj zadanie autonomicznie aż do pełnego zakończenia albo konkretnego zewnętrznego blockera, którego nie da się usunąć w repozytorium.

Pracuj sekwencyjnie w kilku focused packages. Nie rób jednego ogromnego PR-a.

### 1. Gate 0 — audyt live state

Przed jakąkolwiek implementacją:

- pobierz aktualny `develop`, open PR-y, branche, task ownership, workflow conclusions i unresolved review threads;
- sprawdź dokładny stan PR #816, jego workflow i trwałego capture state;
- sprawdź aktualny Portal API/read model oraz immutable package, na który wskazuje;
- ustal pierwszą rzeczywistą przyczynę każdego czerwonego statusu;
- rozróżnij brak danych zewnętrznych od błędu kodu, konfiguracji, deploymentu, cache lub read modelu;
- sprawdź request/run IDs, SHA-256, source mappings, interval, pre-roll, freshness, gap accounting i authority flags;
- wyszukaj aktywnych właścicieli ścieżek i nie wchodź w konflikt.

Zapisz wyniki w checkpoint taska. Każda teza ma mieć konkretne repo/PR/workflow/artifact evidence.

### 2. Utwórz dokładne child taski

Task koordynacyjny początkowo posiada tylko swój task i prompt. Przed zmianą kodu utwórz child taski z dokładnymi, rozłącznymi `owned_paths`.

Rozdziel co najmniej:

- OKX candle/market-quality/instrument-history implementation;
- immutable binding i WH-01 materialization boundary;
- production operational request/execution;
- Portal/read-model repair tylko wtedy, gdy audyt potwierdzi realny defect;
- terminal checkpoint/closure.

Możesz wykonać wszystkie child taski sam, jeden po drugim, ale każdy musi mieć osobny branch, focused PR i checkpoint.

### 3. Napraw kompletność OKX

Jeżeli live audit potwierdzi brak OKX candle evidence, zbuduj pełny publiczny, credential-free i source-separated adapter OKX SWAP zgodny z canonical WH-01 cadence oraz semantyką Binance USD-M i Bybit Linear.

Wymagaj:

- tylko publicznych market/instrument endpoints;
- fail-closed rejection, jeśli obecne są credentials lub private/account/order capability;
- tylko zamkniętych świec;
- event/open/close/receive/availability timestamps;
- historycznych instrument snapshots oraz dokładnego symbol/venue/market mapping;
- kompletu wymaganych market-quality i WH-01 metrics;
- deterministycznego ordering, dedupe, restart recovery, gap accounting i atomic publication;
- testów missing, stale, conflicting, reconnect, tamper, symlink, traversal i zero-order boundary;
- statusu healthy/eligible dopiero po niezależnej weryfikacji realnego evidence.

Nie dopisuj świec do starych likwidacji, nie backdate'uj metadata i nie używaj synthetic fallback.

### 4. Napraw archive binding

Znajdź jedno kwalifikujące się accepted immutable Liquid20 archive/import, które jest czasowo i mapująco zgodne z finalnym market evidence.

Binding musi zawierać i weryfikować:

- accepted import/run identity;
- archive digest i accepted-selection digest;
- market-evidence package identity i digest;
- dokładny source/instrument mapping;
- decision cadence, history, purge, embargo i split geometry digest;
- temporal overlap i wymagany pre-roll;
- availability-time semantics;
- protected holdout exclusion;
- nowy immutable no-overwrite materialization request ID.

Nie modyfikuj, nie przepisuj, nie podmieniaj i nie zmieniaj nazw immutable inputs.

Jeżeli split geometry nie została zamrożona przed obserwacją danych, obecny run musi zostać odrzucony dla WH-01. Przygotuj nowy prospective run z nowym request/run ID; nie naprawiaj tego retroaktywnie.

### 5. Doprowadź capture do terminalnego stanu

Najpierw wykorzystaj istniejący capture i PR #816, jeśli są nadal ważne. Napraw tylko udowodniony problem runtime/deployment i zachowaj immutable identity oraz durable state.

Jeżeli potrzebny jest nowy run:

- użyj nowego request/run ID;
- przygotuj osobny canonical exact-scope request PR;
- request-only PR zamknij bez merge po terminalnym workflow;
- użyj zatwierdzonego Synology runnera i trwałego storage;
- runner zwolnij po bounded deployment i health confirmation;
- persistent collector ma sam prowadzić sampling i restart recovery;
- poczekaj na pełny real interval i pre-roll;
- opublikuj nowy immutable package atomowo i bez overwrite;
- niezależnie sprawdź hashes, counts, gaps, freshness, instruments, source coverage oraz `orders_submitted == 0`.

Nie używaj ponownie consumed request identity i nie uruchamiaj niedozwolonego retry.

### 6. Materializuj i zweryfikuj WH-01

Uruchom istniejący guarded operator dopiero po pełnym `ready` preflight.

Wymagaj:

- braku ignorowanych blockerów;
- niepustego `wickhunter-dataset-manifest-v1`;
- deterministycznych rows i partitions;
- poprawnych source identities i universe history;
- exact artifact hashes i niezależnej ponownej weryfikacji;
- braku future data;
- braku protected holdout `20260801-20260930`;
- braku synthetic fallback i current-state backdating;
- wszystkich model/replay/performance/execution/trading/live-capital flags nadal false.

Samo usunięcie komunikatu z Portalu bez realnego manifestu oznacza porażkę.

### 7. Portal naprawiaj tylko na podstawie dowodu

Jeżeli backend evidence jest poprawny, a czerwony status pozostaje przez błąd read modelu, cache, mappingu lub deploymentu, napraw dokładnie tę przyczynę.

Portal musi:

- pokazywać health każdego źródła oddzielnie;
- zachowywać typed blockers, dopóki istnieją;
- oznaczać OKX jako healthy/eligible tylko po verified evidence;
- usuwać `LIQUIDATION_ARCHIVE_NOT_BOUND` tylko po znalezieniu archive digest w bindingu i final manifest;
- usuwać globalny `BLOCKED` tylko po pełnym WH-01 readiness pass;
- pozostać read-only, tenant-safe i bez trading controls.

Po wdrożeniu porównaj Portal API z immutable package i WH-01 verifier output.

## Bezpieczeństwo i zakazy

Bezwzględnie:

- brak exchange secrets, API keys, private endpoints, proxy/VPN bypass i account APIs;
- brak orders, withdrawals, leverage/DCA, execution i live capital;
- brak replay, model training, performance research i strategy optimization w tym tasku;
- brak protected holdout reuse;
- brak synthetic evidence, backdating i guessed mappings;
- brak overwrite lub mutacji immutable evidence;
- brak force push, CI bypass i osłabiania fail-closed tests;
- request-only PR-y nigdy nie są merge'owane;
- implementation PR-y merge'uj normalnie dopiero po green exact-head CI i zero unresolved review threads.

Authority invariants na końcu:

```text
execution_enabled=false
trading_authorized=false
trading_credentials_present=false
orders_submitted=0
model_execution_authorized=false
replay_authorized=false
performance_research_authorized=false
live_capital_authorized=false
```

## Kryteria zakończenia

Nie oznaczaj taska `completed`, dopóki live production evidence nie potwierdzi:

- brak `BLOCKED` i `WH-01 BLOCKED`;
- brak `LIQUIDATION_ARCHIVE_NOT_BOUND`, ponieważ archive jest realnie związane, a nie ukryte;
- OKX ma verified liquidation, candle, market-quality i instrument-history evidence oraz jest `HEALTHY` i eligible, chyba że właściciel podejmie jawny product decision o usunięciu OKX z required WH-01 universe;
- Binance USD-M i Bybit Linear pozostały healthy;
- final evidence package i WH-01 dataset są niepuste, immutable, hash-verified, source-separated i czasowo poprawne;
- brak niewyjaśnionych gapów w accepted interval;
- exact-head CI jest zielone, unresolved threads = 0, a mergeable PR-y zostały scalone normalnie;
- checkpoint zawiera exact SHAs, PR-y, workflow runs, artifact IDs, hashes, counts, first failure, rejected hypotheses i dokładnie jeden `next_action`.

Jeżeli jedynym blockerem jest przyszłe zakończenie realnego okna obserwacji albo niedostępny zewnętrzny runner, ukończ wszystkie możliwe prerequisites, zapisz dokładny blocker i resumable next action. Nie udawaj zielonego stanu.

Działaj teraz autonomicznie.
