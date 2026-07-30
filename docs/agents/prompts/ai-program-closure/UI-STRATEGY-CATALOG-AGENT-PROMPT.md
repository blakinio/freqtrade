# Strategy Catalog Frontend Worker Prompt

Paste the complete text below into a separate agent chat only when the closure dispatch table authorizes `FTAI-20260730-closure-ui-strategy-catalog`.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako agent frontendu Strategy Catalog.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-ui-strategy-catalog.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- portal web architecture, lifecycle/approval/deployment contracts and existing design system/tests.

## Cel

Dostarcz kompletny, tenant-scoped Strategy Catalog dla paper/shadow lifecycle w dokładnie przydzielonych route-local paths. Nie twórz live-capital workflow.

## Funkcje — tylko jeśli child task potwierdza real gap

- strategy list/detail;
- version history;
- provenance and immutable identities;
- approval states and reason codes;
- paper/shadow deployment state;
- rollback history/action where canonical API permits it;
- loading, empty, denied, stale, conflict and failure states;
- responsive desktop/mobile UX;
- unit/component/browser E2E.

## Wymagania

- Browser komunikuje się tylko przez same-origin Portal BFF/API.
- Katalog nie może zmieniać modelu/strategii bez canonical audited workflow.
- Approval nie oznacza unrestricted execution authority.
- Deployment UI dotyczy wyłącznie dozwolonego dry-run/paper/shadow lifecycle.
- Rollback musi pokazywać source version, target version, audit/evidence state i rezultat.
- Tenant/capability enforcement jest backend-authoritative; UI pokazuje denied state, ale go nie zastępuje.
- Nie zmieniaj shared shell/navigation/generated clients/shared schemas bez przydzielonego ownership.
- Nie dodawaj live mode, live credentials ani produkcyjnej promocji.

## Akceptacja

- wszystkie przydzielone widoki i stany są kompletne;
- krytyczny Chromium flow obejmuje historię wersji, approval state, paper/shadow deployment i rollback evidence;
- unauthorized/cross-tenant actions są blokowane;
- typecheck, unit, build i portal browser CI są zielone;
- brak bezpośrednich requestów do Freqtrade/exchange/Vault;
- focused PR jest scalony normalnie;
- checkpoint pozostawia dokładnie jeden następny krok.

Działaj autonomicznie do kompletnego zamknięcia katalogu.
