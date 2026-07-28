import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";


test.describe("catalog-driven bot configuration", { tag: [tags.critical, tags.regression] }, () => {
  test("finalizes an immutable dry-run configuration without runtime submission", async ({ page }) => {
    await page.goto("/bots/new");

    await expect(page.getByRole("heading", { name: "Create Bot Configuration" })).toBeVisible();
    await expect(page.getByLabel("Template")).toHaveValue("ai-directional-dry-run");
    await expect(page.getByLabel("Strategy")).toHaveValue("ai-directional-v1");
    await expect(page.getByLabel("Model")).toHaveValue("model-validated-2026-07");
    await expect(page.getByLabel("Runtime")).toHaveValue("freqtrade-2026.7");
    await expect(page.getByLabel("Risk policy")).toHaveValue("risk-default-v1");
    await expect(page.getByText("Configuration finalization only")).toBeVisible();

    await page.getByLabel("Bot ID").fill("bot-e2e-catalog-01");
    await page.getByRole("button", { name: "Finalize dry-run configuration" }).click();

    await expect(page.getByRole("status")).toContainText("revision 1");
    await expect(page.getByRole("status")).toContainText("Runtime submitted: no");
  });

  test("does not render browser-editable internal version fields", async ({ page }) => {
    await page.goto("/bots/new");

    await expect(page.getByLabel("Strategy")).toHaveJSProperty("tagName", "SELECT");
    await expect(page.getByLabel("Model")).toHaveJSProperty("tagName", "SELECT");
    await expect(page.getByLabel("Runtime")).toHaveJSProperty("tagName", "SELECT");
    await expect(page.getByLabel("Risk policy")).toHaveJSProperty("tagName", "SELECT");
    await expect(page.getByText(/does not start Freqtrade or submit an order/i)).toBeVisible();
  });

  test("rejects a non-dry-run builder payload at the same-origin BFF", async ({ identity, request }) => {
    await identity.authenticateRequest();
    const response = await request.post("/api/bot-management/builder", {
      headers: identity.csrfHeaders(),
      data: {
        draft_id: "draft-live-rejected",
        bot_id: "bot-live-rejected",
        payload: {
          execution_mode: "simulated",
          runtime_policy: { execution_mode: "simulated" },
        },
      },
    });

    expect(response.status()).toBe(422);
    await expect(response.json()).resolves.toMatchObject({
      detail: "Request must match the canonical dry-run bot builder contract",
    });
  });
});
