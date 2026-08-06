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

  test("logout response and browser history cannot restore protected content", async ({
    identity,
    page,
  }) => {
    await identity.setState("authenticated");
    const protectedPage = await page.goto("/bots");
    expect(protectedPage?.status()).toBe(200);
    assertPrivateNoStore(protectedPage!.headers());

    const logout = await page.request.post("/api/identity/logout", {
      headers: identity.csrfHeaders(),
    });
    expect(logout.status()).toBe(200);
    assertPrivateNoStore(logout.headers());

    await page.goto("/login");
    await page.goBack({ waitUntil: "domcontentloaded" });

    await expect(page).toHaveURL(/\/login\?/);
    expect(page.url()).toContain("reason=session_missing");
  });

  test("tenant change and browser history cannot restore the prior workspace", async ({
    identity,
    page,
  }) => {
    await identity.setState("authenticated");
    const protectedPage = await page.goto("/bots");
    expect(protectedPage?.status()).toBe(200);
    assertPrivateNoStore(protectedPage!.headers());

    await identity.setState("cross_tenant");
    await page.goto("/login");
    await page.goBack({ waitUntil: "domcontentloaded" });

    await expect(page).toHaveURL(/\/denied\?reason=cross_tenant$/);
  });

  test("static Next assets are not assigned the authenticated private policy", async ({
    identity,
    page,
  }) => {
    await identity.setState("anonymous");
    await page.goto("/login");
    const source = await page.locator("script[src]").first().getAttribute("src");
    expect(source).toBeTruthy();

    const asset = await page.request.get(source!);
    expect(asset.status()).toBe(200);
    expect(cacheDirectives(asset.headers())).not.toContain("private");
  });
});

function assertPrivateNoStore(headers: Record<string, string>): void {
  const directives = cacheDirectives(headers);
  expect(directives).toContain("private");
  expect(directives).toContain("no-store");
}

function cacheDirectives(headers: Record<string, string>): string[] {
  return (headers["cache-control"] ?? "")
    .split(",")
    .map((directive) => directive.trim().toLowerCase())
    .filter(Boolean);
}
