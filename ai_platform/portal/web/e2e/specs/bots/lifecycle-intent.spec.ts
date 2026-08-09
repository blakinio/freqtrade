import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";


test.describe("BMW-02 lifecycle command intents", { tag: [tags.critical, tags.security] }, () => {
  test("records an accepted command intent without claiming runtime execution", async ({ page }) => {
    await page.goto("/bots/detail/bot-btc-dryrun-01");
    await expect(page.getByRole("heading", { name: "BTC AI Dry Run" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Command intent controls" })).toBeVisible();

    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Pause" }).click();

    const status = page.getByRole("status");
    await expect(status).toContainText("Command intent");
    await expect(status).toContainText(
      "accepted for generation fixture-generation:bot-btc-dryrun-01:1 (SHADOW)",
    );
    await expect(status).toContainText("Desired and observed runtime state remain unchanged");
    await expect(page.getByText(/never calls a runtime or exchange endpoint/i)).toBeVisible();
  });

  test("same-origin BFF rejects browser-supplied runtime authority", async ({ identity, request }) => {
    await identity.authenticateRequest();
    const response = await request.post("/api/bot-management/commands/lifecycle-intents", {
      headers: identity.csrfHeaders(),
      data: {
        bot_id: "bot-btc-dryrun-01",
        action: "PAUSE_NEW_ENTRIES",
        expected_config_revision: 1,
        expected_runtime_generation_id: "fixture-generation:bot-btc-dryrun-01:1",
        idempotency_key: "browser-authority-rejected",
        runtime_id: "browser-runtime",
        runtime_revision: 99,
        environment: "production",
      },
    });

    expect(response.status()).toBe(422);
    await expect(response.json()).resolves.toMatchObject({
      detail: "Invalid lifecycle command intent request",
    });
  });
});
