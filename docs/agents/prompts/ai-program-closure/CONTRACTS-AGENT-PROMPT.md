# Shared Contracts Worker Prompt

Paste the complete text below into a separate agent chat only when the closure dispatch table marks `FTAI-20260730-closure-contracts` as ready.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako wyłączny agent współdzielonych kontraktów dla programu zamknięcia AI Platform.

Przeczytaj i bezwzględnie stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-contracts.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- task-relevant architecture and existing canonical contract tests.

## Cel

Zamknij wyłącznie kontraktowe elementy sklasyfikowane jako `REAL_GAP`. Nie implementuj logiki biznesowej downstream ani frontendu.

## Zakres możliwy po potwierdzeniu w child tasku

- canonical `FeatureRecord`, `SignalEvent`, `StrategyDefinition`, `Experiment`, `ValidationReport` lub ich istniejące odpowiedniki;
- wersjonowane JSON Schema;
- stabilne tenant/actor/resource/environment context;
- idempotency contracts;
- compatibility/versioning policy;
- canonical event/API schemas;
- contract exports and generated-client inputs tylko wtedy, gdy child task przydziela dokładne pliki;
- serialization, tenant-scope, secret-exclusion and backward-compatibility tests.

## Wymagania

- Najpierw udowodnij, które modele już istnieją i są canonical.
- Nie twórz drugiego modelu dla istniejącego pojęcia.
- Zmiana kontraktu musi być jawnie wersjonowana lub kompatybilna.
- Nie usuwaj pól ani nie zmieniaj semantyki bez migration/compatibility evidence.
- Każdy command/event wymagający kontekstu musi fail-closed bez tenant, actor, target i environment.
- Sekrety pozostają opaque references i nie serializują się do browser-readable payloads.
- Zapisz w task checkpoint dokładny contract freeze commit, który downstream agents mają przyjąć.

## Akceptacja

- wszystkie przydzielone `REAL_GAP` kontraktowe są zamknięte;
- JSON Schema i modele są zgodne;
- compatibility/idempotency/tenant/secret tests przechodzą;
- downstream ma jednoznaczny canonical import path;
- brak execution authority i browser-to-private-engine path;
- focused PR jest scalony normalnie po zielonych checkach;
- checkpoint wskazuje dokładnie jedną następną akcję: synchronizacja downstream albo powrót do koordynatora.

Działaj autonomicznie do pełnego zamknięcia tego bounded tasku.
