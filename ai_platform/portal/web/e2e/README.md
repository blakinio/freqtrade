# Portal E2E tests

This directory contains browser and same-origin BFF acceptance tests for the AI Trading Portal. It validates the portal boundary above private Freqtrade runtimes; it does not connect browser tests directly to Freqtrade or authorize live capital.

## Structure

```text
e2e/
├── config/       environment and tag vocabulary
├── data/         deterministic factories and canonical request data
├── fixtures/     composed Playwright fixtures and failure evidence
├── journeys/     multi-step user and BFF workflows
├── pages/        reusable page/component interactions
├── specs/        domain-owned test scenarios
└── support/      accessibility, layout and evidence helpers
```

A scenario exists once under its business domain. Smoke, critical, regression, security, responsive, resilience, stability and soak suites are selected with tags rather than copied into suite-specific directories.

## Commands

```bash
npm run test:e2e                 # complete Chromium regression used by Portal Web CI
npm run test:e2e:smoke           # minimum portal availability and navigation
npm run test:e2e:critical        # PR integration gate
npm run test:e2e:regression      # all configured browser projects
npm run test:e2e:cross-browser   # representative desktop browser coverage
npm run test:e2e:security        # identity, tenant, CSRF, MFA and fail-closed checks
npm run test:e2e:a11y            # baseline critical-page accessibility checks
npm run test:e2e:responsive      # representative Android and iPhone layouts
npm run test:e2e:resilience      # deterministic dependency failure scenarios
npm run test:e2e:stability       # repeated read-only critical journey
npm run test:e2e:soak            # longer manual repeated journey
```

Local execution starts the Next.js server in deterministic fixture mode. Set `PORTAL_E2E_BASE_URL` to test an already running fixture-enabled preview instead. Real Authentik/Cloudflare staging acceptance remains a separate externally provisioned suite and must not introduce an authentication bypass.

## Test rules

- Use accessible locators (`getByRole`, `getByLabel`, `getByText`) before test IDs.
- Keep selectors and repeated UI mechanics in pages or journeys.
- Create unique mutable data with a factory; never depend on execution order.
- Do not use `waitForTimeout`; wait for visible UI or explicit state.
- Keep all bot creation dry-run and all execution tests fail-closed.
- Do not expose exchange credentials, browser tokens or private Freqtrade endpoints.
- Add tags from `config/e2e.config.ts`; do not invent local tag spellings.
- Preserve failure traces, screenshots, videos, redacted console evidence and failed-request summaries.

## CI matrix

- Pull request: full Chromium portal regression plus a separate critical universal journey.
- Nightly: configured desktop browsers, mobile projects, accessibility and resilience.
- Weekly: repeated read-only stability flow.
- Soak: manual only until runtime cost and evidence retention are reviewed.

Failure artifacts are uploaded only for failed jobs and retained for seven days to control storage use.
