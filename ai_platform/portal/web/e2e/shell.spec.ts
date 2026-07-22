import { expect, test } from "@playwright/test";

test("renders responsive shell with explicit environment and bot navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByTestId("environment-badge")).toHaveText("TEST");
  await page.getByRole("link", { name: "Bots", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Bot fleet" })).toBeVisible();
  await expect(page.getByText("BTC AI Dry Run")).toBeVisible();
  await expect(page.getByText("RUNNING", { exact: true }).first()).toBeVisible();
});

test("creates a canonical dry-run bot through the same-origin BFF", async ({ page }) => {
  await page.goto("/bots/new");
  await expect(page.getByRole("heading", { name: "Create Bot" })).toBeVisible();
  await page.getByLabel("Bot ID").fill("bot-e2e-01");
  await page.getByLabel("Name").fill("E2E Dry Run Bot");
  await page.getByRole("button", { name: "Create dry-run bot" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Created E2E Dry Run Bot (bot-e2e-01) in dry-run mode.",
  );
});

test("renders an intentional authorization denied state", async ({ page }) => {
  await page.goto("/denied");
  await expect(
    page.getByRole("heading", { name: "You do not have permission to view this resource" }),
  ).toBeVisible();
  await expect(
    page.getByText("Navigation visibility is not an authorization boundary."),
  ).toBeVisible();
});

test("rejects non-dry-run bot creation at the same-origin BFF", async ({ request }) => {
  const response = await request.post("/api/bots", {
    data: {
      bot_id: "bot-live-rejected",
      name: "Rejected Live Bot",
      spec: {
        tenant_id: "tenant-demo",
        strategy_version: "ai-directional-v1",
        model_version: "model-validated-2026-07",
        risk_policy_version: "risk-default-v1",
        exchange_connection_ref: "exchange-simulated-kraken",
        pair_universe: ["BTC/USDT"],
        timeframe: "5m",
        capital_allocation: "1000",
        capital_currency: "USDT",
        runtime_version: "freqtrade-2026.7",
        config_revision: 1,
        environment: "production",
        execution_mode: "simulated",
      },
    },
  });
  expect(response.status()).toBe(422);
  await expect(response.json()).resolves.toMatchObject({
    detail: "Request must match the canonical P2 dry-run bot contract",
  });
});
