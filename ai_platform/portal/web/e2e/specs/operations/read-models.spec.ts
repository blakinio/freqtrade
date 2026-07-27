import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

test.describe("operational read models", { tag: [tags.regression, tags.crossBrowser] }, () => {
  test("renders canonical portfolio and execution evidence", async ({ page }) => {
    await page.goto("/performance");
    await expect(page.getByRole("heading", { name: "PNL & Performance" })).toBeVisible();
    await expect(page.getByText("11.60", { exact: true })).toBeVisible();

    await page.goto("/positions");
    await expect(page.getByRole("heading", { name: "Open Positions" })).toBeVisible();
    await expect(page.getByText("ETH/USDT", { exact: true })).toBeVisible();

    await page.goto("/orders");
    await expect(page.getByRole("heading", { name: "Orders" })).toBeVisible();
    await expect(page.getByText("fixture-order-1", { exact: true })).toBeVisible();

    await page.goto("/trades");
    await expect(page.getByRole("heading", { name: "Trade History" })).toBeVisible();
    await expect(page.getByText("trade-fixture-1", { exact: true })).toBeVisible();

    await page.goto("/operations/risk-events");
    await expect(page.getByRole("heading", { name: "Risk Events" })).toBeVisible();
    await expect(page.getByText("RISK_APPROVED", { exact: true })).toBeVisible();

    await page.goto("/operations/audit");
    await expect(page.getByRole("heading", { name: "Audit Events" })).toBeVisible();
    await expect(page.getByText("bot.created", { exact: true })).toBeVisible();

    await page.goto("/operations/execution-logs");
    await expect(page.getByRole("heading", { name: "Execution Activity" })).toBeVisible();
    await expect(page.getByText("trade.manual_intent", { exact: true })).toBeVisible();
    await expect(page.getByText("Raw runtime logs: available")).toBeVisible();
    await expect(
      page.getByText("Exchange request failed and remained operational evidence only."),
    ).toBeVisible();
    await expect(page.getByRole("heading", { name: "Execution audit activity" })).toBeVisible();
  });
});
