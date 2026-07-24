import { expect, test } from "@playwright/test";


test("performance separates realized and authoritative unrealized evidence", async ({ page }) => {
  await page.goto("/performance");

  await expect(page.getByRole("heading", { name: "PNL & Performance" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Realized performance" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Open position valuation" })).toBeVisible();
  await expect(page.getByText("mark-to-entry-v1")).toBeVisible();
  await expect(page.getByText("fixture:runtime-bot-alpha:BTC-USDT")).toBeVisible();
});
