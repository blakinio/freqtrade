import crypto from "node:crypto";
import fs from "node:fs";
import { chromium } from "@playwright/test";

const origin = process.env.WICKHUNTER_BROWSER_ORIGIN ?? "https://127.0.0.1:3443";
const expectedMode = (process.env.WICKHUNTER_EXPECTED_MODE ?? "shadow").toLowerCase();
const expectedModelVersion = process.env.WICKHUNTER_EXPECTED_MODEL_VERSION ?? "wh09-h900-v1";
const expectedDesiredGeneration = process.env.WICKHUNTER_EXPECTED_DESIRED_GENERATION ?? "";
const expectedObservedGeneration = process.env.WICKHUNTER_EXPECTED_OBSERVED_GENERATION ?? "";
const sessionToken =
  process.env.WICKHUNTER_SESSION_TOKEN ?? "wickhunter-browser-session-" + "s".repeat(40);
const csrfToken =
  process.env.WICKHUNTER_CSRF_TOKEN ?? "wickhunter-browser-csrf-" + "c".repeat(40);
const browserExecutablePath = process.env.WICKHUNTER_BROWSER_EXECUTABLE_PATH ?? "";
const evidencePath = process.env.WICKHUNTER_BROWSER_EVIDENCE_PATH ?? "";
const noSandbox = process.env.WICKHUNTER_BROWSER_NO_SANDBOX === "1";
const maxPageAttempts = 3;

if (!new Set(["shadow", "paper"]).has(expectedMode)) {
  throw new Error(`unsupported WICKHUNTER_EXPECTED_MODE=${expectedMode}`);
}
if (!expectedModelVersion) {
  throw new Error("WICKHUNTER_EXPECTED_MODEL_VERSION must be non-empty");
}
if (Boolean(expectedDesiredGeneration) !== Boolean(expectedObservedGeneration)) {
  throw new Error("both expected generation ids must be provided together");
}
if (sessionToken.length < 48) {
  throw new Error("WickHunter browser session token is too short");
}
const shortId = (value) => (value.length <= 12 ? value : `${value.slice(0, 12)}…`);
const expectedBotsUrl = new URL("/bots", origin).toString();
const expectedModeModelMarker = `${expectedMode.toUpperCase()} · ${expectedModelVersion}`;

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
        expectedModeModelMarker,
        "no_trade_confidence=0.60",
        "PAPER: inactive · LIVE: BLOCKED",
        "Credentials: absent",
        "Order adapter: absent",
        "Execution: disabled · Orders: 0",
        "Live capital: false",
      ]
    : [...common, expectedModeModelMarker, "Legacy SHADOW evidence: not applicable in PAPER"];
if (expectedDesiredGeneration) {
  expected.push(
    `D ${shortId(expectedDesiredGeneration)} · O ${shortId(expectedObservedGeneration)}`,
  );
}

const writeEvidence = (payload) => {
  console.log(`WICKHUNTER_EVIDENCE=${JSON.stringify(payload)}`);
  if (!evidencePath) return;
  fs.writeFileSync(evidencePath, `${JSON.stringify(payload, null, 2)}\n`, {
    encoding: "utf-8",
    mode: 0o600,
  });
};

const inspectVisibleTruth = async (page, response) => {
  const bodyText = await page.locator("body").innerText();
  const counts = /Decisions: (\d+) · NO_TRADE: (\d+)/u.exec(bodyText);
  const missing = expected.filter((text) => !bodyText.includes(text));
  const finalUrl = page.url();
  const responseStatus = response?.status() ?? null;
  const urlMatches = finalUrl === expectedBotsUrl;
  const healthVisible = expectedMode === "shadow" ? bodyText.includes("HEALTHY") : null;
  const countersVisible =
    expectedMode === "shadow"
      ? Boolean(counts && Number(counts[1]) > 0 && Number(counts[2]) > 0)
      : true;
  return {
    bodyText,
    counts,
    missing,
    finalUrl,
    responseStatus,
    urlMatches,
    healthVisible,
    countersVisible,
    ready:
      responseStatus === 200 &&
      urlMatches &&
      missing.length === 0 &&
      healthVisible !== false &&
      countersVisible,
  };
};

