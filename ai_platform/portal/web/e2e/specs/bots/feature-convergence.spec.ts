import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";


test.describe("BMW-03 safe feature convergence", { tag: [tags.critical, tags.security] }, () => {
  test("renders secret-free exchange metadata", async ({ page }) => {
    await page.goto("/platform/exchanges");

    await expect(page.getByRole("heading", { name: "Exchange Connections" })).toBeVisible();
    await expect(page.getByText("Simulated dry-run")).toBeVisible();
    await expect(page.getByText("Not exposed", { exact: true })).toBeVisible();
    const body = (await page.locator("body").innerText()).toLowerCase();
    expect(body).not.toContain("credref_");
    expect(body).not.toContain("api key");
    expect(body).not.toContain("passphrase");
    expect(body).not.toContain("secret-store");
  });

  test("blocks signed signal acceptance without PI-07", async ({ page }) => {
    await page.goto("/bots/signals");

    await expect(page.getByRole("heading", { name: "Signal Control" })).toBeVisible();
    await expect(page.getByText("Authentication provider: UNAVAILABLE")).toBeVisible();
    await expect(page.getByText(/Accepted processing: blocked/)).toBeVisible();
    await expect(page.getByText(/Execution submission: no/)).toBeVisible();
    const body = (await page.locator("body").innerText()).toLowerCase();
    expect(body).not.toContain("signalref_");
    expect(body).not.toContain("endpoint_slug");
  });

  test("blocks grid preview without trusted server evidence", async ({ page }) => {
    await page.goto("/bots/grid");

    await expect(page.getByRole("heading", { name: "Grid Control" })).toBeVisible();
    await expect(page.getByText("Capability evidence provider: UNAVAILABLE")).toBeVisible();
    await expect(page.getByText("Not accepted", { exact: true })).toBeVisible();
    await expect(page.getByText("Not submitted", { exact: true })).toBeVisible();
    await expect(page.getByText(/Trusted grid evidence is not configured/)).toBeVisible();
  });
});
