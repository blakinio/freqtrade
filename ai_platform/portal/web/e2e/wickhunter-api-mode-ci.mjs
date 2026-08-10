import { chromium } from "@playwright/test";

const origin = process.env.WICKHUNTER_BROWSER_ORIGIN ?? "https://127.0.0.1:3443";
const sessionToken = "wickhunter-browser-session-" + "s".repeat(40);
const csrfToken = "wickhunter-browser-csrf-" + "c".repeat(40);

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

  for (const text of [
    "WickHunter",
    "wickhunter",
    "SHADOW · H900",
    "no_trade_confidence=0.60",
    "PAPER: inactive · LIVE: BLOCKED",
    "Credentials: absent",
    "Order adapter: absent",
    "Execution: disabled · Orders: 0",
    "Live capital: false",
    "Generation: desired = observed",
  ]) {
    await page.getByText(text, { exact: true }).waitFor();
  }
  if (!(await page.locator("body").innerText()).includes("HEALTHY")) {
    throw new Error("WickHunter HEALTHY state is not visible");
  }

  await page.reload({ waitUntil: "networkidle" });
  await page.getByText("WickHunter", { exact: true }).waitFor();
  await page.getByText("SHADOW · H900", { exact: true }).waitFor();
  await page.getByText("Generation: desired = observed", { exact: true }).waitFor();
} finally {
  await browser.close();
}