const loadVisibleTruth = async (page, reloadOnly = false) => {
  let snapshot = null;
  for (let attempt = 1; attempt <= maxPageAttempts; attempt += 1) {
    const response =
      reloadOnly || attempt > 1
        ? await page.reload({ waitUntil: "networkidle" })
        : await page.goto(expectedBotsUrl, { waitUntil: "networkidle" });
    snapshot = await inspectVisibleTruth(page, response);
    if (snapshot.ready) return snapshot;
    if (attempt < maxPageAttempts) {
      await page.waitForTimeout(3000);
    }
  }
  return snapshot;
};

const browser = await chromium.launch({
  headless: true,
  ...(browserExecutablePath ? { executablePath: browserExecutablePath } : {}),
  ...(noSandbox ? { args: ["--no-sandbox"] } : {}),
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
  const first = await loadVisibleTruth(page);
  const cookies = await context.cookies();
  const fixtureCookiePresent = cookies.some((cookie) => cookie.name.startsWith("portal_fixture_"));
  const provenance = {
    expected_model_version: expectedModelVersion,
    expected_desired_generation: expectedDesiredGeneration || null,
    expected_observed_generation: expectedObservedGeneration || null,
  };

  if (!first?.ready || fixtureCookiePresent) {
    const bodyText = first?.bodyText ?? "";
    writeEvidence({
      result: "FAIL",
      origin,
      mode: expectedMode,
      authenticated: Boolean(first?.urlMatches),
      fixture_cookie_present: fixtureCookiePresent,
      response_status: first?.responseStatus ?? null,
      final_url: first?.finalUrl ?? page.url(),
      missing_visible_markers: first?.missing ?? expected,
      health_visible: first?.healthVisible ?? null,
      decision_counters_visible: first?.countersVisible ?? false,
      body_chars: bodyText.length,
      body_sha256: crypto.createHash("sha256").update(bodyText).digest("hex"),
      runtime_generation_converged: false,
      reload_persistence: false,
      ...provenance,
    });
    if (fixtureCookiePresent) {
      throw new Error("fixture authentication cookie appeared in API-mode browser journey");
    }
    if (!first?.urlMatches) {
      throw new Error(`deployed browser left canonical /bots path: ${first?.finalUrl ?? page.url()}`);
    }
    if (first?.responseStatus !== 200) {
      throw new Error(`WickHunter bots page failed: ${first?.responseStatus}`);
    }
    throw new Error(`deployed WickHunter truth did not converge in browser: ${(first?.missing ?? []).join(", ")}`);
  }

  const reload = await loadVisibleTruth(page, true);
  if (!reload?.ready) {
    const bodyText = reload?.bodyText ?? "";
    writeEvidence({
      result: "FAIL",
      origin,
      mode: expectedMode,
      authenticated: Boolean(reload?.urlMatches),
      fixture_cookie_present: fixtureCookiePresent,
      response_status: reload?.responseStatus ?? null,
      final_url: reload?.finalUrl ?? page.url(),
      missing_visible_markers: reload?.missing ?? expected,
      health_visible: reload?.healthVisible ?? null,
      decision_counters_visible: reload?.countersVisible ?? false,
      body_chars: bodyText.length,
      body_sha256: crypto.createHash("sha256").update(bodyText).digest("hex"),
      runtime_generation_converged: false,
      reload_persistence: false,
      ...provenance,
    });
    throw new Error("deployed WickHunter truth did not persist after bounded reload validation");
  }

  writeEvidence({
    result: "PASS",
    origin,
    mode: expectedMode,
    authenticated: true,
    fixture_cookie_present: false,
    health_visible: expectedMode === "shadow" ? true : null,
    decision_count: reload.counts ? Number(reload.counts[1]) : null,
    no_trade_count: reload.counts ? Number(reload.counts[2]) : null,
    runtime_generation_converged: true,
    reload_persistence: true,
    ...provenance,
  });
} finally {
  await browser.close();
}
