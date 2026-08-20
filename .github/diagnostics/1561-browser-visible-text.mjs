import crypto from "node:crypto";
import { chromium } from "@playwright/test";

const origin = process.env.WICKHUNTER_BROWSER_ORIGIN;
const sessionToken = process.env.WICKHUNTER_SESSION_TOKEN;
if (!origin || !sessionToken) throw new Error("bounded browser diagnostic inputs are required");

const browser = await chromium.launch({
  headless: true,
  executablePath: "/usr/bin/chromium",
  args: ["--no-sandbox"],
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
  ]);
  const page = await context.newPage();
  const response = await page.goto(`${origin}/bots`, { waitUntil: "networkidle" });
  const bodyText = await page.locator("body").innerText();
  const probes = {
    response_status: response?.status() ?? null,
    final_url: page.url(),
    title: await page.title(),
    h1: await page.locator("h1").allInnerTexts(),
    body_chars: bodyText.length,
    body_sha256: crypto.createHash("sha256").update(bodyText).digest("hex"),
    contains_bot_operations: bodyText.includes("Bot operations"),
    contains_bot_fleet: bodyText.includes("Bot fleet"),
    contains_wickhunter_id: bodyText.includes("wickhunter"),
    contains_wickhunter_name: bodyText.includes("WickHunter"),
    contains_canonical_runtime: bodyText.includes("Canonical RuntimeGeneration"),
    contains_generation_converged: bodyText.includes("Generation: desired = observed"),
    contains_healthy: bodyText.includes("HEALTHY"),
    contains_decision_counts: /Decisions: \d+ · NO_TRADE: \d+/u.test(bodyText),
    contains_no_match: bodyText.includes("No bots match the current filters"),
    contains_login: /login|sign in/iu.test(bodyText),
    contains_error: /internal server error|application error|something went wrong/iu.test(bodyText),
  };
  console.log(JSON.stringify(probes, null, 2));
} finally {
  await browser.close();
}
