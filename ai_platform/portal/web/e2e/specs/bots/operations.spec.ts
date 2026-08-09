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
    await expect(page.getByRole("heading", { name: "Command intent controls" })).toBeVisible();
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

  test("shows fail-closed managed mode authoring and separate desired/active truth", async ({ botDetail, page }) => {
    await botDetail.open();

    const mode = page.getByLabel("Managed mode");
    await expect(mode).toHaveValue("shadow");
    await expect(mode.locator('option[value="live_blocked"]')).toHaveAttribute("disabled", "");
    await mode.selectOption("paper");
    await expect(mode).toHaveValue("paper");
    await expect(
      page.getByText(/PAPER is accepted only when trusted server evidence authorizes it/),
    ).toBeVisible();

    const desired = page.locator("dt", { hasText: "Desired" }).locator("..");
    const active = page.locator("dt", { hasText: "Active" }).locator("..");
    await expect(desired).toContainText("SHADOW");
    await expect(active).toContainText("SHADOW");
  });

  test("creates a confirmed immutable revision through the same-origin BFF", async ({ botDetail, page }) => {
    await botDetail.open();
    await botDetail.createRevision("model-revision-e2e");
    await expect(page.getByRole("status")).toContainText("Immutable revision 2 created");
  });

  test("records lifecycle intent while runtime state remains independent", async ({ botDetail, page }) => {
    await botDetail.open();
    await botDetail.requestPause();
    const status = page.getByRole("status");
    await expect(status).toContainText(
      "accepted for generation fixture-generation:bot-btc-dryrun-01:1 (SHADOW)",
    );
    await expect(status).toContainText("Desired and observed runtime state remain unchanged");
  });

  test("lifecycle-intent BFF is deterministic and never claims execution", async ({ identity, request }) => {
    await identity.authenticateRequest();
    const payload = {
      bot_id: "bot-btc-dryrun-01",
      action: "PAUSE_NEW_ENTRIES",
      expected_config_revision: 1,
      expected_runtime_generation_id: "fixture-generation:bot-btc-dryrun-01:1",
      idempotency_key: "operations-lifecycle-intent-replay",
    };

    const first = await request.post("/api/bot-management/commands/lifecycle-intents", {
      headers: identity.csrfHeaders(),
      data: payload,
    });
    const replay = await request.post("/api/bot-management/commands/lifecycle-intents", {
      headers: identity.csrfHeaders(),
      data: payload,
    });

    expect(first.status()).toBe(202);
    expect(replay.status()).toBe(202);
    const firstBody = await first.json();
    const replayBody = await replay.json();
    expect(replayBody.command_id).toBe(firstBody.command_id);
    expect(replayBody.status).toBe("ACCEPTED");
    expect(replayBody.command_persisted).toBe(true);
    expect(replayBody.execution_submission_performed).toBe(false);
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
