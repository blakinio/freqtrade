# Signal Wizard Backend Worker Prompt

Paste the complete text below into a separate agent chat only when the closure dispatch table authorizes `FTAI-20260730-closure-signal-wizard-backend` and no active implementation PR already owns it.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako agent canonical backend/API dla Signal Wizard.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md`;
- `docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- frozen contracts z PR #781 oraz istniejące Feature Registry, Strategy Lab i control-plane patterns.

## Branch

Pracuj wyłącznie na `agent/closure-signal-wizard-backend`, utworzonym z aktualnego `develop` po ponownym preflightcie. Jeżeli PR #825 jest nadal aktywny, kontynuuj ten sam branch i task — nie twórz duplikatu.

## Cel

Dostarcz brakujący canonical, tenant-scoped Signal Wizard preview service, durable submit service i zarejestrowane same-origin Portal/control-plane endpoints. Zaimplementuj kompletny bounded backend task, testy, checkpoint, focused PR i normalny merge po zielonym exact-head CI.

## Wymagany zakres

- `POST /v1/signal-wizard/preview` dla `SignalWizardPreviewCommand` -> `SignalWizardPreviewResult`;
- `POST /v1/signal-wizard/submit` dla `SignalWizardSubmitCommand` -> `SignalWizardSubmitResult`;
- canonical Feature Registry validation wyłącznie dla istniejących `approved_for_ai` entries, bez lokalnego allowlistu;
- zachowanie dokładnych feature IDs, enablement, timeframe, parameters, constraints, target, environment, actor, tenant i provenance;
- canonical typed DSL parse/normalization/validation bez `eval`, `exec`, source generation ani compiler authority;
- deterministyczny v2 research-draft envelope, immutable version i `preview_hash`;
- trwały preview store oraz trwały research experiment-intent submit store;
- tenant isolation, restart-safe lookup i deterministyczna idempotency;
- stabilne reason codes i fail-closed router errors;
- rejestracja modeli w `create_schema` oraz routera/service injection w canonical `control_plane.api.create_app`;
- service, API, persistence, compatibility, tenant-isolation, idempotency i secret-exclusion tests w dokładnych `owned_paths` tasku.

## Semantyka bezpieczeństwa

- Nie twórz backtest result, deployment, approval, promotion ani execution request.
- Nie nadawaj execution, order, deployment, promotion ani live-capital authority.
- Nie mapuj wyborów na `tv_supertrend_v1` lub `tv_squeeze_momentum_v1`.
- Nie generuj transient/random candidate IDs; durable experiment ID ma być deterministyczny i zapisany.
- Nie wymyślaj brakujących universe/risk/execution pól ani nie opisuj research draft jako kompatybilnej strategii runtime.
- Nie zmieniaj frozen contracts, Feature Registry source files, Strategy Lab fixed catalog definitions ani żadnego frontendowego Signal Wizard path.
- Brak browser-to-Freqtrade, exchange lub Vault path.
- Brak credentials, tokens, secret values, private endpoints, protected-holdout use i zmian progów.

## Governance

- Przed edycją sprawdź aktualny `develop`, wszystkie open PR-y, active tasks i overlap każdego owned path.
- Zostań wyłącznie w `owned_paths` z child tasku.
- Aktualizuj checkpoint po każdym materialnym etapie.
- Uruchom narrow tests, następnie wszystkie wymagane repository gates dla dotkniętych ścieżek.
- Utrzymuj jeden focused PR do `develop` — obecnie PR #825, jeżeli pozostaje aktywny.
- Sprawdź exact implementation HEAD, wszystkie wymagane CI conclusions i zero unresolved review threads.
- Synchronizuj tylko normalnie, bez force push lub bypassu.
- Scal normalnie dopiero po zielonym exact-head CI.
- Po merge pozostaw dokładnie jeden `next_action`: Agent 0 ma oznaczyć frontend `FTAI-20260730-closure-ui-signal-wizard` jako `READY` i uruchomić go z aktualnego `develop`.

Nie kończ na analizie lub mocku. Działaj autonomicznie do kompletnego backendowego zamknięcia tasku albo zapisz pierwszy rzeczywisty blocker zgodnie z governance.
