import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

test.describe("read-only critical flow stability", { tag: [tags.stability, tags.soak] }, () => {
  test("navigates dashboard, fleet, bot detail and Liquid20 without mutating state", async ({
    appShell,
    botFleet,
    liquidations,
    page,
  }) => {
    await appShell.open();
    await appShell.expectDashboard();
    await botFleet.open();
    await botFleet.openFirstBot();
    await expect(page.getByRole("heading", { name: "BTC AI Dry Run" })).toBeVisible();
    await liquidations.open();
    await expect(page.getByText("Market Data · Research preview")).toBeVisible();
  });
});
