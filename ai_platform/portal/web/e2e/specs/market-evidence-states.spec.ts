import { expect, test, type Page, type Route } from "@playwright/test";

const authority = {
  execution_enabled: false,
  orders_submitted: 0,
  trading_credentials_present: false,
  model_execution_authorized: false,
  replay_authorized: false,
  performance_research_authorized: false,
  live_capital_authorized: false,
} as const;

const unavailableSummary = {
  schema_version: 1,
  status: "UNAVAILABLE",
  updated_at_ms: 1785391200000,
  active_run_id: null,
  latest_immutable_run_id: null,
  capture_start_ms: null,
  capture_end_ms: null,
  pre_roll_ms: null,
  completeness: 0,
  instrument_count: 0,
  completed_candle_count: 0,
  market_quality_observation_count: 0,
  gap_count: 0,
  gap_duration_ms: 0,
  wh01: {
    ready: false,
    market_evidence_ready: false,
    blocker_code: "MARKET_EVIDENCE_UNAVAILABLE",
    blocker_detail: "No verified immutable market-evidence run is available.",
  },
  identities: {
    request_sha256: null,
    policy_sha256: null,
    code_sha: null,
    manifest_sha256: null,
  },
  authority,
} as const;

async function fulfillJson(route: Route, value: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(value),
  });
}

async function routeEmptyEvidence(page: Page, status = "UNAVAILABLE"): Promise<void> {
  await page.route("**/api/market/evidence/summary", async (route) => {
    await fulfillJson(route, { ...unavailableSummary, status });
  });
  await page.route("**/api/market/evidence/sources", async (route) => {
    await fulfillJson(route, [
      {
        source: "binance-usdm",
        display_name: "Binance USD-M",
        connected: false,
        healthy: false,
        last_event_at_ms: null,
        last_ticker_at_ms: null,
        last_completed_candle_at_ms: null,
        freshness_ms: null,
        active_symbols: 0,
        errors: [],
        reconnect_count: 0,
        gaps: 0,
        records_written: 0,
        required_scope: "completed 5m candles",
        liquidation_feed: "unknown",
        candle_evidence: "unavailable",
        market_quality_evidence: "unavailable",
        instrument_history: "unavailable",
        wickhunter_available: false,
        exclusion_reason: "MARKET_EVIDENCE_UNAVAILABLE",
      },
      {
        source: "bybit-linear",
        display_name: "Bybit Linear",
        connected: false,
        healthy: false,
        last_event_at_ms: null,
        last_ticker_at_ms: null,
        last_completed_candle_at_ms: null,
        freshness_ms: null,
        active_symbols: 0,
        errors: [],
        reconnect_count: 0,
        gaps: 0,
        records_written: 0,
        required_scope: "completed 5m candles",
        liquidation_feed: "unknown",
        candle_evidence: "unavailable",
        market_quality_evidence: "unavailable",
        instrument_history: "unavailable",
        wickhunter_available: false,
        exclusion_reason: "MARKET_EVIDENCE_UNAVAILABLE",
      },
      {
        source: "okx-swap",
        display_name: "OKX Swap",
        connected: true,
        healthy: true,
        last_event_at_ms: 1785391200000,
        last_ticker_at_ms: null,
        last_completed_candle_at_ms: null,
        freshness_ms: null,
        active_symbols: 0,
        errors: [],
        reconnect_count: 1,
        gaps: 0,
        records_written: 10,
        required_scope: "liquidation feed only",
        liquidation_feed: "available",
        candle_evidence: "unavailable",
        market_quality_evidence: "unavailable",
        instrument_history: "unavailable",
        wickhunter_available: false,
        exclusion_reason: "OKX_CANDLE_EVIDENCE_NOT_CONFIGURED",
      },
    ]);
  });
  await page.route("**/api/market/evidence/instruments**", async (route) => {
    await fulfillJson(route, {
      schema_version: 1,
      items: [],
      page: 1,
      page_size: 10,
      total: 0,
      total_pages: 0,
    });
  });
  await page.route("**/api/market/evidence/runs**", async (route) => {
    await fulfillJson(route, {
      schema_version: 1,
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
    });
  });
}

test.describe("Market evidence dashboard states", () => {
  test("@component renders loading before the read model resolves", async ({ page }) => {
    let release!: () => void;
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    await page.route("**/api/market/evidence/**", async (route) => {
      await gate;
      await fulfillJson(route, unavailableSummary);
    });
    await page.goto("/market/evidence");
    await expect(page.getByText("Ładowanie danych WickHunter Market Evidence…")).toBeVisible();
    release();
  });

  test("@component renders unavailable and empty states without invented rows", async ({ page }) => {
    await routeEmptyEvidence(page);
    await page.goto("/market/evidence");
    await expect(page.getByText("UNAVAILABLE", { exact: true })).toBeVisible();
    await expect(page.getByText("Brak instrumentów dla wybranych filtrów.")).toBeVisible();
    await expect(page.getByText("Brak runów market evidence.")).toBeVisible();
    await expect(page.getByTestId("source-okx-swap")).toContainText("Liquidation feed");
    await expect(page.getByTestId("source-okx-swap")).toContainText("dostępne");
    await expect(page.getByTestId("source-okx-swap")).toContainText("Candle evidence");
    await expect(page.getByTestId("source-okx-swap")).toContainText("niedostępne");
  });

  test("@component renders stale state and exact blocker", async ({ page }) => {
    await routeEmptyEvidence(page, "STALE");
    await page.goto("/market/evidence");
    await expect(page.getByText("STALE", { exact: true })).toBeVisible();
    await expect(page.getByText("Source stale", { exact: true })).toBeVisible();
    await expect(page.getByTestId("wh01-blocker")).toContainText(
      "MARKET_EVIDENCE_UNAVAILABLE",
    );
  });

  test("@component renders bounded API error state", async ({ page }) => {
    await page.route("**/api/market/evidence/**", async (route) => {
      await fulfillJson(
        route,
        { detail: "WickHunter market evidence is currently unavailable" },
        503,
      );
    });
    await page.goto("/market/evidence");
    await expect(page.getByRole("alert")).toContainText("Market evidence jest niedostępne.");
    await expect(page.getByRole("alert")).toContainText(
      "WickHunter market evidence is currently unavailable",
    );
  });
});
