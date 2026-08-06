import {
  applyPrivateNoStoreCachePolicy,
  PRIVATE_NO_STORE_CACHE_CONTROL,
} from "../../../lib/response-cache-policy";
import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

const representativeStatuses = [200, 401, 403, 404, 409, 500] as const;

test.describe("Portal authenticated response cache boundary", {
  tag: [tags.critical, tags.security],
}, () => {
  test("canonical policy is status-independent and fail-closed", () => {
    for (const status of representativeStatuses) {
      const response = new Response(null, { status });
      response.headers.set("cache-control", "public, max-age=3600");

      applyPrivateNoStoreCachePolicy(response);

      expect(response.headers.get("cache-control")).toBe(PRIVATE_NO_STORE_CACHE_CONTROL);
    }
  });

  test("documents, redirects and API success/error responses are private no-store", async ({
    identity,
    page,
  }) => {
    await identity.setState("anonymous");

    const login = await page.request.get("/login");
    expect(login.status()).toBe(200);
    assertPrivateNoStore(login.headers());

    const redirect = await page.request.get("/bots", { maxRedirects: 0 });
    expect([307, 308]).toContain(redirect.status());
    assertPrivateNoStore(redirect.headers());

    const unauthorized = await page.request.post("/api/terminal", {
      data: { amount: "0.01", bot_id: "bot-btc-dryrun-01", pair: "BTC/USDT", side: "BUY" },
    });
    expect(unauthorized.status()).toBe(401);
    assertPrivateNoStore(unauthorized.headers());

    await identity.setState("cross_tenant");
    const forbidden = await page.request.post("/api/terminal", {
      data: { amount: "0.01", bot_id: "bot-btc-dryrun-01", pair: "BTC/USDT", side: "BUY" },
    });
    expect(forbidden.status()).toBe(403);
    assertPrivateNoStore(forbidden.headers());

    await identity.setState("authenticated");
    const success = await page.request.get("/api/identity/session");
    expect(success.status()).toBe(200);
    assertPrivateNoStore(success.headers());

    const notFound = await page.request.get("/api/route-that-does-not-exist");
    expect(notFound.status()).toBe(404);
    assertPrivateNoStore(notFound.headers());
  });

  test("browser history cannot restore a protected page after logout", async ({ identity, page }) => {
    await identity.setState("authenticated");
    await page.goto("/bots");
    await expect(page).toHaveURL(/\/bots$/);

    await identity.setState("anonymous");
    await page.goto("/login");
    await page.goBack();

    await expect(page).toHaveURL(/\/login\?/);
    expect(page.url()).toContain("reason=session_missing");
  });

  test("static Next assets are not assigned the authenticated no-store policy", async ({
    identity,
    page,
  }) => {
    await identity.setState("anonymous");
    await page.goto("/login");
    const source = await page.locator("script[src]").first().getAttribute("src");
    expect(source).toBeTruthy();

    const asset = await page.request.get(source!);
    expect(asset.status()).toBe(200);
    expect(asset.headers()["cache-control"]).not.toBe(PRIVATE_NO_STORE_CACHE_CONTROL);
  });
});

function assertPrivateNoStore(headers: Record<string, string>): void {
  expect(headers["cache-control"]).toBe(PRIVATE_NO_STORE_CACHE_CONTROL);
}
