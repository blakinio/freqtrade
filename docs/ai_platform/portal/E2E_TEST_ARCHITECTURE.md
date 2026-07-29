# AI Trading Portal — E2E Test Architecture

## Purpose

This document defines the implemented Playwright architecture for the browser-facing AI Trading Portal. It turns the quality contract in `QUALITY_AND_AUTONOMOUS_E2E.md` into a concrete repository layout and CI execution model.

The suite validates the supported portal and same-origin BFF path. It does not expose Freqtrade to the browser, connect to real capital, invent production identity bypasses or reinterpret fixture evidence as production acceptance.

## Repository layout

```text
ai_platform/portal/web/e2e/
├── config/       shared environment and tag vocabulary
├── data/         deterministic factories and canonical request fixtures
├── fixtures/     composed Playwright dependencies and failure evidence
├── journeys/     multi-page and browser/BFF workflows
├── pages/        reusable page and component interactions
├── specs/        one source scenario per business domain
└── support/      layout, accessibility and evidence helpers
```

Business domains under `specs/` currently cover:

```text
accessibility
ai
bots
market
operations
platform
responsive
security
smoke
stability
terminal
```

Tests are not copied into smoke, critical and regression directories. One test may carry several tags and remains owned by one business domain.

## Dependency flow

```text
SPEC
  -> JOURNEY
  -> PAGE / COMPONENT
  -> BROWSER / SAME-ORIGIN BFF
```

Supporting dependencies are composed through fixtures:

```text
FIXTURE
  ├── deterministic identity state
  ├── page objects
  ├── business journeys
  ├── unique data factory
  └── redacted failure evidence
```

Specs retain the business assertion. Selectors and repeated mechanics stay in page or journey classes. Canonical mutation payloads and unique test identities stay in data factories.

## Tag vocabulary

```text
@smoke
@critical
@regression
@security
@permissions
@cross-browser
@responsive
@a11y
@resilience
@stability
@soak
```

Tags are defined centrally in `e2e/config/e2e.config.ts`. A new local spelling is not allowed.

## Playwright projects

```text
chromium-desktop
chromium-accessibility
chromium-resilience
firefox-desktop
webkit-desktop
mobile-chrome
mobile-safari
chromium-stability
chromium-soak
```

The default Chromium project excludes accessibility, resilience, stability and soak classes. Each of those classes has an isolated project so failures are attributable and expensive repetition cannot leak into the normal regression gate.

CI uses one worker because fixture-backed mutable portal state must remain deterministic. Tests still create unique bot identifiers and may not depend on execution order.

## Safety invariants

Every browser test preserves these boundaries:

- bot creation is `dry_run` only;
- a risk-approved manual intent still fails closed when execution is unavailable;
- browser-supplied risk snapshots have no authority;
- Freqtrade REST/WebSocket endpoints remain private;
- sessions are opaque and no access, refresh or ID token is exposed to JavaScript;
- unsafe requests require valid same-origin CSRF evidence;
- MFA, step-up and tenant checks remain backend authoritative;
- Liquid20 is read-only research preview and cannot place an order;
- resilience scenarios use deterministic route substitution, not production dependency mutation;
- no exchange key, secret, wallet credential or private endpoint is committed or attached.

## Test data and cleanup

Fixture-mode requests are deterministic. Mutable objects use a factory that incorporates test title, project and worker identity. This removes fixed bot identifiers from create scenarios and prevents collisions.

The current fixture BFF does not persist created bots beyond the deterministic test server lifecycle. When a persistent test control plane is activated, API-created resources must register cleanup callbacks in the fixture before parallel workers are enabled.

## Failure evidence

Playwright produces:

- trace on first retry;
- screenshot only on failure;
- retained failure video;
- HTML report;
- JSON result file;
- redacted browser warning/error summary;
- redacted failed-request summary.

Artifacts are uploaded only for failed CI jobs and retained for seven days. Evidence helpers redact common authorization, cookie, password, secret, token and API-key representations before attachment.

## CI gates

### Pull request web gate

```text
typecheck
lint
production fixture build
complete Chromium browser regression
```

### Pull request universal gate

```text
deterministic backend simulator scenario
BM-09 repository scenario-matrix validation
@critical Chromium browser journey
```

### Nightly

```text
Chromium regression
Firefox and WebKit representative journeys
mobile Chrome and Safari responsive checks
baseline accessibility
resilience scenarios
```

### Weekly

```text
read-only critical flow repeated 10 times with one worker
```

### Manual soak

```text
read-only critical flow repeated 25 times with one worker
```

The manual soak boundary avoids silently increasing scheduled runtime and artifact usage before measured need is reviewed.

## BM-09 repository closure

BM-09 closes the repository-side bot-management scenario family through two coordinated artifacts:

```text
ai_platform/portal/e2e/scenarios/bot_management_closure.json
ai_platform/portal/web/e2e/specs/bots/full-product-closure.spec.ts
```

The versioned matrix maps each required family exactly once to existing narrow repository evidence. Validation fails when a family is missing, duplicated or references a path that does not exist.

The critical browser closure traverses:

```text
dashboard -> bot fleet -> bot detail -> exchange connections -> signals -> grid
```

It asserts explicit dry-run and unavailable-source semantics, records browser requests and rejects direct private Freqtrade mutation routes, Vault references and credential references. Lifecycle replay separately proves that accepted persisted command intent is not execution submission or execution proof.

`Portal Universal E2E` runs both the deterministic backend closure and the critical Chromium journey. Exact BM-09 head `e0a90ccdcfb3dc0e1ac03acede92f0f8c9da70e3` passed that gate in run `30437195047`, together with Portal Web CI `30437194948`, AI Platform CI `30437195010`, Freqtrade CI `30437194987` and workflow security `30437194958`.

This is repository acceptance only. Real Authentik, Vault, Synology, private Freqtrade and Cloudflare acceptance remain separate owner-managed evidence. P14 remains blocked.

## Adding a scenario

A pull request adding E2E coverage must satisfy:

```text
[ ] scenario is placed in one business domain
[ ] existing page/journey/factory is reused or extended
[ ] tags come from the central vocabulary
[ ] no arbitrary waitForTimeout is used
[ ] selectors are semantic and absent from high-level business flow where reusable
[ ] mutable identifiers are unique
[ ] failure output contains no secret material
[ ] dry-run, tenant, identity, risk and private-Freqtrade boundaries remain intact
[ ] the narrow command passes before the broader required gate
```

Real Cloudflare/Authentik staging acceptance remains a separately provisioned external E2E package. It must traverse the real protected path and may not reuse fixture identity as proof of production identity acceptance.
