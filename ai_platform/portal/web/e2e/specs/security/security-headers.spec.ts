import { buildContentSecurityPolicy } from "../../../lib/security-headers";
import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

const requiredInvariantHeaders = {
  "cross-origin-opener-policy": "same-origin",
  "cross-origin-resource-policy": "same-origin",
  "permissions-policy": "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
  "referrer-policy": "strict-origin-when-cross-origin",
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
} as const;

const privateBrowserOrigins = ["control-plane", "vault", "freqtrade", "exchange"];

test.describe("Portal browser security headers", { tag: [tags.critical, tags.security] }, () => {
  test("production CSP is nonce-bound and excludes unbounded/private sources", () => {
    const csp = buildContentSecurityPolicy("YWJjZGVmZ2hpamtsbW5vcA==", "production");

    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("script-src 'self' 'nonce-YWJjZGVmZ2hpamtsbW5vcA==' 'strict-dynamic'");
    expect(csp).toContain("style-src 'self' 'nonce-YWJjZGVmZ2hpamtsbW5vcA=='");
    expect(csp).toContain("connect-src 'self'");
    expect(csp).toContain("form-action 'self'");
    expect(csp).toContain("base-uri 'self'");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("upgrade-insecure-requests");
    expect(csp).not.toContain("'unsafe-eval'");
    expect(csp).not.toContain("*");
    for (const privateOrigin of privateBrowserOrigins) expect(csp).not.toContain(privateOrigin);
  });

  test("document responses use fresh nonces and render Next scripts with the response nonce", async ({
    identity,
    page,
  }) => {
    await identity.setState("anonymous");

    const first = await page.request.get("/login");
    const second = await page.request.get("/login");
    expect(first.status()).toBe(200);
    expect(second.status()).toBe(200);
    assertInvariantHeaders(first.headers());
    assertInvariantHeaders(second.headers());

    const firstCsp = requiredHeader(first.headers(), "content-security-policy");
    const secondCsp = requiredHeader(second.headers(), "content-security-policy");
    const firstNonce = nonceFromCsp(firstCsp);
    const secondNonce = nonceFromCsp(secondCsp);
    expect(secondNonce).not.toBe(firstNonce);
    assertDirectOriginPolicy(firstCsp, firstNonce);
    assertDirectOriginPolicy(secondCsp, secondNonce);

    const navigation = await page.goto("/login");
    expect(navigation).not.toBeNull();
    const navigationCsp = requiredHeader(navigation!.headers(), "content-security-policy");
    const navigationNonce = nonceFromCsp(navigationCsp);
    const scriptNonces = await page.locator("script[nonce]").evaluateAll((scripts) =>
      scripts.map((script) => (script as HTMLScriptElement).nonce).filter(Boolean),
    );
    expect(scriptNonces.length).toBeGreaterThan(0);
    expect(new Set(scriptNonces)).toEqual(new Set([navigationNonce]));
  });

  test("security headers cover protected redirects and API errors", async ({ identity, page }) => {
    await identity.setState("anonymous");

    const redirect = await page.request.get("/bots", { maxRedirects: 0 });
    expect([307, 308]).toContain(redirect.status());
    assertInvariantHeaders(redirect.headers());
    expect(requiredHeader(redirect.headers(), "content-security-policy")).toContain(
      "frame-ancestors 'none'",
    );

    const apiError = await page.request.post("/api/terminal", {
      data: { amount: "0.01", bot_id: "bot-btc-dryrun-01", pair: "BTC/USDT", side: "BUY" },
    });
    expect(apiError.status()).toBe(401);
    assertInvariantHeaders(apiError.headers());
    expect(requiredHeader(apiError.headers(), "content-security-policy")).toContain(
      "object-src 'none'",
    );
  });

  test("static Next assets retain invariant headers without a nonce policy", async ({
    identity,
    page,
  }) => {
    await identity.setState("anonymous");
    await page.goto("/login");
    const source = await page.locator("script[src]").first().getAttribute("src");
    expect(source).toBeTruthy();

    const asset = await page.request.get(source!);
    expect(asset.status()).toBe(200);
    assertInvariantHeaders(asset.headers());
  });
});

function assertInvariantHeaders(headers: Record<string, string>): void {
  for (const [name, value] of Object.entries(requiredInvariantHeaders)) {
    expect(requiredHeader(headers, name)).toBe(value);
  }
}

function assertDirectOriginPolicy(csp: string, nonce: string): void {
  expect(csp).toContain(`script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`);
  expect(csp).toContain(`style-src 'self' 'nonce-${nonce}'`);
  expect(csp).toContain("connect-src 'self'");
  expect(csp).toContain("frame-ancestors 'none'");
  expect(csp).not.toContain("*");
  for (const privateOrigin of privateBrowserOrigins) expect(csp).not.toContain(privateOrigin);
}

function nonceFromCsp(csp: string): string {
  const match = csp.match(/script-src[^;]*'nonce-([^']+)'/);
  if (!match?.[1]) throw new Error("CSP response does not contain a script nonce");
  return match[1];
}

function requiredHeader(headers: Record<string, string>, name: string): string {
  const value = headers[name.toLowerCase()];
  if (!value) throw new Error(`Missing required response header: ${name}`);
  return value;
}
