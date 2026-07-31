# Signal Wizard Semantic Hardening Worker Prompt

Paste the complete text below into a separate agent chat only after PR #844 has merged normally and the closure dispatch table changes `FTAI-20260731-closure-signal-wizard-context-hardening` to `READY`.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako bounded backend/persistence worker domykający semantykę Signal Wizard po merge PR #825 i correlation repair PR #844.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260731-closure-signal-wizard-context-hardening.md`;
- `docs/agents/tasks/FTAI-20260731-signal-wizard-correlation-repair.md`;
- `docs/agents/tasks/FTAI-20260730-closure-ui-signal-wizard.md`;
- `docs/agents/tasks/FTAI-20260730-closure-signal-wizard-backend.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- frozen contracts z PR #781;
- merged backend z PR #825;
- finalny correlation/router repair z PR #844.

## Start condition

Nie zaczynaj implementacji, dopóki PR #844 nie jest normalnie scalony z zielonym exact-head CI i zerem unresolved review threads. Po jego merge wykonaj nowy preflight `develop` i open PR path inventory.

## Branch

Pracuj wyłącznie na `agent/closure-signal-wizard-semantic-hardening`, utworzonym z aktualnego `develop` po merge PR #844. Jeżeli aktywny PR już używa tego brancha i tasku, kontynuuj go zamiast tworzyć duplikat.

## Owned paths

Nie wychodź poza dokładne `owned_paths` zapisane w tasku. W szczególności nie zmieniaj:

- frozen contracts;
- `ai_platform/portal/signal_wizard/router.py`;
- `tests/ai_platform/portal/signal_wizard/test_signal_wizard.py`;
- Feature Registry source definitions;
- Strategy Lab fixed catalog;
- żadnego frontendowego Signal Wizard path.

## Cel

Dostarcz jeden focused repair, który domyka pozostałe luki semantyczne i persistence bez ponownego implementowania correlation/router lane z PR #844.

## Wymagania implementacyjne

- Waliduj wszystkie feature selections, również disabled; każda musi istnieć i mieć `approved_for_ai=true`.
- Zachowaj exact `feature_id`, `enabled`, timeframe, resolved parameters i registry definition identity.
- Warunki DSL mogą odwoływać się tylko do enabled features; co najmniej jedna feature musi być enabled.
- Zawsze wyprowadzaj nowy immutable research-draft strategy version z canonical trusted request digest po bindingu z PR #844.
- `base_strategy_version` zachowaj wyłącznie jako provenance; nigdy nie używaj go jako nowej wersji draftu.
- Usuń wymyślone `risk.max_leverage` i wszelką fałszywą runtime compatibility.
- Dodaj forward migration `0002_semantic_hardening.sql`; nie modyfikuj `0001_signal_wizard.sql`.
- Persistuj exact canonical trusted preview command JSON wraz z result JSON, request digest i derived version.
- Submit ma wiązać persisted preview z pełnym tenant/actor/actor_type/resource_type/resource_id/environment/execution_mode identity oraz exact derived version.
- Zachowaj deterministic durable experiment ID i tenant-scoped idempotency.
- Dodaj stabilne service conflict reason codes dla idempotency, target, environment, execution mode, actor, version i blocking leakage; router mapping pozostaje własnością PR #844.
- Numeric minimum/maximum constraint z nonnumeric value ma fail closed.
- Dodaj nowy, rozłączny test file z service/persistence, tenant-isolation, disabled-feature preservation, non-approved disabled feature rejection, base-version provenance, exact target binding, restart-safe command identity, idempotency i secret-exclusion coverage.

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
