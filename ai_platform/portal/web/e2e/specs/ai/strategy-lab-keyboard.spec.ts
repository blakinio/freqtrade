import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

const baselineExperimentId = "11111111-1111-5111-8111-111111111111";
const variantExperimentId = "22222222-2222-5222-8222-222222222222";

test.describe(
  "Strategy Lab experiment selection",
  { tag: [tags.accessibility, tags.regression, tags.critical] },
  () => {
    test("opens experiment detail with native keyboard activation", async ({ page }) => {
      await page.goto("/ai/experiments");
      await expect(page.getByRole("heading", { name: "Testy / Laboratorium" })).toBeVisible();

      const detail = page.getByTestId("experiment-detail");
      await expect(detail).toHaveAttribute("data-experiment-id", baselineExperimentId);

      const variantAction = page.getByRole("button", {
        name: `Otwórz eksperyment ${variantExperimentId}`,
      });
      await variantAction.focus();
      await expect(variantAction).toBeFocused();
      await page.keyboard.press("Enter");
      await expect(detail).toHaveAttribute("data-experiment-id", variantExperimentId);

      const baselineAction = page.getByRole("button", {
        name: `Otwórz eksperyment ${baselineExperimentId}`,
      });
      await baselineAction.click();
      await expect(detail).toHaveAttribute("data-experiment-id", baselineExperimentId);
    });
  },
);
