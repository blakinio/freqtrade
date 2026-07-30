import { expect, test } from "@playwright/test";

const API_PATHS = [
  "/api/market/evidence/summary",
  "/api/market/evidence/sources",
  "/api/market/evidence/instruments?page=1&page_size=10",
  "/api/market/evidence/runs?page=1&page_size=10",
] as const;

test.describe("WickHunter market evidence", () => {
  test("@critical enforces identity, renders source capabilities and exposes no trading path", async ({
    page,
  }) => {
    const anonymous = await page.request.get("/api/market/evidence/summary");
    expect(anonymous.status()).toBe(401);

    await page.goto("/market/evidence");
    await expect(page.getByRole("heading", { name: "Market Evidence" })).toBeVisible();
    await expect(page.getByTestId("wh01-blocker")).toContainText(
      "LIQUIDATION_ARCHIVE_NOT_BOUND",
    );

    await expect(page.getByTestId("source-binance-usdm")).toContainText("Binance USD-M");
    await expect(page.getByTestId("source-bybit-linear")).toContainText("Bybit Linear");
    await expect(page.getByTestId("source-okx-swap")).toContainText("OKX Swap");
    await expect(page.getByTestId("source-okx-swap")).toContainText(
      "OKX_CANDLE_EVIDENCE_NOT_CONFIGURED",
    );
    await expect(page.getByTestId("source-okx-swap")).toContainText("Candle evidence");
    await expect(page.getByTestId("source-okx-swap")).toContainText("niedostępne");

    await page.getByLabel("Źródło instrumentu").selectOption("binance-usdm");
    await page.getByLabel("Szukaj symbolu").fill("BTCUSDT");
    await expect(page.getByRole("cell", { name: "BTCUSDT", exact: true })).toHaveCount(1);
    await expect(page.getByRole("cell", { name: "bybit-linear", exact: true })).toHaveCount(0);

    await page.getByRole("button", { name: "Szczegóły" }).first().click();
    await expect(page.getByTestId("run-details")).toContainText(
      "wickhunter-production-market-evidence-20260729-v1-r1",
    );
    await expect(page.getByTestId("run-details")).toContainText("WH-01 BLOCKED");

    await expect(
      page.getByRole("button", { name: /trade|order|live trading|submit|execute/i }),
    ).toHaveCount(0);

    for (const path of API_PATHS) {
      const response = await page.request.get(path);
      expect(response.status(), path).toBe(200);
      const text = await response.text();
      expect(text).not.toContain("/volume1/");
      expect(text).not.toContain("/var/lib/");
      expect(text).not.toMatch(/api[_-]?key|secret|passphrase/i);
      expect(text.length).toBeLessThan(250_000);
    }
  });

  test("@regression supports pagination and rejects unbounded queries", async ({ page }) => {
    await page.goto("/market/evidence");
    const first = await page.request.get(
      "/api/market/evidence/instruments?page=1&page_size=2&sort=volume&direction=desc",
    );
    expect(first.status()).toBe(200);
    const payload = (await first.json()) as {
      items: Array<{ symbol: string }>;
      page_size: number;
      total: number;
      total_pages: number;
    };
    expect(payload.page_size).toBe(2);
    expect(payload.items).toHaveLength(2);
    expect(payload.total).toBe(8);
    expect(payload.total_pages).toBe(4);

    const invalid = await page.request.get(
      "/api/market/evidence/instruments?page=1&page_size=101",
    );
    expect(invalid.status()).toBe(422);
    const invalidPayload = (await invalid.json()) as { code?: string };
    expect(invalidPayload).toMatchObject({ code: "MARKET_EVIDENCE_QUERY_INVALID" });

    const invalidQuality = await page.request.get(
      "/api/market/evidence/instruments?quality=accepted",
    );
    expect(invalidQuality.status()).toBe(422);
  });

  test("@permissions denies cross-tenant identity", async ({ page }) => {
    const state = await page.request.post("/api/identity/fixture-state", {
      data: { state: "cross_tenant" },
    });
    expect(state.status()).toBe(200);
    const api = await page.request.get("/api/market/evidence/summary");
    expect(api.status()).toBe(403);
    const payload = (await api.json()) as { code?: string };
    expect(payload).toMatchObject({ code: "CROSS_TENANT_DENIED" });

    await page.goto("/market/evidence");
    await expect(page).toHaveURL(/\/denied\?reason=cross_tenant/u);
  });
});
