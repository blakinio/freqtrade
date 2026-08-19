import fs from "node:fs";
import { chromium } from "@playwright/test";

const origin = process.env.WICKHUNTER_BROWSER_ORIGIN ?? "https://127.0.0.1:3443";
const expectedMode = (process.env.WICKHUNTER_EXPECTED_MODE ?? "shadow").toLowerCase();
const expectedDesiredGeneration = process.env.WICKHUNTER_EXPECTED_DESIRED_GENERATION ?? "";
const expectedObservedGeneration = process.env.WICKHUNTER_EXPECTED_OBSERVED_GENERATION ?? "";
const sessionToken =
  process.env.WICKHUNTER_SESSION_TOKEN ?? "wickhunter-browser-session-" + "s".repeat(40);
const csrfToken =
  process.env.WICKHUNTER_CSRF_TOKEN ?? "wickhunter-browser-csrf-" + "c".repeat(40);
const browserExecutablePath = process.env.WICKHUNTER_BROWSER_EXECUTABLE_PATH ?? "";
const evidencePath = process.env.WICKHUNTER_BROWSER_EVIDENCE_PATH ?? "";

if (!new Set(["shadow", "paper"]).has(expectedMode)) {
  throw new Error(`unsupported WICKHUNTER_EXPECTED_MODE=${expectedMode}`);
}
if (Boolean(expectedDesiredGeneration) !== Boolean(expectedObservedGeneration)) {
  throw new Error("both expected generation ids must be provided together");
}
if (sessionToken.length < 48) {
  throw new Error("WickHunter browser session token is too short");
}
const shortId = (value) => (value.length <= 12 ? value : `${value.slice(0, 12)}…`);

const browser = await chromium.launch({
  headless: true,
  ...(browserExecutablePath ? { executablePath: browserExecutablePath } : {}),
});
try {
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  await context.addCookies([
    {
      name: "__Host-portal_session",
      value: sessionToken,
      url: origin,
      secure: true,
      httpOnly: true,
      sameSite: "Lax",
    },
    {
      name: "__Host-portal_csrf",
      value: csrfToken,
      url: origin,
      secure: true,
      httpOnly: false,
      sameSite: "Lax",
    },
  ]);

  const page = await context.newPage();
  const response = await page.goto(`${origin}/bots`, { waitUntil: "networkidle" });
  if (!response || response.status() !== 200) {
    throw new Error(`WickHunter bots page failed: ${response?.status()}`);
  }

  const common = [
    "WickHunter",
    "wickhunter",
    "Canonical RuntimeGeneration",
    "Generation: desired = observed",
  ];
  const expected =
    expectedMode === "shadow"
      ? [
          ...common,
          "SHADOW · wh09-h900-v1",
          "no_trade_confidence=0.60",
          "PAPER: inactive · LIVE: BLOCKED",
          "Credentials: absent",
          "Order adapter: absent",
          "Execution: disabled · Orders: 0",
          "Live capital: false",
        ]
      : [
          ...common,
          "PAPER · wh09-h900-v1",
          "Legacy SHADOW evidence: not applicable in PAPER",
        ];
  if (expectedDesiredGeneration) {
    expected.push(
      `D ${shortId(expectedDesiredGeneration)} · O ${shortId(expectedObservedGeneration)}`,
    );
  }

  for (const text of expected) {
    await page.getByText(text, { exact: true }).waitFor();
  }
  const bodyText = await page.locator("body").innerText();
  if (expectedMode === "shadow" && !bodyText.includes("HEALTHY")) {
    throw new Error("WickHunter HEALTHY state is not visible");
  }
  const counts = /Decisions: (\d+) · NO_TRADE: (\d+)/u.exec(bodyText);
  if (expectedMode === "shadow" && (!counts || Number(counts[1]) <= 0 || Number(counts[2]) <= 0)) {
    throw new Error("durable WickHunter decision/NO_TRADE counters are not visible");
  }
  const cookies = await context.cookies();
  if (cookies.some((cookie) => cookie.name.startsWith("portal_fixture_"))) {
    throw new Error("fixture authentication cookie appeared in API-mode browser journey");
  }

  await page.reload({ waitUntil: "networkidle" });
  await page.getByText("WickHunter", { exact: true }).waitFor();
  await page.getByText(
    expectedMode === "shadow" ? "SHADOW · wh09-h900-v1" : "PAPER · wh09-h900-v1",
    { exact: true },
  ).waitFor();
  await page.getByText("Generation: desired = observed", { exact: true }).waitFor();
  if (expectedDesiredGeneration) {
    await page
      .getByText(
        `D ${shortId(expectedDesiredGeneration)} · O ${shortId(expectedObservedGeneration)}`,
        { exact: true },
      )
      .waitFor();
  }

  if (evidencePath) {
    fs.writeFileSync(
      evidencePath,
      `${JSON.stringify(
        {
          result: "PASS",
          origin,
          mode: expectedMode,
          authenticated: true,
          fixture_cookie_present: false,
          health_visible: expectedMode === "shadow" ? true : null,
          decision_count: counts ? Number(counts[1]) : null,
          no_trade_count: counts ? Number(counts[2]) : null,
          runtime_generation_converged: true,
          reload_persistence: true,
        },
        null,
        2,
      )}\n`,
      { encoding: "utf-8", mode: 0o600 },
    );
  }
} finally {
  await browser.close();
}
