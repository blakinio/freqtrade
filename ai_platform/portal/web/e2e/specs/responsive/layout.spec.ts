import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";
import { expectNoUnclippedHorizontalOverflow } from "../../support/quality";

test.describe("responsive layouts", { tag: [tags.responsive, tags.regression] }, () => {
  test("keeps primary navigation visible on wide desktop", async ({ appShell, page }) => {
    await page.setViewportSize({ width: 3440, height: 1440 });
    await appShell.open();
    await appShell.expectDashboard();
    await appShell.expectPrimaryNavigation();
    await expect(page.getByRole("link", { name: "Profile & Security" })).toBeVisible();
    await expectNoUnclippedHorizontalOverflow(page);
  });

  test("keeps Liquid20 usable on a narrow mobile viewport", async ({ liquidations, page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await liquidations.open();
    await expect(page.getByLabel("Źródło")).toBeVisible();
    await expect(page.getByText("Ranking symboli")).toBeVisible();
    await expectNoUnclippedHorizontalOverflow(page);
  });
});
