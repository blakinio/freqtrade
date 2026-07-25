# Portal Liquidations Integration — Agent Prompt

Pracujesz autonomicznie nad wdrożeniem danych o likwidacjach Bybit i Binance do AI Trading Portal.

Repozytoria:

- `blakinio/freqtrade`
- `blakinio/Oteryn-Platform`

Twoim celem jest dostarczenie bezpiecznego, tylko-do-odczytu modułu **„Likwidacje”** w portalu, wdrożonego na istniejącym środowisku Synology.

Nie polegaj bezkrytycznie na tym promptcie ani historii rozmowy.

Aktualne repozytoria, Git, otwarte i zamknięte PR-y, GitHub Actions, task records, `AGENTS.md`, dokumentacja portalu, kod kolektora oraz rzeczywisty stan Synology są source of truth.

Pracuj autonomicznie do zakończenia zadania albo do wystąpienia trwałego blokera wymagającego działania użytkownika.

---

## 1. Obowiązkowy live-state preflight

Najpierw wykonaj świeży, oszczędny preflight.

Sprawdź co najmniej:

- HEAD i domyślne branche obu repozytoriów;
- otwarte PR-y związane z:
  - Liquid20;
  - portalem;
  - Synology;
  - portalowym preview;
- aktualne workflowy GitHub Actions;
- rzeczywiste etykiety self-hosted runnerów;
- aktualny port portalu na Synology;
- aktualny stan issue `blakinio/Oteryn-Platform#148`;
- stan kontenera `liquid20-collector`;
- lokalizację danych Liquid20 na Synology;
- aktualną strukturę AI Trading Portal;
- aktualne kontrakty API, BFF, Data Plane i wdrożenia portalu;
- `AGENTS.md` w każdym używanym repozytorium;
- task records i obowiązujące checkpointy.

Nie zakładaj, że numery PR, SHA, porty lub branche podane niżej są nadal aktualne.

Znany wcześniejszy stan, który należy zweryfikować:

- pierwszy pełny przebieg Liquid20 zebrał 24 godziny danych;
- zebrał dane ze wszystkich 20 symboli na obu giełdach;
- wynik acceptance był `failed` wyłącznie przez `binance-usdm.maximum_latency_over_threshold_ratio`;
- polityka acceptance jest zamrożona i nie wolno jej łagodzić;
- pełne dane powinny znajdować się pod ścieżką zbliżoną do `/volume1/docker/freqtrade-liquidations/data/runs/`;
- portalowe preview mogło działać na prywatnym adresie LAN i porcie `3031`;
- powyższe fakty są tylko wskazówką i muszą zostać potwierdzone.

---

## 2. Cel produktowy

Dodaj do portalu nową powierzchnię:

`Likwidacje`

Moduł ma prezentować dane Liquid20 jako dane rynkowe tylko do odczytu.

Minimalny zakres interfejsu:

1. Strumień ostatnich likwidacji.
2. Filtry:
   - źródło: Bybit / Binance / wszystkie;
   - symbol;
   - strona likwidowanej pozycji: long / short;
   - zakres czasu.
3. Kolumny:
   - czas zdarzenia;
   - giełda;
   - symbol;
   - likwidowana strona pozycji;
   - cena;
   - ilość;
   - wartość w USDT;
   - opóźnienie ingestu.
4. Podsumowania:
   - ostatnie 5 minut;
   - ostatnia godzina;
   - ostatnie 24 godziny.
5. Ranking symboli:
   - liczba likwidacji;
   - suma notional;
   - podział long/short.
6. Stan danych:
   - tryb danych;
   - świeżość;
   - ostatnie zdarzenie;
   - aktywne źródła;
   - liczba obserwowanych symboli;
   - dostępność;
   - rozłączenia;
   - status acceptance, jeśli istnieje.
7. Jawne objaśnienie semantyki źródeł:
   - Bybit i Binance nie mają identycznej semantyki;
   - Binance `forceOrder` publikuje najnowsze zdarzenie w oknie około 1000 ms;
   - danych między giełdami nie wolno deduplikować ani sumować bez zachowania etykiety źródła.

Portal musi uczciwie oznaczać tryb:

- `historical` — dane z zakończonego przebiegu;
- `live` — dane z aktualnie zapisywanego przebiegu;
- `stale` — źródło nie aktualizuje się w zadanym czasie;
- `acceptance-failed` — dane istnieją, ale przebieg nie przeszedł zamrożonej polityki jakości;
- `accepted` — dopiero gdy istnieje raport z `passed: true`.

Nie przedstawiaj niezaakceptowanego przebiegu jako produkcyjnego źródła live.

