import { chromium } from "@playwright/test";

const origin = process.env.WICKHUNTER_BROWSER_ORIGIN ?? "https://127.0.0.1:3443";
const expectedMode = (process.env.WICKHUNTER_EXPECTED_MODE ?? "shadow").toLowerCase();
const expectedDesiredGeneration = process.env.WICKHUNTER_EXPECTED_DESIRED_GENERATION ?? "";
const expectedObservedGeneration = process.env.WICKHUNTER_EXPECTED_OBSERVED_GENERATION ?? "";
const sessionToken = "wickhunter-browser-session-" + "s".repeat(40);
const csrfToken = "wickhunter-browser-csrf-" + "c".repeat(40);

if (!new Set(["shadow", "paper"]).has(expectedMode)) {
  throw new Error(`unsupported WICKHUNTER_EXPECTED_MODE=${expectedMode}`);
}
if (Boolean(expectedDesiredGeneration) !== Boolean(expectedObservedGeneration)) {
  throw new Error("both expected generation ids must be provided together");
}
const shortId = (value) => (value.length <= 12 ? value : `${value.slice(0, 12)}…`);

const browser = await chromium.launch({ headless: true });
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

  const common = ["WickHunter", "wickhunter", "Canonical RuntimeGeneration", "Generation: desired = observed"];
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
  if (expectedMode === "shadow" && !(await page.locator("body").innerText()).includes("HEALTHY")) {
    throw new Error("WickHunter HEALTHY state is not visible");
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
} finally {
  await browser.close();
}
