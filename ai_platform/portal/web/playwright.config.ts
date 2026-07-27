import { defineConfig, devices } from "@playwright/test";

import { e2eEnvironment, tags } from "./e2e/config/e2e.config";

export default defineConfig({
  testDir: "./e2e/specs",
  outputDir: "./artifacts/test-results",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["list"],
    ["html", { outputFolder: "artifacts/playwright-report", open: "never" }],
    ["json", { outputFile: "artifacts/results.json" }],
  ],
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: e2eEnvironment.baseURL,
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium-desktop",
      grepInvert: new RegExp(
        `${tags.accessibility}|${tags.resilience}|${tags.stability}|${tags.soak}`,
      ),
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "chromium-accessibility",
      grep: new RegExp(tags.accessibility),
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "chromium-resilience",
      grep: new RegExp(tags.resilience),
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox-desktop",
      grep: new RegExp(tags.crossBrowser),
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit-desktop",
      grep: new RegExp(tags.crossBrowser),
      use: { ...devices["Desktop Safari"] },
    },
    {
      name: "mobile-chrome",
      grep: new RegExp(tags.responsive),
      use: { ...devices["Pixel 7"] },
    },
    {
      name: "mobile-safari",
      grep: new RegExp(tags.responsive),
      use: { ...devices["iPhone 15"] },
    },
    {
      name: "chromium-stability",
      grep: new RegExp(tags.stability),
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "chromium-soak",
      grep: new RegExp(tags.soak),
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: e2eEnvironment.startsLocalServer
    ? {
        command: "npm run dev -- --hostname 127.0.0.1 --port 3100",
        url: e2eEnvironment.baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
        env: {
          ...process.env,
          PORTAL_WEB_DATA_MODE: e2eEnvironment.dataMode,
          PORTAL_ENVIRONMENT: e2eEnvironment.environment,
          PORTAL_IDENTITY_FIXTURE_MODE: e2eEnvironment.identityFixtureMode,
        },
      }
    : undefined,
});
