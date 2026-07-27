import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

const validIntent = {
  bot_id: "bot-btc-dryrun-01",
  pair: "BTC/USDT",
  side: "BUY",
  amount: "0.01",
};

test.describe("risk-gated terminal", { tag: [tags.critical, tags.security, tags.regression] }, () => {
  test("approves deterministic risk but fails closed at execution", async ({ botJourney, page }) => {
    await botJourney.submitManualIntent();
    await expect(page.getByRole("status")).toContainText(
      "Risk: APPROVED · Execution: BLOCKED · ORDER_SUBMISSION_NOT_IMPLEMENTED",
    );
  });

  test("rejects browser-supplied risk snapshot authority", async ({ identity, request }) => {
    await identity.authenticateRequest();
    const response = await request.post("/api/terminal", {
      headers: identity.csrfHeaders(),
      data: {
        ...validIntent,
        snapshot: { runtime_health: "HEALTHY", daily_loss: "0" },
      },
    });
    expect(response.status()).toBe(422);
  });
});
