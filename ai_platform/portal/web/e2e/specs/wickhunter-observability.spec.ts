import { expect, test } from "@playwright/test";

const API_PATH = "/api/market/wickhunter";

test.describe("WickHunter runtime observability", () => {
  test("@critical requires identity and renders a read-only runtime snapshot", async ({ page }) => {
    const anonymous = await page.request.get(API_PATH);
    expect(anonymous.status()).toBe(401);

    await page.goto("/market/wickhunter");
    await expect(page.getByRole("heading", { name: "WickHunter Observability" })).toBeVisible();
    await expect(page.getByTestId("runtime-mode")).toHaveText("shadow");
    await expect(page.getByTestId("runtime-health")).toContainText("healthy");
    await expect(page.getByTestId("dynamic-universe")).toContainText("BTCUSDT");
    await expect(page.getByTestId("dynamic-universe")).toContainText("ETHUSDT");
    await expect(page.getByTestId("source-binance-usdm")).toContainText("healthy");
    await expect(page.getByTestId("decision-ETHUSDT")).toContainText("rejected_by_risk");
    await expect(page.getByTestId("risk-rejection-count")).toContainText("1");
    await expect(page.getByTestId("position-BTCUSDT")).toContainText("65100");
    await expect(page.getByTestId("circuit-breaker")).toContainText("nieaktywny");
    await expect(page.getByTestId("authority-boundary")).toContainText("Złożone zlecenia: 0");

    await expect(
      page.getByRole("button", { name: /trade|order|live trading|submit|execute|kup|sprzedaj/i }),
    ).toHaveCount(0);

    const response = await page.request.get(API_PATH);
    expect(response.status()).toBe(200);
    expect(response.headers()["cache-control"]).toContain("no-store");
    const body = await response.text();
    expect(body).not.toMatch(/api[_-]?key|secret|passphrase/i);
    expect(body).not.toContain("/volume1/");
    expect(body).not.toContain("/var/lib/");
    expect(body.length).toBeLessThan(100_000);
    const payload = JSON.parse(body) as {
      snapshot: {
        read_only: boolean;
        trading_credentials_present: boolean;
        order_adapter_present: boolean;
        orders_submitted: number;
        live_capital_authorized: boolean;
      };
    };
    expect(payload.snapshot).toMatchObject({
      read_only: true,
      trading_credentials_present: false,
      order_adapter_present: false,
      orders_submitted: 0,
      live_capital_authorized: false,
    });
  });

  test("@permissions denies cross-tenant identity", async ({ page }) => {
    const state = await page.request.post("/api/identity/fixture-state", {
      data: { state: "cross_tenant" },
    });
    expect(state.status()).toBe(200);
    const response = await page.request.get(API_PATH);
    expect(response.status()).toBe(403);
    await page.goto("/market/wickhunter");
    await expect(page).toHaveURL(/\/denied\?reason=cross_tenant/u);
  });
});
