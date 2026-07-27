import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

test.describe("Liquid20 read-only portal", { tag: [tags.critical, tags.regression] }, () => {
  test("serves versioned read-only BFF contracts without caching", async ({ identity, request }) => {
    await identity.authenticateRequest();
    const healthResponse = await request.get("/api/market/liquidations/health");
    expect(healthResponse.status()).toBe(200);
    expect(healthResponse.headers()["cache-control"]).toContain("no-store");
    const health = await healthResponse.json();
    expect(health).toEqual(
      expect.objectContaining({
        schema_version: 1,
        contract: "portal-liquidations-health-v2",
        mode: "historical",
        run_state: "completed",
        acceptance_status: "failed",
        collector_heartbeat_at_ms: null,
        research_preview: true,
        trading_authorized: false,
      }),
    );
    expect(health.portal_checked_at_ms).toBe(health.refreshed_at_ms);
    expect(health.sources["okx-swap"]).toEqual(
      expect.objectContaining({ configured: false, connected: false }),
    );
    expect(JSON.stringify(health)).not.toMatch(/api[_-]?key|secret|token|password/i);

    const listResponse = await request.get(
      "/api/market/liquidations?source=binance-usdm&symbol=BTCUSDT&limit=20",
    );
    expect(listResponse.status()).toBe(200);
    expect(listResponse.headers()["cache-control"]).toContain("no-store");
    const list = await listResponse.json();
    expect(list.schema_version).toBe(1);
    expect(list.events).toHaveLength(1);
    expect(list.events[0]).toEqual(
      expect.objectContaining({
        source: "binance-usdm",
        symbol: "BTCUSDT",
        notional_usd: "4995",
      }),
    );
    expect(list.events[0]).not.toHaveProperty("raw_side");

    const summaryResponse = await request.get("/api/market/liquidations/summary?side=long");
    expect(summaryResponse.status()).toBe(200);
    expect(summaryResponse.headers()["cache-control"]).toContain("no-store");
    const summary = await summaryResponse.json();
    expect(summary.windows.find((window: { window: string }) => window.window === "24h")).toEqual(
      expect.objectContaining({ event_count: 3, notional_usd: "18235" }),
    );

    expect((await request.get("/api/market/liquidations?limit=201")).status()).toBe(422);
    expect((await request.get("/api/market/liquidations?symbol=../../secret")).status()).toBe(422);
    expect((await request.get("/api/market/liquidations?source=unknown")).status()).toBe(422);
  });

  test("renders truthful historical state, rankings and source health", async ({ liquidations, page }) => {
    await liquidations.open();
    await expect(page.getByText("Market Data · Research preview")).toBeVisible();
    await expect(page.getByText("HISTORYCZNE", { exact: true })).toBeVisible();
    await expect(page.getByText("ODRZUCONE", { exact: true })).toBeVisible();
    await expect(page.getByText("Ostatnie zdarzenie", { exact: true })).toBeVisible();
    await expect(page.getByText("Ostatni heartbeat collectora", { exact: true })).toBeVisible();
    await expect(page.getByText("Ostatnie sprawdzenie przez portal", { exact: true })).toBeVisible();
    await expect(page.getByText("Strumień likwidacji")).toBeVisible();
    await expect(page.getByText("Ranking symboli")).toBeVisible();
    await expect(page.getByRole("cell", { name: "SOLUSDT" })).toBeVisible();
    await expect(page.getByRole("cell", { name: "Binance" }).first()).toBeVisible();
    await expect(page.getByRole("region", { name: "Zdrowie źródeł" })).toContainText("OKX");
    await expect(page.getByRole("region", { name: "Zdrowie źródeł" })).toContainText("niewłączone");
    await expect(page.getByText(/approximately 1000 ms window/)).toBeVisible();
    await expect(page.getByText(/nie są deduplikowane/)).toBeVisible();

    await liquidations.filterBySource("binance-usdm");
    await expect(page.getByRole("cell", { name: "Binance" }).first()).toBeVisible();
    await expect(page.getByRole("cell", { name: "Bybit" })).toHaveCount(0);

    await liquidations.filterBySymbol("BTCUSDT");
    await expect(page.getByRole("cell", { name: "BTCUSDT" })).toHaveCount(1);
    await expect(page.getByRole("button", { name: /buy|sell|trade|order/i })).toHaveCount(0);
    await expect(page.getByText(/uprawnień do składania zleceń/i)).toBeVisible();
  });

  test("shows an explicit unavailable state when the read model fails", { tag: tags.resilience }, async ({ page }) => {
    await page.route("**/api/market/liquidations/health", async (route) => {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Deterministic E2E outage" }),
      });
    });
    await page.goto("/market/liquidations");
    await expect(page.getByRole("alert")).toContainText("Dane Liquid20 są niedostępne.");
    await expect(page.getByRole("alert")).toContainText("Deterministic E2E outage");
  });
});
