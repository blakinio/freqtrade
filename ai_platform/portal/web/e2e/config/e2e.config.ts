export const tags = {
  smoke: "@smoke",
  critical: "@critical",
  regression: "@regression",
  security: "@security",
  permissions: "@permissions",
  crossBrowser: "@cross-browser",
  responsive: "@responsive",
  accessibility: "@a11y",
  resilience: "@resilience",
  stability: "@stability",
  soak: "@soak",
} as const;

export const fixtureCsrfToken = "fixture-csrf-token";

export const e2eEnvironment = {
  baseURL: process.env.PORTAL_E2E_BASE_URL ?? "http://127.0.0.1:3100",
  environment: process.env.PORTAL_ENVIRONMENT ?? "test",
  dataMode: process.env.PORTAL_WEB_DATA_MODE ?? "fixture",
  identityFixtureMode: process.env.PORTAL_IDENTITY_FIXTURE_MODE ?? "enabled",
  startsLocalServer: !process.env.PORTAL_E2E_BASE_URL,
} as const;
