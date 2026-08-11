import { tags } from "./config/e2e.config";
import { expect, test } from "./fixtures/test.fixture";


test.describe(
  "PAPER G0 product surface availability truth",
  { tag: [tags.regression] },
  () => {
    test("marks a disconnected capability unavailable in navigation and direct view", async ({
      identity,
      page,
    }) => {
      await identity.setState("authenticated");
      await page.goto("/ai");

      await expect(
        page.getByRole("link", { name: "AI Overview · Unavailable" }),
      ).toBeVisible();
      const notice = page.locator('[data-surface-availability="DISCONNECTED"]');
      await expect(notice).toBeVisible();
      await expect(notice).toContainText("AI Overview capability unavailable");
      await expect(notice).toContainText(
        "not connected end to end in the canonical product runtime",
      );
      await expect(notice).toContainText("#1098, #1102");
    });

    test("does not label a non-disconnected capability unavailable", async ({
      identity,
      page,
    }) => {
      await identity.setState("authenticated");
      await page.goto("/market/liquidations");

      await expect(page.getByRole("link", { name: "Likwidacje", exact: true })).toBeVisible();
      await expect(page.locator("[data-surface-availability]")).toHaveCount(0);
    });
  },
);
