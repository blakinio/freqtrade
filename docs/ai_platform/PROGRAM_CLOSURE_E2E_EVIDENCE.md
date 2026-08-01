# AI Platform Program Closure — Integration and E2E Evidence

## Evidence status

This document defines the repository acceptance package for the final paper/shadow
integration worker.

Evidence classes are explicit:

- `REPOSITORY_FIXTURE` — canonical portal and backend fixtures executed in the repository;
- `DETERMINISTIC_SIMULATION` — byte-stable local exchange simulation with versioned inputs;
- `REPOSITORY_CI` — exact-commit Linux workflow evidence;
- `EXTERNAL_NOT_RUN` — real Cloudflare, Authentik, Vault, Synology and protected-ingress
  acceptance is not claimed here.

This package does not constitute real P11 acceptance and grants no live-capital authority.

## Canonical closure path

```text
opaque authenticated portal session and tenant scope
-> Signal Wizard canonical v2 preview
-> persisted research experiment intent
-> immutable strategy version and dry-run bot configuration
-> deterministic Risk Core approval
-> deterministic exchange simulation and immutable execution evidence
-> private runtime reconciliation with PNL and source attribution
-> portal read models, audit and provenance
-> evidence-backed paper rollback / runtime stop
```

The browser communicates only with the canonical portal and same-origin BFF. Freqtrade,
exchange private APIs and Vault remain server-side private boundaries.

## Intent and proof separation

| State | Meaning | Evidence | Not claimed |
|---|---|---|---|
| Persisted intent | The canonical research or lifecycle command was durably accepted. | Signal Wizard submission and idempotent lifecycle command identity. | Transport delivery, runtime execution or fill. |
| Transport acknowledgement | The private dry-run adapter provisioned and observed a test runtime. | ASE-03 admission audit, runtime identity and observed `RUNNING` state. | Order submission or authoritative execution proof. |
| Authoritative execution proof | A deterministic approved intent produced stable order, trade, PNL, fees, funding and reconciliation evidence. | Simulator evidence hash, source identities and `SYNCED` reconciliation. | Real exchange execution or live capital. |
| Rollback proof | The admitted paper runtime was stopped and the rollback audit linked to the source admission. | Append-only rollback record and observed `STOPPED` state. | Production rollback or external target acceptance. |

## Versioned scenario matrix

| ID | Layer | Scenario | Required result | Evidence class |
|---|---|---|---|---|
| `PC-BE-01` | Backend integration | Signal Wizard preview/submit, bot creation, Risk Core approval, deterministic simulation, private reconciliation, ASE-03 paper admission and rollback. | Stable identities and hashes, exact PNL/fee attribution, `SYNCED` evidence, no order submitted by ASE-03, audited stop. | `REPOSITORY_FIXTURE`, `DETERMINISTIC_SIMULATION` |
| `PC-BE-02` | Contract/security | Python/TypeScript v2 parity, false authority literals, sensitive metadata rejection, RBAC, tenant mismatch and production denial. | Fail closed with bounded reason codes. | `REPOSITORY_CI` |
| `PC-BE-03` | Architecture | Scan browser client sources for direct Freqtrade, exchange-private, Vault, token and private-key references. | No forbidden reference. | `REPOSITORY_CI` |
| `PC-WEB-01` | Chromium critical | Authenticated tenant, Signal Wizard candidate, Strategy Catalog paper/shadow evidence, lifecycle intent, PNL/reconciliation, audit, provenance and rollback. | Complete journey; persisted intent remains distinct from execution proof; no live authority. | `REPOSITORY_FIXTURE_BROWSER` |
| `PC-WEB-02` | Chromium states | Deterministic loading gate plus stale, empty, denied, conflict and error states. | Every state is explicit; no arbitrary sleep or invented success. | `REPOSITORY_FIXTURE_BROWSER` |
| `PC-WEB-03` | Chromium security | Opaque session, tenant isolation, CSRF denial and secret exclusion. | Cross-tenant and unsafe requests fail closed; no browser token exposure. | `REPOSITORY_FIXTURE_BROWSER` |
| `PC-WEB-04` | Responsive | Signal Wizard, Strategy Catalog and PNL at 390 px. | Critical content visible with no horizontal overflow. | `REPOSITORY_FIXTURE_BROWSER` |

