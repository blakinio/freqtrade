import { expect, test } from "@playwright/test";

test("renders responsive shell with explicit environment and full product navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByTestId("environment-badge")).toHaveText("TEST");
  await expect(page.getByRole("link", { name: "PNL & Performance" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Trade Analysis" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Runtime Health" })).toBeVisible();
  await page.getByRole("link", { name: "View Bots", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Bot fleet" })).toBeVisible();
  await expect(page.getByText("BTC AI Dry Run")).toBeVisible();
  await expect(page.getByText("RUNNING", { exact: true }).first()).toBeVisible();
});

test("renders wide desktop shell without collapsing primary navigation", async ({ page }) => {
  await page.setViewportSize({ width: 3440, height: 1440 });
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Profile & Security" })).toBeVisible();
});

test("opens immutable bot detail from the fleet", async ({ page }) => {
  await page.goto("/bots");
  await page.getByRole("link", { name: "Open", exact: true }).first().click();
  await expect(page.getByRole("heading", { name: "BTC AI Dry Run" })).toBeVisible();
  await expect(page.getByText("model-validated-2026-07", { exact: true })).toBeVisible();
  await expect(page.getByText("risk-default-v1", { exact: true })).toBeVisible();
});

test("renders AI intelligence surfaces from deterministic fixture read models", async ({ page }) => {
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

test("renders canonical operational read-model surfaces in fixture mode", async ({ page }) => {
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
  await expect(page.getByText("Raw runtime logs: unavailable")).toBeVisible();
});

test("renders integrated signal, strategy, notification and security surfaces", async ({ page }) => {
  await page.goto("/bots/signals");
  await expect(page.getByRole("heading", { name: "Signal Wizard" })).toBeVisible();
  await expect(page.getByText("Advisory evidence only")).toBeVisible();
  await expect(page.getByRole("combobox", { name: "Pair" })).toHaveValue("BTC/USDT");

  await page.goto("/operations/signal-logs");
  await expect(page.getByRole("heading", { name: "Signal Logs" })).toBeVisible();
  await expect(page.getByText("Deterministic fixture signal for browser acceptance only.")).toBeVisible();

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

test("records advisory signal through the same-origin BFF without execution authority", async ({ page }) => {
  await page.goto("/bots/signals");
  await page.getByRole("button", { name: "Record advisory signal" }).click();
  await expect(page.getByRole("status")).toContainText("No execution was triggered.");
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

test("submits manual intent through deterministic risk gate and fails closed at execution", async ({
  page,
}) => {
  await page.goto("/terminal");
  await expect(page.getByRole("heading", { name: "Risk-gated manual intent" })).toBeVisible();
  await page.getByRole("button", { name: "Submit trade intent" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Risk: APPROVED · Execution: BLOCKED · ORDER_SUBMISSION_NOT_IMPLEMENTED",
  );
});

test("terminal BFF rejects browser-supplied risk snapshot authority", async ({ request }) => {
  const response = await request.post("/api/terminal", {
    data: {
      bot_id: "bot-btc-dryrun-01",
      pair: "BTC/USDT",
      side: "BUY",
      amount: "0.01",
      snapshot: { runtime_health: "HEALTHY", daily_loss: "0" },
    },
  });
  expect(response.status()).toBe(422);
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
