import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

const validIntent = {
  bot_id: "bot-btc-dryrun-01",
  pair: "BTC/USDT",
  side: "BUY",
  amount: "0.01",
};

test.describe("browser identity and session boundary", { tag: [tags.critical, tags.security] }, () => {
  test("anonymous protected page access redirects to product login", async ({ identity, page }) => {
    await identity.setState("anonymous");
    await page.goto("/bots");
    await expect(page).toHaveURL(/\/login\?.*return_to=%2Fbots/);
    await expect(page.getByRole("heading", { name: "Sign in to AI Trading Portal" })).toBeVisible();
    await expect(page.getByText("A portal session is required to continue.")).toBeVisible();
  });

  test("fixture login creates only an opaque portal session", async ({ identity, page }) => {
    await identity.setState("anonymous");
    await page.goto("/api/identity/login?return_to=%2Fbots");
    await expect(page).toHaveURL(/\/bots$/);
    await expect(page.getByRole("heading", { name: "Bot fleet" })).toBeVisible();
    await expect(page.getByLabel("Portal session")).toContainText("Tenant tenant-demo · MFA verified");
    const cookies = await page.context().cookies();
    expect(cookies.some((cookie) => cookie.name === "portal_fixture_session" && cookie.httpOnly)).toBe(true);
    expect(cookies.some((cookie) => cookie.name === "portal_fixture_csrf" && !cookie.httpOnly)).toBe(true);
    expect(cookies.some((cookie) => /access|refresh|id_token/i.test(cookie.name))).toBe(false);
  });

  test("same-origin callback completes the fixture session without token exposure", async ({
    identity,
    page,
  }) => {
    await identity.setState("anonymous");
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

  test("unsafe BFF request without double-submit header fails closed", async ({ identity, page }) => {
    await identity.setState("authenticated");
    const response = await page.request.post("/api/terminal", { data: validIntent });
    expect(response.status()).toBe(403);
    await expect(response.json()).resolves.toMatchObject({ code: "CSRF_MISSING" });
  });

  test("unsafe BFF request with mismatched CSRF token fails closed", async ({ identity, page }) => {
    await identity.setState("authenticated");
    const response = await page.request.post("/api/terminal", {
      headers: { "x-csrf-token": "wrong-token" },
      data: validIntent,
    });
    expect(response.status()).toBe(403);
    await expect(response.json()).resolves.toMatchObject({ code: "CSRF_MISMATCH" });
  });

  test("mutation-capable membership without MFA is denied server-side", async ({ identity, page }) => {
    await identity.setState("mfa_missing");
    const response = await page.request.post("/api/terminal", {
      headers: identity.csrfHeaders(),
      data: validIntent,
    });
    expect(response.status()).toBe(403);
    await expect(response.json()).resolves.toMatchObject({ code: "MFA_REQUIRED" });
  });

  test("stale authentication is denied when step-up is required", async ({ identity, page }) => {
    await identity.setState("step_up_stale");
    const response = await page.request.post("/api/terminal", {
      headers: identity.csrfHeaders(),
      data: validIntent,
    });
    expect(response.status()).toBe(403);
    await expect(response.json()).resolves.toMatchObject({ code: "STEP_UP_REQUIRED" });
  });

  for (const state of ["expired", "revoked"] as const) {
    test(`${state} session redirects to login with neutral recovery`, async ({ identity, page }) => {
      await identity.setState(state);
      await page.goto("/bots");
      await expect(page).toHaveURL(new RegExp(`/login\\?.*reason=session_${state}`));
      await expect(page.getByRole("heading", { name: "Sign in to AI Trading Portal" })).toBeVisible();
      await expect(page.getByText(/Sign in again to continue\./)).toBeVisible();
    });
  }

  test("logout-all revokes the browser session and future protected access", async ({ identity, page }) => {
    await identity.setState("authenticated");
    const response = await page.request.post("/api/identity/logout-all", {
      headers: identity.csrfHeaders(),
    });
    expect(response.status()).toBe(200);
    await expect(response.json()).resolves.toMatchObject({ revoked_sessions: 2 });
    expect((await page.request.get("/api/identity/session")).status()).toBe(401);
    await page.goto("/bots");
    await expect(page).toHaveURL(/\/login\?/);
  });

  test("cross-tenant membership is denied for pages and unsafe APIs", async ({ identity, page }) => {
    await identity.setState("cross_tenant");
    const response = await page.request.post("/api/terminal", {
      headers: identity.csrfHeaders(),
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
});
