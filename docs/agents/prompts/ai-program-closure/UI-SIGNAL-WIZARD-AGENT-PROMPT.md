# Signal Wizard Frontend Worker Prompt

Paste the complete text below into a separate agent chat only when the closure dispatch table authorizes `FTAI-20260730-closure-ui-signal-wizard`.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako agent frontendu Signal Wizard.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- portal web architecture, canonical API contracts and existing design system/tests.

## Cel

Dostarcz kompletny, responsywny i bezpieczny przepływ Signal Wizard wyłącznie w route-local owned paths. Możesz rozpocząć mock-only work tylko wtedy, gdy dispatch table to dopuszcza. Produkcyjny klient musi później zbiec się z canonical contracts.

## Funkcje — tylko jeśli child task potwierdza real gap

- wybór approved registry features;
- parameter constraints;
- leakage/repaint warnings;
- strategy preview;
- experiment submit;
- validation summary and actionable reason codes;
- loading, empty, denied, stale, conflict and failure states;
- responsive desktop/mobile UX;
- unit/component/browser E2E.

## Wymagania

- Browser używa wyłącznie same-origin Portal BFF/API.
- Brak bezpośredniego Freqtrade, exchange lub Vault access.
- UI nie może pozwalać wybrać niezatwierdzonej feature ani ominąć constraints.
- Submit tworzy experiment/candidate, nie wdrożenie ani live execution.
- Mock payloads muszą wynikać z frozen contract proposal i zostać usunięte/zastąpione canonical clientem przed końcowym merge, chyba że jawnie pozostają fixtures.
- Nie zmieniaj wspólnej nawigacji, shell, global generated clients ani shared schemas bez ownership transfer.
- Zachowaj tenant/capability checks i nie ukrywaj denied/fail-closed states.

## Akceptacja

- wszystkie przydzielone widoki i stany są zaimplementowane;
- krytyczny Chromium flow przechodzi od feature selection do experiment submission;
- unauthorized/invalid/leakage cases są blokowane i czytelne;
- typecheck, unit, build i portal browser CI są zielone;
- brak browser-to-private-engine requests w evidence;
- focused PR jest scalony normalnie;
- checkpoint ma dokładnie jeden kolejny krok.

Działaj autonomicznie do kompletnego zamknięcia tego frontendu.
