import { canonicalBtcBotSpec, createUniqueBot } from "../../data/bot.factory";
import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

test.describe("dry-run bot creation", { tag: [tags.critical, tags.regression] }, () => {
  test("creates a canonical dry-run bot through the same-origin BFF", async ({ botJourney, page }, testInfo) => {
    const bot = createUniqueBot(testInfo);
    await botJourney.createDryRunBot(bot.botId, bot.name);
    await expect(page.getByRole("status")).toContainText(
      `Created ${bot.name} (${bot.botId}) in dry-run mode.`,
    );
  });

  test("rejects non-dry-run bot creation at the same-origin BFF", async ({ identity, request }) => {
    await identity.authenticateRequest();
    const response = await request.post("/api/bots", {
      headers: identity.csrfHeaders(),
      data: {
        bot_id: "bot-live-rejected",
        name: "Rejected Live Bot",
        spec: {
          ...canonicalBtcBotSpec,
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
});
