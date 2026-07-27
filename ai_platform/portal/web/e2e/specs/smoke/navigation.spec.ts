import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

test.describe("portal shell", { tag: [tags.smoke, tags.critical, tags.crossBrowser] }, () => {
  test("renders explicit environment and primary product navigation", async ({ appShell, page }) => {
    await appShell.open();
    await appShell.expectDashboard();
    await appShell.expectPrimaryNavigation();

    await page.getByRole("link", { name: "View Bots", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Bot fleet" })).toBeVisible();
    await expect(page.getByText("BTC AI Dry Run")).toBeVisible();
    await expect(page.getByText("RUNNING", { exact: true }).first()).toBeVisible();
  });

  test("opens immutable bot detail from the fleet", async ({ botFleet, page }) => {
    await botFleet.open();
    await botFleet.openFirstBot();
    await expect(page.getByRole("heading", { name: "BTC AI Dry Run" })).toBeVisible();
    await expect(
      page.getByRole("definition").filter({ hasText: "model-validated-2026-07" }),
    ).toBeVisible();
    await expect(page.getByRole("definition").filter({ hasText: "risk-default-v1" })).toBeVisible();
  });
});
