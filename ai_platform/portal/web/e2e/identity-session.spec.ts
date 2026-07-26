import { expect, test, type Page } from "@playwright/test";

const csrfToken = "fixture-csrf-token";

type FixtureState =
  | "authenticated"
  | "anonymous"
  | "expired"
  | "revoked"
  | "mfa_missing"
  | "step_up_stale"
  | "cross_tenant";

async function setIdentityState(page: Page, state: FixtureState) {
  const response = await page.request.post("/api/identity/fixture-state", { data: { state } });
  expect(response.status()).toBe(200);
}

const validIntent = {
  bot_id: "bot-btc-dryrun-01",
  pair: "BTC/USDT",
  side: "BUY",
  amount: "0.01",
};

test("anonymous protected page access redirects to product login", async ({ page }) => {
  await setIdentityState(page, "anonymous");
  await page.goto("/bots");
  await expect(page).toHaveURL(/\/login\?.*return_to=%2Fbots/);
  await expect(page.getByRole("heading", { name: "Sign in to AI Trading Portal" })).toBeVisible();
  await expect(page.getByText("A portal session is required to continue.")).toBeVisible();
});

test("fixture login creates only an opaque portal session and returns to the requested page", async ({
  page,
}) => {
  await setIdentityState(page, "anonymous");
  await page.goto("/api/identity/login?return_to=%2Fbots");
  await expect(page).toHaveURL(/\/bots$/);
  await expect(page.getByRole("heading", { name: "Bot fleet" })).toBeVisible();
  await expect(page.getByLabel("Portal session")).toContainText("Tenant tenant-demo · MFA verified");
  const cookies = await page.context().cookies();
  expect(cookies.some((cookie) => cookie.name === "portal_fixture_session" && cookie.httpOnly)).toBe(true);
  expect(cookies.some((cookie) => cookie.name === "portal_fixture_csrf" && !cookie.httpOnly)).toBe(true);
  expect(cookies.some((cookie) => /access|refresh|id_token/i.test(cookie.name))).toBe(false);
});

test("same-origin callback completes the fixture browser session without token exposure", async ({
  page,
}) => {
  await setIdentityState(page, "anonymous");
  await page.goto("/api/identity/callback?code=fixture&state=fixture&return_to=%2F");
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  const session = await page.request.get("/api/identity/session");
  expect(session.status()).toBe(200);
  await expect(session.json()).resolves.toMatchObject({
    tenant_id: "tenant-demo",
    mfa_satisfied: true,
  });
});

test("unsafe BFF request without double-submit header fails closed", async ({ page }) => {
  await setIdentityState(page, "authenticated");
  const response = await page.request.post("/api/terminal", { data: validIntent });
  expect(response.status()).toBe(403);
  await expect(response.json()).resolves.toMatchObject({ code: "CSRF_MISSING" });
});

test("unsafe BFF request with mismatched CSRF token fails closed", async ({ page }) => {
  await setIdentityState(page, "authenticated");
  const response = await page.request.post("/api/terminal", {
    headers: { "x-csrf-token": "wrong-token" },
    data: validIntent,
  });
  expect(response.status()).toBe(403);
  await expect(response.json()).resolves.toMatchObject({ code: "CSRF_MISMATCH" });
});

test("mutation-capable membership without MFA is denied server-side", async ({ page }) => {
  await setIdentityState(page, "mfa_missing");
  const response = await page.request.post("/api/terminal", {
    headers: { "x-csrf-token": csrfToken },
    data: validIntent,
  });
  expect(response.status()).toBe(403);
  await expect(response.json()).resolves.toMatchObject({ code: "MFA_REQUIRED" });
});

test("stale authentication is denied when step-up is required", async ({ page }) => {
  await setIdentityState(page, "step_up_stale");
  const response = await page.request.post("/api/terminal", {
    headers: { "x-csrf-token": csrfToken },
    data: validIntent,
  });
  expect(response.status()).toBe(403);
  await expect(response.json()).resolves.toMatchObject({ code: "STEP_UP_REQUIRED" });
});

for (const state of ["expired", "revoked"] as const) {
  test(`${state} session redirects to login with a neutral recovery message`, async ({ page }) => {
    await setIdentityState(page, state);
    await page.goto("/bots");
    await expect(page).toHaveURL(new RegExp(`/login\\?.*reason=session_${state}`));
    await expect(page.getByRole("heading", { name: "Sign in to AI Trading Portal" })).toBeVisible();
    await expect(page.getByText(/Sign in again to continue\./)).toBeVisible();
  });
}

test("logout-all revokes the browser session and future protected access", async ({ page }) => {
  await setIdentityState(page, "authenticated");
  const response = await page.request.post("/api/identity/logout-all", {
    headers: { "x-csrf-token": csrfToken },
  });
  expect(response.status()).toBe(200);
  await expect(response.json()).resolves.toMatchObject({ revoked_sessions: 2 });
  expect((await page.request.get("/api/identity/session")).status()).toBe(401);
  await page.goto("/bots");
  await expect(page).toHaveURL(/\/login\?/);
});

test("cross-tenant fixture membership is denied for pages and unsafe APIs", async ({ page }) => {
  await setIdentityState(page, "cross_tenant");
  const response = await page.request.post("/api/terminal", {
    headers: { "x-csrf-token": csrfToken },
    data: validIntent,
  });
  expect(response.status()).toBe(403);
  await expect(response.json()).resolves.toMatchObject({ code: "CROSS_TENANT_DENIED" });
  await page.goto("/bots");
  await expect(page).toHaveURL(/\/denied\?reason=cross_tenant/);
  await expect(
    page.getByRole("heading", { name: "You do not have permission to view this resource" }),
  ).toBeVisible();
});
