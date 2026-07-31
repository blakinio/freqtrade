# Signal Wizard Context Hardening Worker Prompt

Paste the complete text below into a separate agent chat only when the closure dispatch table authorizes `FTAI-20260731-closure-signal-wizard-context-hardening` and no active implementation PR already owns it.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako bounded backend/API worker naprawiający Signal Wizard po merge PR #825.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md`;
- `docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md`;
- `docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- frozen contracts z PR #781;
- merged backend z PR #825;
- identity-enabled control plane z `ai_platform/portal/identity/http.py` i `service.py`.

## Branch

Pracuj wyłącznie na `agent/closure-signal-wizard-context-hardening`, utworzonym z aktualnego `develop` po ponownym preflightcie. Jeżeli aktywny PR już używa tego brancha i tasku, kontynuuj go zamiast tworzyć duplikat.

## Owned paths

Nie wychodź poza dokładne `owned_paths` zapisane w tasku. W szczególności nie zmieniaj frozen contracts, Feature Registry source definitions, Strategy Lab fixed catalog ani żadnego frontendowego Signal Wizard path.

## Cel

Dostarcz jeden focused repair, który:

1. wiąże correlation context po stronie serwera do trusted `RequestContext` przed digestem, idempotency, persistence i response construction;
2. przechodzi prawdziwy identity-enabled HTTP flow przez `create_identity_enabled_app`, realną portal session i CSRF;
3. domyka wszystkie wykazane luki semantyczne scalonego backendu.

## Wymagania implementacyjne

- Zachowaj frozen `SignalWizardPreviewCommand` i `SignalWizardSubmitCommand` bez redefinicji.
- Zweryfikuj tenant, actor i actor type względem trusted `RequestContext`.
- Zastąp wyłącznie command correlation context przez `RequestContext.correlation_context()` przed canonical JSON, digestem i persistence.
- Nigdy nie traktuj correlation z body jako authorization lub trusted provenance.
- Identity-enabled test ma wysłać inne UUID-y w body niż wygenerowane przez identity boundary i potwierdzić zapis trusted wartości.
- Waliduj wszystkie feature selections, również disabled; każda musi istnieć i mieć `approved_for_ai=true`.
- Zachowaj exact `feature_id`, `enabled`, timeframe, resolved parameters i registry definition identity.
- Warunki DSL mogą odwoływać się tylko do enabled features; co najmniej jedna feature musi być enabled.
- Zawsze wyprowadzaj nowy immutable research-draft strategy version z canonical trusted request digest. `base_strategy_version` zachowaj wyłącznie jako provenance.
- Usuń wymyślone `risk.max_leverage` i wszelką fałszywą runtime compatibility.
- Dodaj forward migration i zapis exact canonical trusted preview command JSON.
- Submit ma wiązać persisted preview z pełnym tenant/actor/resource_type/resource_id/environment/execution_mode identity oraz exact derived version.
- Zachowaj deterministic durable experiment ID.
- Wprowadź stabilne, rozłączne reason codes dla idempotency, target, environment, execution mode, version, leakage i corrupt-record konfliktów.
- Router nie może zwracać raw exception, Pydantic input, cookies, tokens, headers, credentials ani private endpoints.
- Numeric minimum/maximum constraint z nonnumeric value ma fail closed.
- Dodaj service, persistence, tenant-isolation, restart-safe idempotency, compatibility, identity-enabled HTTP i secret-exclusion tests.

## Safety

- Research-only.
- Brak execution, backtest-result fabrication, approval, deployment, promotion, exchange/Vault, protected holdout, orders i live-capital authority.
- Brak mock-only BFF.
- Brak transient/random candidate IDs.
- Brak mapowania do `tv_supertrend_v1`, `tv_squeeze_momentum_v1` lub innej stałej niekompatybilnej strategii.
- Brak `eval`, `exec`, source generation i compiler authority.

## Governance

- Przed edycją sprawdź aktualny `develop`, wszystkie open PR-y, active tasks i overlap każdego owned path.
- Utrzymuj checkpoint tasku po każdym materialnym etapie.
- Uruchom narrow tests, potem wszystkie wymagane repository gates.
- Otwórz jeden focused PR do `develop`.
- Sprawdź exact implementation HEAD, wszystkie wymagane CI conclusions i zero unresolved review threads.
- Synchronizuj normalnie, bez force push, bypassu lub rewrite historii.
- Scal normalnie dopiero po zielonym exact-head CI.
- Po merge pozostaw dokładnie jeden `next_action`: Agent 0 ma zmienić Signal Wizard frontend i closure matrix na `READY` z exact merge/CI evidence.

Nie kończ na analizie, mocku ani raporcie. Działaj autonomicznie do kompletnego merge albo zapisz pierwszy rzeczywisty blocker zgodnie z governance.
