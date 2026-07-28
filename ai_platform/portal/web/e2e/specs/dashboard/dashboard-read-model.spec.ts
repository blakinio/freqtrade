import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

test.describe("BM-08 dashboard read model", { tag: [tags.critical, tags.regression] }, () => {
  test("renders explicit fixture evidence without claiming provider health", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByText("Active bots")).toBeVisible();
    await expect(page.getByText("Runtime evidence")).toBeVisible();
    await expect(page.getByText("PARTIAL", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Risk evidence")).toBeVisible();
    await expect(page.getByText("UNAVAILABLE", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Bot evidence" })).toBeVisible();
    await expect(page.getByText(/runtime PARTIAL/).first()).toBeVisible();
    await expect(page.getByText(/Live control-plane snapshot/)).toHaveCount(0);
  });
});
