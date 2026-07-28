import { canonicalBtcBotSpec } from "../../data/bot.factory";
import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";


test.describe("bot operations", { tag: [tags.critical, tags.regression] }, () => {
  test("renders bounded fleet operations and filters by market", async ({ botFleet, page }) => {
    await botFleet.open();
    await expect(page.getByRole("columnheader", { name: "Positions" })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: "PNL" })).toBeVisible();

    const btcRow = page.getByRole("row").filter({ hasText: "BTC AI Dry Run" });
    await expect(btcRow.getByText("R 11.60 USDT", { exact: true })).toBeVisible();
    await expect(btcRow.getByText("NORMAL", { exact: true })).toBeVisible();

    const ethRow = page.getByRole("row").filter({ hasText: "ETH Validation Bot" });
    await expect(ethRow.getByText("1", { exact: true })).toBeVisible();
    await expect(ethRow.getByText("UNAVAILABLE", { exact: true })).toBeVisible();

    await botFleet.filterByMarket("ETH/USDT");
    await expect(page.getByText("ETH Validation Bot")).toBeVisible();
    await expect(page.getByText("BTC AI Dry Run")).not.toBeVisible();
  });

  test("renders bot-scoped runtime, valuation, risk, audit and logs", async ({ botDetail, page }) => {
    await botDetail.open();
    await expect(page.getByRole("heading", { name: "Audited command intents" })).toBeVisible();
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

  test("creates a confirmed immutable revision through the same-origin BFF", async ({ botDetail, page }) => {
    await botDetail.open();
    await botDetail.createRevision("model-revision-e2e");
    await expect(page.getByRole("status")).toContainText("Immutable revision 2 created");
  });

  test("persists lifecycle intent without claiming runtime execution", async ({ botDetail, page }) => {
    await botDetail.open();
    await botDetail.requestPauseIntent();
    await expect(page.getByRole("status")).toContainText("ACCEPTED");
    await expect(page.getByRole("status")).toContainText("Command persisted: yes");
    await expect(page.getByRole("status")).toContainText("Execution submitted: no");
  });

  test("lifecycle BFF rejects browser-supplied runtime authority", async ({ identity, request }) => {
    await identity.authenticateRequest();
    const response = await request.post("/api/bot-management/commands/lifecycle", {
      headers: identity.csrfHeaders(),
      data: {
        bot_id: "bot-btc-dryrun-01",
        action: "PAUSE_NEW_ENTRIES",
        expected_config_revision: 1,
        idempotency_key: "browser-runtime-injection",
        runtime_id: "browser-controlled-runtime",
      },
    });

    expect(response.status()).toBe(422);
    await expect(response.json()).resolves.toMatchObject({
      detail: "Invalid lifecycle command intent request",
    });
  });

  test("lifecycle BFF returns intent evidence, never execution success", async ({ identity, request }) => {
    await identity.authenticateRequest();
    const response = await request.post("/api/bot-management/commands/lifecycle", {
      headers: identity.csrfHeaders(),
      data: {
        bot_id: "bot-btc-dryrun-01",
        action: "PAUSE_NEW_ENTRIES",
        expected_config_revision: 1,
        idempotency_key: "e2e-lifecycle-intent",
      },
    });

    expect(response.status()).toBe(202);
    await expect(response.json()).resolves.toMatchObject({
      status: "ACCEPTED",
      command_persisted: true,
      execution_submission_performed: false,
    });
  });

  test("revision BFF rejects stale and execution-mode-changing requests", async ({ identity, request }) => {
    await identity.authenticateRequest();
    const stale = await request.post("/api/bots/bot-btc-dryrun-01/revisions", {
      headers: identity.csrfHeaders(),
      data: { spec: { ...canonicalBtcBotSpec, config_revision: 3 } },
    });
    expect(stale.status()).toBe(409);

    const modeChange = await request.post("/api/bots/bot-btc-dryrun-01/revisions", {
      headers: identity.csrfHeaders(),
      data: { spec: { ...canonicalBtcBotSpec, config_revision: 2, execution_mode: "simulated" } },
    });
    expect(modeChange.status()).toBe(422);
    await expect(modeChange.json()).resolves.toMatchObject({
      detail: "Revision cannot change the bot environment or execution mode",
    });
  });
});
