import { expect, test, type APIRequestContext } from "@playwright/test";

async function authenticateFixture(request: APIRequestContext) {
  const response = await request.post("/api/identity/fixture-state", {
    data: { state: "authenticated" },
  });
  expect(response.status()).toBe(200);
}

test("serves versioned read-only liquidation BFF contracts", async ({ request }) => {
  await authenticateFixture(request);
  const healthResponse = await request.get("/api/market/liquidations/health");
  expect(healthResponse.status()).toBe(200);
  expect(healthResponse.headers()["cache-control"]).toContain("no-store");
  const health = await healthResponse.json();
  expect(health).toEqual(
    expect.objectContaining({
      schema_version: 1,
      mode: "historical",
      acceptance_status: "failed",
      research_preview: true,
      trading_authorized: false,
    }),
  );
  expect(JSON.stringify(health)).not.toMatch(/api[_-]?key|secret|token|password/i);

  const listResponse = await request.get(
    "/api/market/liquidations?source=binance-usdm&symbol=BTCUSDT&limit=20",
  );
  expect(listResponse.status()).toBe(200);
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

  const summaryResponse = await request.get(
    "/api/market/liquidations/summary?side=long",
  );
  expect(summaryResponse.status()).toBe(200);
  const summary = await summaryResponse.json();
  expect(summary.windows.find((window: { window: string }) => window.window === "24h")).toEqual(
    expect.objectContaining({ event_count: 3, notional_usd: "18235" }),
  );

  expect((await request.get("/api/market/liquidations?limit=201")).status()).toBe(422);
  expect((await request.get("/api/market/liquidations?symbol=../../secret")).status()).toBe(422);
  expect((await request.get("/api/market/liquidations?source=unknown")).status()).toBe(422);
});

test("renders filters, truthful acceptance state, rankings and source semantics", async ({ page }) => {
  await page.goto("/market/liquidations");

  await expect(page.getByRole("heading", { name: "Likwidacje", exact: true })).toBeVisible();
  await expect(page.getByText("Market Data · Research preview")).toBeVisible();
  await expect(page.getByText("Acceptance failed.")).toBeVisible();
  await expect(
    page.getByText("binance-usdm.maximum_latency_over_threshold_ratio"),
  ).toBeVisible();
  await expect(page.getByText("Strumień likwidacji")).toBeVisible();
  await expect(page.getByText("Ranking symboli")).toBeVisible();
  await expect(page.getByRole("cell", { name: "SOLUSDT" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Binance" }).first()).toBeVisible();
  await expect(page.getByText(/approximately 1000 ms window/)).toBeVisible();
  await expect(page.getByText(/nie deduplikuje się/)).toBeVisible();

  const source = page.getByLabel("Źródło");
  await source.selectOption("binance-usdm");
  await expect(page.getByRole("cell", { name: "Binance" }).first()).toBeVisible();
  await expect(page.getByRole("cell", { name: "Bybit" })).toHaveCount(0);

  await page.getByLabel("Symbol").fill("BTCUSDT");
  await expect(page.getByRole("cell", { name: "BTCUSDT" })).toHaveCount(1);

  await expect(page.getByRole("button", { name: /buy|sell|trade|order/i })).toHaveCount(0);
  await expect(page.getByText(/autoryzuje handlu/i)).toBeVisible();
});

test("keeps the liquidation page usable on a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/market/liquidations");
  await expect(page.getByRole("heading", { name: "Likwidacje", exact: true })).toBeVisible();
  await expect(page.getByLabel("Źródło")).toBeVisible();
  await expect(page.getByText("Ranking symboli")).toBeVisible();

  const overflowSources = await page.evaluate(() => {
    const viewportWidth = window.innerWidth;
    return [...document.querySelectorAll<HTMLElement>("body *")]
      .map((element) => {
        const bounds = element.getBoundingClientRect();
        let parent = element.parentElement;
        let clipped = false;
        while (parent) {
          const overflowX = getComputedStyle(parent).overflowX;
          if (["auto", "scroll", "hidden", "clip"].includes(overflowX)) {
            clipped = true;
            break;
          }
          parent = parent.parentElement;
        }
        return {
          tag: element.tagName.toLowerCase(),
          className: element.className,
          right: Math.round(bounds.right),
          width: Math.round(bounds.width),
          clipped,
        };
      })
      .filter((item) => !item.clipped && item.right > viewportWidth + 1)
      .sort((left, right) => right.right - left.right)
      .slice(0, 5);
  });

  expect(overflowSources, `Unclipped mobile overflow: ${JSON.stringify(overflowSources)}`).toEqual(
    [],
  );
});
