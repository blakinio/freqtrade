import { tags } from "./config/e2e.config";
import { expect, test } from "./fixtures/test.fixture";


test.describe(
  "Portal responsive closure shell",
  { tag: [tags.regression, tags.responsive] },
  () => {
    test("contains navigation and product surfaces at 390px", async ({ identity, page }) => {
      await identity.setState("authenticated");
      await page.setViewportSize({ width: 390, height: 844 });

      for (const [path, heading] of [
        ["/ai/signal-wizard", "Signal Wizard"],
        ["/bots/strategies", "Strategy Catalog"],
        ["/performance", "PNL & Performance"],
      ] as const) {
        await test.step(path, async () => {
          await page.goto(path);
          await expect(page.getByRole("heading", { name: heading })).toBeVisible();
          await expect(page.locator(".primary-nav")).toBeVisible();

          const dimensions = await page.evaluate(() => ({
            clientWidth: document.documentElement.clientWidth,
            scrollWidth: document.documentElement.scrollWidth,
            navigationClientWidth:
              document.querySelector<HTMLElement>(".primary-nav")?.clientWidth ?? 0,
          }));

          expect(dimensions.clientWidth).toBe(390);
          expect(dimensions.scrollWidth - dimensions.clientWidth).toBeLessThanOrEqual(1);
          expect(dimensions.navigationClientWidth).toBeLessThanOrEqual(
            dimensions.clientWidth,
          );
        });
      }
    });
  },
);
