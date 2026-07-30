# Full-Platform Integration and E2E Worker Prompt

Paste the complete text below into a separate agent chat when the closure dispatch table authorizes `FTAI-20260730-closure-integration-e2e`. Early harness-only work is allowed only if the child task says so; final acceptance waits for its declared dependencies.

---

Pracujesz autonomicznie w repozytorium `blakinio/freqtrade` jako agent końcowej integracji, jakości i E2E programu AI Platform.

Przeczytaj i stosuj:

- `docs/agents/prompts/ai-program-closure/WORKER-COMMON-RULES.md`;
- `docs/agents/tasks/FTAI-20260730-closure-integration-e2e.md`;
- `docs/ai_platform/PROGRAM_CLOSURE_MATRIX.md`;
- current merged child PRs, universal E2E architecture and security requirements.

## Cel

Udowodnij pełny, bezpieczny przepływ produktu paper/shadow przez canonical portal, backend, deterministic risk, simulator/private dry-run boundaries, evidence and rollback. Nie implementuj funkcjonalności należącej do workerów, chyba że koordynator utworzy dokładny repair slice.

## Zakres

- early phase: fixtures, deterministic harness, page objects, evidence collectors and failure bundles w owned paths;
- final phase: cross-layer integration after wymagane child PRs są scalone;
- contract/API parity;
- critical Chromium user journeys;
- responsive, loading, empty, denied, stale, conflict and error states;
- tenant isolation, RBAC/capabilities, CSRF/session and secret-exclusion checks;
- deterministic exchange/simulator evidence;
- PNL/execution reconciliation and audit attribution;
- paper/shadow rollback;
- proof that browser never reaches Freqtrade, exchange or Vault directly;
- exact-head workflow matrix and zero unresolved review threads.

## Minimalny krytyczny journey

1. Użytkownik uwierzytelniony przez supported test boundary wybiera tenant.
2. Tworzy lub wybiera strategię/eksperyment zgodnie z canonical workflow.
3. System waliduje contracts, timestamp/leakage and deterministic risk.
4. Uruchamia dozwolony paper/shadow/dry-run lifecycle.
5. Deterministyczna symulacja lub istniejący prywatny dry-run path generuje evidence.
6. Portal pokazuje stan, PNL/reconciliation, audit and provenance.
7. Rollback/stop działa i jest audytowany.
8. Żaden krok nie daje live-capital authority.

## Wymagania

- Nie fałszuj gotowości sleepami ani mock success bez jawnego fixture label.
- Oddziel persisted intent, transport acknowledgement i authoritative execution proof.
- Simulated/local/CI evidence pozostaje jawnie oznaczone.
- Nie nazywaj tego realnym P11 bez prawdziwego protected ingress.
- Każdy failure bundle musi wskazywać pierwszą awarię i dowody między warstwami.
- Naprawy poza owned paths wymagają osobnego bounded repair tasku od koordynatora.

## Akceptacja

- wszystkie zadeklarowane krytyczne journeys przechodzą;
- backend, web, browser, security, deterministic simulation and relevant full CI są zielone na exact head;
- brak unresolved review threads;
- brak public/direct private-engine access;
- evidence jest kompletne i reprodukowalne;
- focused PR jest scalony normalnie;
- checkpoint kieruje dokładnie jedną akcją do finalnego koordynatora.

Działaj autonomicznie do pełnego zakończenia integracji lub udokumentowania pierwszego konkretnego dependency blocker.
