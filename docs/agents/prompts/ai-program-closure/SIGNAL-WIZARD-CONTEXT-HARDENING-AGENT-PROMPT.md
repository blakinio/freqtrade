# Signal Wizard Semantic Hardening Worker Prompt

Paste the complete text below into a separate agent chat for `FTAI-20260731-closure-signal-wizard-context-hardening`.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako bounded backend/persistence worker domykający semantykę Signal Wizard po merge backend PR #825 i authenticated-context repair PR #846.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md`;
- `docs/agents/tasks/FTAI-20260731-signal-wizard-context-repair.md`;
- `docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md`;
- `docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- frozen contracts z PR #781;
- merged backend z PR #825;
- merged authenticated context repair z PR #846.

## Verified base

- PR #846 merged normally as `367a51b610d2a34ee5841bc0b86622bd64fc6858`.
- Its exact head `647ea9fb79134e90af87f165ea1529482f2c1f5c` passed AI Platform CI `30612077198`, Freqtrade CI `30612077288` and security `30612077128`, with zero review threads.
- Competing PR #844 is closed and must not be revived.
- Agent 0 created `agent/closure-signal-wizard-semantic-hardening` from current `develop` after a live open-PR overlap check.

## Branch

Pracuj wyłącznie na istniejącym branchu `agent/closure-signal-wizard-semantic-hardening`. Przed pierwszą edycją sprawdź, czy nie istnieje już aktywny PR dla tego tasku/brancha; jeżeli istnieje, kontynuuj go zamiast tworzyć duplikat. Synchronizuj normalnie z aktualnym `develop`.

## Owned paths

Nie wychodź poza dokładne `owned_paths` zapisane w tasku. W szczególności nie zmieniaj frozen contracts, Feature Registry source definitions, Strategy Lab fixed catalog ani żadnego frontendowego Signal Wizard path.

## Cel

Dostarcz jeden focused backend/API repair domykający pozostałe luki semantyczne, durable persistence i public error behavior bez cofania authenticated context construction z PR #846.

## Wymagania implementacyjne

- Zachowaj frozen `SignalWizardPreviewCommand` i `SignalWizardSubmitCommand` bez redefinicji.
- Zachowaj server-bound stable correlation z PR #846; nie przyjmuj browser correlation jako authority.
- Waliduj wszystkie feature selections, również disabled; każda musi istnieć i mieć `approved_for_ai=true`.
- Zachowaj exact `feature_id`, `enabled`, timeframe, resolved parameters i registry definition identity.
- Warunki DSL mogą odwoływać się tylko do enabled features; co najmniej jedna feature musi być enabled.
- Zawsze wyprowadzaj nowy immutable research-draft strategy version z canonical trusted command digest.
- `base_strategy_version` zachowaj wyłącznie jako provenance; nigdy nie używaj go jako nowej wersji draftu.
- Usuń wymyślone `risk.max_leverage` i wszelką fałszywą runtime compatibility.
- Dodaj forward migration `0002_semantic_hardening.sql`; nie modyfikuj `0001_signal_wizard.sql`.
- Persistuj exact canonical trusted preview command JSON wraz z result JSON, request digest i derived version.
- Submit ma wiązać persisted preview z pełnym tenant/actor/actor_type/resource_type/resource_id/environment/execution_mode identity oraz exact derived version.
- Zachowaj deterministic durable experiment ID i tenant-scoped idempotency.
- Dodaj stabilne, rozłączne reason codes dla preview idempotency, submit idempotency, target, environment, execution mode, actor, version, leakage i corrupt record.
- Router ma zwracać bounded public messages i nigdy nie może echo raw exception, Pydantic input, cookie, tokenu, headera, credentiala ani private endpointu.
- Numeric minimum/maximum constraint z nonnumeric value ma fail closed.
- Dodaj service, persistence, tenant-isolation, restart-safe identity, compatibility, identity-enabled error-shape i secret-exclusion tests.

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