## Deterministic backend evidence

`tests/ai_platform_integration/test_program_closure_e2e.py` writes:

```text
artifacts/program-closure/backend/program-closure-backend.json
```

The successful bundle includes:

- tenant and correlation identity;
- persisted experiment, preview and strategy identities;
- risk decision, reason codes and policy hash;
- deterministic order, trade and outcome identities;
- gross PNL, fees, funding cash flow, realized PNL and simulation evidence hash;
- private runtime reconciliation and source attribution;
- transport acknowledgement explicitly marked as non-authoritative;
- rollback audit linkage and stopped runtime state;
- cross-tenant zero-result proof.

On failure, the same path records the first failing stage and reason code together with all
evidence completed before that stage. If collection or import fails before the test can write
the bundle, the workflow creates a bounded `test_collection_or_import` failure record.

## Browser failure evidence

The dedicated workflow runs only the owned `program-closure.spec.ts` through a temporary
Playwright configuration. It does not change the shared Playwright configuration.

Artifacts contain:

- Playwright JSON results for desktop and responsive runs;
- trace on first retry, failure screenshot and retained failure video;
- redacted console and failed-request attachments from the shared fixture;
- `browser-first-failure.json`, identifying the first failed journey and bounded error.

No readiness sleep is used. The loading assertion is controlled by an explicit intercepted
same-origin request gate and is released deterministically.

## Dedicated Linux workflow

`.github/workflows/ai-program-closure-e2e.yml` executes on Ubuntu and contains three gates:

1. backend integration, canonical regression slices, Ruff and checkpoint validation;
2. critical Chromium and 390 px responsive journeys;
3. an exact-head matrix that fails unless both jobs pass.

All evidence artifacts are retained for seven days. Repository fixtures remain visibly
labelled and are never described as external staging acceptance.

## Reproduction

Backend:

```bash
PYTHONPATH="$PWD:$PWD/ai_strategy_engine/src" \
PROGRAM_CLOSURE_ARTIFACT_DIR="$PWD/artifacts/program-closure/backend" \
python -m pytest -q -o addopts='' \
  --confcutdir=tests/ai_platform_integration \
  tests/ai_platform_integration/test_program_closure_e2e.py
```

Browser:

```bash
cd ai_platform/portal/web
npm ci
npx playwright install chromium
npx playwright test \
  --config=program-closure.playwright.config.ts \
  --project=chromium-desktop
```

The temporary browser config is materialized by CI and selects
`e2e/program-closure.spec.ts` without changing shared E2E ownership.

## Exact-head workflow matrix

The implementation PR must record the final values here after normal CI completion.

| Gate | Exact head | Run | Result |
|---|---|---|---|
| AI Program Closure E2E | pending | pending | pending |
| Portal Web CI | pending | pending | pending |
| Portal Universal E2E | pending | pending | pending |
| AI Platform CI | pending | pending | pending |
| Freqtrade CI | pending | pending | pending |
| GitHub Actions Security Analysis | pending | pending | pending |

Completion also requires zero unresolved review threads and normal merge into `develop`.

## Explicit exclusions

- no live exchange credentials, private endpoints, withdrawals or order authority;
- no browser-to-Freqtrade, browser-to-exchange or browser-to-Vault path;
- no protected holdout reuse;
- no change to frozen thresholds `0.006/-0.009`;
- no change to authoritative `selected_model = null`;
- no claim of real Cloudflare, Authentik, Vault, Synology or protected-ingress acceptance;
- no production mutation, live-capital promotion or autonomous repair outside the owned paths.