---

## 3. Nienaruszalne granice

Nie wolno:

- zmieniać listy 20 symboli Liquid20;
- zmieniać 24-godzinnego czasu acceptance;
- zmieniać progów lub frozen acceptance policy;
- usuwać ani omijać bramki latency;
- zmieniać schematu istniejących dowodów bez osobnego wersjonowanego kontraktu;
- mutować istniejących katalogów dowodowych;
- usuwać lub nadpisywać danych z przebiegu 24-godzinnego;
- wystawiać Freqtrade REST lub WebSocket bezpośrednio do przeglądarki;
- wystawiać kontenera Liquid20 bezpośrednio do Internetu;
- montować Docker socket do kontenera aplikacyjnego lub adaptera danych;
- dodawać kluczy Binance, Bybit lub innych credentials;
- łączyć modułu likwidacji z logiką składania zleceń;
- generować sygnałów kupna lub sprzedaży;
- uruchamiać DCA, leverage, dry-run lub live trading;
- traktować likwidacji jako autoryzacji handlowej;
- publikować surowych sekretów, tokenów lub prywatnych logów w UI;
- modyfikować zakończonych kontraktów Phase 5, Phase 6, RL lub holdoutu.

Moduł ma być wyłącznie read-only market-data / research preview.

---

## 4. Architektura docelowa

Zachowaj obowiązującą architekturę portalu:

```text
Bybit / Binance
        ↓
Liquid20 collector
        ↓
niezmienne NDJSON + summary + manifest + acceptance report
        ↓
prywatny read-model / adapter danych
        ↓
portal control-plane / BFF
        ↓
przeglądarka
```

Przeglądarka nie może czytać plików Synology bezpośrednio.

Przeglądarka nie może łączyć się bezpośrednio z kolektorem.

Preferuj najmniejszą bezpieczną implementację zgodną z aktualnym kodem.

Dopuszczalne warianty:

A. Moduł read-model w istniejącym control plane portalu.

B. Oddzielny prywatny adapter tylko do odczytu uruchomiony na Synology.

C. Server-side reader w Next.js, jeżeli aktualna architektura i deployment zapewniają właściwą izolację.

Nie twórz nowego mikroserwisu bez potrzeby.

Adapter powinien otrzymać wolumen Liquid20 wyłącznie jako read-only:

```text
/volume1/docker/freqtrade-liquidations/data:/liquid20-data:ro
```

Adapter nie może otrzymać:

- `/var/run/docker.sock`;
- kluczy giełdowych;
- katalogów strategii;
- konfiguracji live trading;
- dostępu zapisu do katalogów Liquid20.

Jeśli potrzebny jest cache lub indeks, zapisuj go w osobnym katalogu stanu adaptera, nigdy w katalogu dowodowym Liquid20.

---

## 5. Kontrakt danych

Zachowaj istniejący kanoniczny model zdarzenia:

- `schema_version`;
- `source`;
- `source_event_id`;
- `symbol`;
- `liquidated_position_side`;
- `occurred_at_ms`;
- `received_at_ms`;
- `price`;
- `quantity`;
- `notional_usd`;
- `raw_side`.

Dodaj wersjonowany portalowy read-model, który nie zmienia oryginalnego zdarzenia.

Przykładowy kontrakt zdarzenia portalowego:

```json
{
  "schema_version": 1,
  "source": "binance-usdm",
  "source_event_id": "string",
  "symbol": "BTCUSDT",
  "liquidated_position_side": "long",
  "occurred_at_ms": 0,
  "received_at_ms": 0,
  "ingest_latency_ms": 0,
  "price": "0.0",
  "quantity": "0.0",
  "notional_usd": "0.0"
}
```

Kwoty i wartości dziesiętne przekazuj jako stringi albo bezpieczny typ decimal. Nie wprowadzaj utraty precyzji przez float.

Minimalne endpointy BFF:

```text
GET /api/market/liquidations
GET /api/market/liquidations/summary
GET /api/market/liquidations/health
```

Minimalne parametry listy:

```text
source
symbol
side
since
until
limit
cursor
```

Wymagania:

- maksymalny limit wyniku;
- deterministyczne sortowanie;
- stabilna paginacja lub cursor;
- walidacja parametrów;
- brak możliwości path traversal;
- brak dowolnego wyboru pliku przez użytkownika;
- brak zwracania całych logów lub manifestów;
- brak pełnego skanowania wielkich plików przy każdym żądaniu.

---

## 6. Wydajność i obsługa plików

Nie ładuj całego NDJSON do pamięci przy każdym żądaniu.

Zaimplementuj bezpieczny bounded read-model.

