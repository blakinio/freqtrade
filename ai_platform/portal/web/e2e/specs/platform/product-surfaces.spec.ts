import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

test.describe("integrated product surfaces", { tag: [tags.regression, tags.crossBrowser] }, () => {
  test("renders signal, strategy, notification and security surfaces", async ({ page }) => {
    await page.goto("/bots/signals");
    await expect(page.getByRole("heading", { name: "Signal Wizard" })).toBeVisible();
    await expect(page.getByText("Advisory evidence only")).toBeVisible();
    await expect(page.getByRole("combobox", { name: "Pair" })).toHaveValue("BTC/USDT");

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
    await expect(page.getByRole("heading", { name: "Grid Bots" })).toBeVisible();
    await expect(page.getByText("grid-dry-run-v1", { exact: true }).first()).toBeVisible();

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

  test("records advisory signal without execution authority", async ({ page }) => {
    await page.goto("/bots/signals");
    await page.getByRole("button", { name: "Record advisory signal" }).click();
    await expect(page.getByRole("status")).toContainText("No execution was triggered.");
  });
});
