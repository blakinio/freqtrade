import { expect, test, type APIRequestContext } from "@playwright/test";

const fixtureCsrfToken = "fixture-csrf-token";

async function authenticateFixture(request: APIRequestContext) {
  const response = await request.post("/api/identity/fixture-state", {
    data: { state: "authenticated" },
  });
  expect(response.status()).toBe(200);
}

const btcSpec = {
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
  environment: "test",
  execution_mode: "dry_run",
};

test("renders bounded bot fleet operations and filters by market", async ({ page }) => {
  await page.goto("/bots");
  await expect(page.getByRole("heading", { name: "Bot fleet" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Positions" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "PNL" })).toBeVisible();

  const btcRow = page.getByRole("row").filter({ hasText: "BTC AI Dry Run" });
  await expect(btcRow.getByText("R 11.60 USDT", { exact: true })).toBeVisible();
  await expect(btcRow.getByText("NORMAL", { exact: true })).toBeVisible();

  const ethRow = page.getByRole("row").filter({ hasText: "ETH Validation Bot" });
  await expect(ethRow.getByText("1", { exact: true })).toBeVisible();
  await expect(ethRow.getByText("UNAVAILABLE", { exact: true })).toBeVisible();

  await page.getByLabel("Market").fill("ETH/USDT");
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(page.getByText("ETH Validation Bot")).toBeVisible();
  await expect(page.getByText("BTC AI Dry Run")).not.toBeVisible();
});

test("renders bot-scoped runtime, valuation, risk, audit and log evidence", async ({ page }) => {
  await page.goto("/bots/detail/bot-btc-dryrun-01");
  await expect(page.getByRole("heading", { name: "BTC AI Dry Run" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Desired-state controls" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Create immutable revision" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Source status" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Risk decisions" })).toBeVisible();
  await expect(page.getByText("RISK_APPROVED", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Audit events" })).toBeVisible();
  await expect(page.getByText("trade.manual_intent", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Runtime logs · last 24 hours" })).toBeVisible();
  await expect(
    page.getByText("Exchange request failed and remained operational evidence only."),
  ).toBeVisible();
});

test("creates a confirmed immutable revision through the same-origin BFF", async ({ page }) => {
  await page.goto("/bots/detail/bot-btc-dryrun-01");
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByLabel("Model version").fill("model-revision-e2e");
  await page.getByRole("button", { name: "Create revision 2" }).click();
  await expect(page.getByRole("status")).toContainText("Immutable revision 2 created");
});

test("requests lifecycle intent with confirmation and keeps execution authority separate", async ({
  page,
}) => {
  await page.goto("/bots/detail/bot-btc-dryrun-01");
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Pause" }).click();
  await expect(page.getByRole("status")).toContainText(
    "PAUSED requested. Observed state remains independent",
  );
});

test("lifecycle BFF is idempotent and rejects stale expected state", async ({ request }) => {
  await authenticateFixture(request);
  const idempotent = await request.post(
    "/api/bots/bot-btc-dryrun-01/desired-state",
    {
      headers: { "x-csrf-token": fixtureCsrfToken },
      data: { desired_state: "RUNNING", expected_current_state: "RUNNING" },
    },
  );
  expect(idempotent.status()).toBe(200);
  expect(idempotent.headers()["x-idempotent-replay"]).toBe("true");

  const stale = await request.post(
    "/api/bots/bot-btc-dryrun-01/desired-state",
    {
      headers: { "x-csrf-token": fixtureCsrfToken },
      data: { desired_state: "PAUSED", expected_current_state: "STOPPED" },
    },
  );
  expect(stale.status()).toBe(409);
  await expect(stale.json()).resolves.toMatchObject({
    detail: "Bot lifecycle state changed. Current desired state is RUNNING",
  });
});

test("revision BFF rejects stale and execution-mode-changing requests", async ({ request }) => {
  await authenticateFixture(request);
  const stale = await request.post(
    "/api/bots/bot-btc-dryrun-01/revisions",
    {
      headers: { "x-csrf-token": fixtureCsrfToken },
      data: { spec: { ...btcSpec, config_revision: 3 } },
    },
  );
  expect(stale.status()).toBe(409);

  const modeChange = await request.post(
    "/api/bots/bot-btc-dryrun-01/revisions",
    {
      headers: { "x-csrf-token": fixtureCsrfToken },
      data: { spec: { ...btcSpec, config_revision: 2, execution_mode: "simulated" } },
    },
  );
  expect(modeChange.status()).toBe(422);
  await expect(modeChange.json()).resolves.toMatchObject({
    detail: "Revision cannot change the bot environment or execution mode",
  });
});
