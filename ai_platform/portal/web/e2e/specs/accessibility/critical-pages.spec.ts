import { tags } from "../../config/e2e.config";
import { test } from "../../fixtures/test.fixture";
import { expectBaselineAccessibility } from "../../support/quality";

const criticalPages = [
  ["dashboard", "/"],
  ["bot fleet", "/bots"],
  ["terminal", "/terminal"],
  ["liquidations", "/market/liquidations"],
  ["administration", "/platform/admin"],
] as const;

test.describe("baseline accessibility", { tag: [tags.accessibility, tags.regression] }, () => {
  for (const [name, path] of criticalPages) {
    test(`${name} has labelled controls and core landmarks`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      await expectBaselineAccessibility(page);
    });
  }
});
