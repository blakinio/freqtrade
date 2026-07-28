import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

test.describe("integrated product surfaces", { tag: [tags.regression, tags.crossBrowser] }, () => {
  test("renders signal, strategy, notification and security surfaces", async ({ page }) => {
    await page.goto("/bots/signals");
    await expect(page.getByRole("heading", { name: "Signal Control" })).toBeVisible();
    await expect(page.getByText("Authentication provider: UNAVAILABLE")).toBeVisible();
    await expect(page.getByText(/Accepted processing: blocked/)).toBeVisible();

    await page.goto("/operations/signal-logs");
    await expect(page.getByRole("heading", { name: "Signal Logs" })).toBeVisible();
    await expect(
      page.getByText("Deterministic fixture signal for browser acceptance only."),
    ).toBeVisible();

    await page.goto("/bots/strategies");
    await expect(page.getByRole("heading", { name: "Strategy Catalog" })).toBeVisible();
    await expect(page.getByText("AI Directional", { exact: true })).toBeVisible();
    await expect(page.getByText("Grid Dry Run", { exact: true })).toBeVisible();

    await page.goto("/bots/grid");
    await expect(page.getByRole("heading", { name: "Grid Control" })).toBeVisible();
    await expect(page.getByText("Capability evidence provider: UNAVAILABLE")).toBeVisible();
    await expect(page.getByText("Not accepted", { exact: true })).toBeVisible();

    await page.goto("/platform/notifications");
    await expect(page.getByRole("heading", { name: "Notifications", exact: true })).toBeVisible();
    await expect(page.getByText(/BUY signal recorded for BTC\/USDT/)).toBeVisible();

    await page.goto("/platform/profile");
    await expect(page.getByRole("heading", { name: "Profile & Security" })).toBeVisible();
    await expect(page.getByText("Identity-provider boundary")).toBeVisible();

    await page.goto("/platform/admin");
    await expect(page.getByRole("heading", { name: "Administration" })).toBeVisible();
    await expect(page.getByText("Built-in RBAC")).toBeVisible();
  });

  test("does not expose unsigned advisory signal mutation", async ({ page }) => {
    await page.goto("/bots/signals");
    await expect(page.getByText(/Accepted processing: blocked/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Record advisory signal" })).toHaveCount(0);
    await expect(page.getByText(/Execution submission: no/)).toBeVisible();
  });
});
