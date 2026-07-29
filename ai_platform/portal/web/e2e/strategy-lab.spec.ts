import { expect, test } from "@playwright/test";

test("@critical Strategy Lab runs a deterministic fixture experiment and shows evidence", async ({ page }) => {
  await page.goto("/ai/experiments");
  await expect(page.getByRole("heading", { name: "Testy / Laboratorium" })).toBeVisible();
  await page.getByLabel("Strategia").selectOption("tv_supertrend_v1");
  await expect(page.getByTestId("strategy-parameters")).toContainText("atr_period");
  await page.getByRole("button", { name: "Uruchom test" }).click();
  await expect(page.getByTestId("experiment-detail")).toContainText("Win rate");
  await expect(page.getByTestId("signal-chart")).toContainText("ENTRY");
  await expect(page.getByRole("heading", { name: "Uzasadnienie sygnałów" })).toBeVisible();
  await expect(page.getByTestId("strategy-comparison")).toContainText("Zmiany parametrów");
});
