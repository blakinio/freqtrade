import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

test.describe("AI intelligence read models", { tag: [tags.regression, tags.crossBrowser] }, () => {
  test("renders deterministic AI evidence without promotion authority", async ({ page }) => {
    await page.goto("/ai");
    await expect(page.getByRole("heading", { name: "AI Overview" })).toBeVisible();
    await expect(page.getByText("model-validated-2026-07", { exact: true }).first()).toBeVisible();

    await page.goto("/ai/trade-analysis");
    await expect(page.getByRole("heading", { name: "Trade Analysis" })).toBeVisible();
    await expect(page.getByText("trade-fixture-1", { exact: true })).toBeVisible();

    await page.goto("/ai/learning");
    await expect(page.getByRole("heading", { name: "Learning History" })).toBeVisible();
    await expect(page.getByText(/Validate whether the observed BTC setup/)).toBeVisible();

    await page.goto("/ai/model-health");
    await expect(page.getByRole("heading", { name: "Model Health" })).toBeVisible();
    await expect(page.getByText("HEALTHY", { exact: true })).toBeVisible();
    await expect(page.getByText("PSI_V1_WITHIN_LIMITS")).toBeVisible();
    await expect(page.getByText("psi-v1", { exact: true })).toBeVisible();
  });
});