Preferowane podejście:

- wykrywanie najnowszego poprawnego runu;
- odczyt zakończonego lub aktywnego NDJSON;
- zapamiętywanie offsetu;
- bounded in-memory cache ostatnich zdarzeń;
- osobny indeks lub SQLite w katalogu stanu adaptera, jeśli jest rzeczywiście potrzebny;
- odporność na częściową ostatnią linię aktywnie zapisywanego pliku;
- odporność na restart;
- wykrywanie rotacji lub zmiany `run_id`;
- limit pamięci;
- limit liczby rekordów;
- brak modyfikowania plików źródłowych.

Dla pierwszego wdrożenia dopuszczalny jest polling server-side co kilka sekund.

Nie wymagaj WebSocket ani SSE w pierwszym PR, chyba że portal ma już gotowy i bezpieczny mechanizm eventowy.

---

## 7. Health i jakość danych

Endpoint health ma zwracać wyłącznie bezpieczne agregaty:

```json
{
  "mode": "historical",
  "run_id": "string",
  "acceptance_status": "failed",
  "failed_gates": [
    "binance-usdm.maximum_latency_over_threshold_ratio"
  ],
  "sources": {
    "bybit-linear": {
      "events": 0,
      "observed_symbols": 0,
      "availability_ratio": 0,
      "disconnects_per_hour": 0,
      "last_event_at_ms": 0
    },
    "binance-usdm": {
      "events": 0,
      "observed_symbols": 0,
      "availability_ratio": 0,
      "disconnects_per_hour": 0,
      "last_event_at_ms": 0
    }
  },
  "stale": false
}
```

Nie pobieraj stanu przez Docker socket.

Health powinien wynikać z:

- summary JSON;
- manifestu;
- acceptance report;
- czasu modyfikacji lub ostatniego zdarzenia;
- bezpiecznego status file, jeśli istniejący runner już taki publikuje.

Portal ma jasno pokazać:

- `Acceptance failed`;
- nazwę niespełnionej bramki;
- że dane pozostają dostępne jako research preview;
- że wynik nie autoryzuje handlu.

---

## 8. UI / UX

Dodaj moduł zgodny z aktualnym design systemem portalu.

Preferowana nawigacja:

```text
Market Data
└── Likwidacje
```

albo najbliższa zgodna z aktualną information architecture.

Widok powinien zawierać:

- nagłówek „Likwidacje”;
- status źródła;
- status acceptance;
- karty 5m / 1h / 24h;
- tabelę zdarzeń;
- filtry;
- ranking symboli;
- podział long/short;
- znacznik czasu ostatniej aktualizacji;
- loading state;
- empty state;
- stale state;
- error state;
- responsywny układ.

Nie używaj sugestii tradingowych typu:

- „kup”;
- „sprzedaj”;
- „sygnał long”;
- „sygnał short”;
- „przewaga rynkowa”.

Dopuszczalne określenia:

- „likwidowane pozycje long”;
- „likwidowane pozycje short”;
- „obserwacja rynku”;
- „dane badawcze”;
- „research preview”.

---

## 9. Testy

Dodaj testy co najmniej dla:

- parsowania poprawnych NDJSON;
- częściowej ostatniej linii;
- uszkodzonego rekordu;
- filtrowania po source;
- filtrowania po symbol;
- filtrowania po side;
- zakresu czasu;
- limitu;
- sortowania;
- agregacji 5m / 1h / 24h;
- sumowania notional z zachowaniem źródła;
- niewykonywania cross-source deduplication;
- statusu historical/live/stale;
- statusu acceptance failed/passed;
- braku path traversal;
- braku dostępu zapisu do źródłowego katalogu;
- braku credentials w kontrakcie;
- UI loading/empty/error;
- renderowania znanej próbki likwidacji;
- jawnego ostrzeżenia o semantyce Binance.

Dodaj E2E dla portalu:

1. otwarcie zakładki Likwidacje;
2. załadowanie fixture/read-model;
3. filtrowanie symbolu;
4. filtrowanie źródła;
5. sprawdzenie statusu acceptance;
6. sprawdzenie, że nie występuje żaden przycisk handlowy;
7. sprawdzenie, że dane nie pochodzą bezpośrednio z publicznego Freqtrade API.

Fixture musi być jawnie oznaczony i nie może zostać przedstawiony jako live.

---

## 10. Deployment na Synology

Wykorzystaj istniejący, aktualnie działający tor wdrożenia portalu.

Nie twórz drugiego konkurencyjnego mechanizmu deploy, jeśli repozytorium ma już:

