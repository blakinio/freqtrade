# AI Trading Portal — P6.1 Web Shell Foundation

## Scope

P6.1 introduced the first isolated web application under `ai_platform/portal/web/`. It is a Next.js/React/TypeScript shell for portal-facing dry-run operations, not a public Freqtrade frontend.

This historical foundation task is **not equivalent to completion of the full P6 roadmap stage**. Full P6 also requires the broader core-operations surfaces declared in `DELIVERY_ROADMAP.md` and is tracked separately through `UI_DELIVERY_STATUS.md` and `FTAI-20260723-portal-ui-completion`.

Initial P6.1 routes:

- `/` — operational dashboard;
- `/bots` — tenant bot fleet read view;
- `/bots/new` — canonical dry-run bot creation form;
- `/denied` — explicit authorization-denied state;
- `/api/bots` — same-origin BFF boundary for bot list/create operations.

Later portal work may add routes without changing the trust boundary established here.

## Trust boundary

```text
Browser
  |
  | same-origin portal request
  v
Next.js portal web / BFF
  |
  | server-only private origin
  v
Portal Control Plane API
  |
  v
ExecutionAdapter -> private Freqtrade runtime
```

The browser does not receive a Freqtrade address, exchange endpoint, private control-plane origin or fabricated identity headers. `PORTAL_CONTROL_PLANE_URL` is read only by server-side code. Existing authenticated cookies may be forwarded to the control plane; P6.1 does not invent an authentication bypass.

## Data modes

### API mode

API mode is the default. It requires server-side `PORTAL_CONTROL_PLANE_URL` and `PORTAL_ENVIRONMENT`. Missing configuration fails closed rather than silently falling back to fixtures.

### Fixture mode

`PORTAL_WEB_DATA_MODE=fixture` is explicit deterministic development/E2E data. It is not selected by default and does not authorize live execution. Fixture-created bots remain `dry_run` and do not provision a trading runtime.

## Contract alignment

The web TypeScript mirror follows the canonical P1/P2 shapes used by `BotSpec`, `BotInstance`, environment and execution-mode contracts. The create-bot BFF performs a narrow runtime shape check before forwarding and accepts only `execution_mode = dry_run`; P2 remains the authoritative validation and authorization boundary.

## UX safety

The foundation keeps the environment badge visible on all initial routes and separates desired from observed bot state. Loading, empty, unavailable and denied states are intentional surfaces. Failure messaging explicitly states that a failed portal data request did not attempt a runtime action.

The dashboard labels snapshot freshness rather than implying that cached or fixture data is live. Production environment styling is visually distinct from test/research/staging.

## Validation

Dedicated web validation covers:

- dependency resolution and deterministic `npm ci`;
- TypeScript typecheck;
- ESLint;
- production Next.js build in explicit fixture/test mode;
- Chromium Playwright navigation and create-bot flow;
- BFF rejection of non-dry-run creation.

Repository Freqtrade CI and zizmor remain required before merge.

## Historical P6.1 exclusions

P6.1 intentionally did not implement:

- end-user OIDC/MFA/session issuance;
- exchange-secret creation;
- risk terminal or manual trade intents;
- direct runtime lifecycle integration from the browser;
- model promotion UI;
- full product navigation;
- the full set of core operations/product surfaces;
- live-capital authorization.

Some of these capabilities were delivered by later bounded workstreams. The remaining UI and read-model status is authoritative in `UI_DELIVERY_STATUS.md`; historical P6.1 completion must not be used to claim that the entire P6 stage was complete at PR #135.