- self-hosted runner;
- exact-SHA image build;
- candidate container;
- health check;
- rollback;
- prywatny LAN bind;
- portal preview workflow.

Rozszerz istniejący deployment minimalnie.

Wdrożenie powinno:

- zbudować immutable image;
- zamontować dane Liquid20 read-only;
- zamontować osobny katalog stanu read-modelu read-write, jeśli jest wymagany;
- nie montować Docker socketa do aplikacji;
- nie wystawiać nowego publicznego portu bez potrzeby;
- zachować prywatny LAN;
- zachować aktualny port portalu, jeżeli nadal jest prawidłowy;
- wykonać candidate health check;
- wykonać rollback przy błędzie;
- sprawdzić portalową stronę Likwidacje;
- sprawdzić endpoint health;
- potwierdzić brak credentials;
- potwierdzić, że katalog Liquid20 jest zamontowany `ro`.

Nie restartuj ani nie usuwaj kolektora Liquid20 bez potrzeby.

Nie uruchamiaj ponownie acceptance tylko w celu budowy UI.

---

## 11. Strategia PR-ów

Nie wdrażaj wszystkiego w jednym ogromnym PR.

Preferowany podział:

### PR 1 — kontrakt i read-model

- wersjonowany kontrakt;
- parser;
- bounded reader/index;
- summary;
- health;
- testy.

### PR 2 — portal API i UI

- endpointy BFF;
- zakładka Likwidacje;
- filtry;
- podsumowania;
- status quality/acceptance;
- UI tests i E2E.

### PR 3 — Synology deployment

- read-only mount;
- exact-SHA image;
- health checks;
- rollback;
- wdrożenie LAN preview;
- rzeczywista walidacja.

Każdy PR ma być:

- mały;
- logiczny;
- możliwy do niezależnego cofnięcia;
- oparty na aktualnym branchu docelowym;
- zielony przed scaleniem;
- udokumentowany task checkpointem.

Nie scalaj PR z czerwonymi wymaganymi kontrolami.

Nie omijaj review ani branch protection.

---

## 12. Dokumentacja i checkpoint

Utwórz osobny task record dla integracji likwidacji z portalem.

Task powinien zawierać:

- goal;
- owned_paths;
- dependencies;
- context routes;
- proven;
- derived;
- unknown;
- blockers;
- conflicts;
- first_failure;
- rejected_hypotheses;
- changed_paths;
- validation;
- dokładnie jeden `next_action`.

Aktualizuj checkpoint po każdym istotnym etapie.

Zaktualizuj dokumentację portalu:

- architecture;
- UI delivery status;
- data ownership;
- deployment;
- security boundary;
- research-preview classification.

---

## 13. Kryteria zakończenia

Zadanie jest ukończone dopiero, gdy:

- portal ma działającą zakładkę Likwidacje;
- dane pochodzą z rzeczywistych plików Liquid20 na Synology;
- moduł działa przez portalowy BFF/read-model;
- przeglądarka nie łączy się bezpośrednio z kolektorem ani Freqtrade;
- wolumen Liquid20 jest read-only;
- nie ma exchange credentials;
- nie ma Docker socketa w aplikacji;
- filtry i podsumowania działają;
- status acceptance jest pokazany uczciwie;
- failed gate Binance jest widoczny, dopóki nowy przebieg nie przejdzie;
- UI poprawnie rozróżnia historical/live/stale;
- testy jednostkowe, integracyjne i E2E są zielone;
- deployment Synology jest zielony;
- candidate health check jest zielony;
- rollback jest zachowany;
- portal jest osiągalny na aktualnym prywatnym adresie LAN;
- task checkpoint jest zakończony i zarchiwizowany;
- nie zmieniono frozen acceptance policy;
- nie uruchomiono ani nie autoryzowano handlu.

---

## 14. Raportowanie

Nie wysyłaj częstych opisów rutynowych działań.

Informuj użytkownika tylko przy:

- scaleniu kolejnego PR;
- działającym wdrożeniu na Synology;
- istotnym błędzie;
- trwałym blokerze;
- pełnym zakończeniu.

Końcowy raport ma zawierać:

- numery PR;
- merge SHA;
- użyte workflow runs;
- aktualny URL portalu LAN;
- endpointy;
- potwierdzenie read-only mount;
- potwierdzenie braku credentials i Docker socketa;
- potwierdzenie rzeczywistych danych Liquid20;
- status acceptance;
- wyniki testów;
- ewentualne ograniczenia;
- dokładnie jeden kolejny krok, tylko jeżeli zadanie nie może zostać zakończone.

Rozpocznij od live-state preflight i kontynuuj autonomicznie.
