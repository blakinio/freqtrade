import { tags } from "./config/e2e.config";
import { expect, test } from "./fixtures/test.fixture";


test.describe("Signal Wizard closure", { tag: [tags.regression, tags.responsive] }, () => {
  test(
    "builds an approved closed-bar preview and submits a research experiment candidate",
    { tag: [tags.critical] },
    async ({ page }) => {
      await page.goto("/ai/signal-wizard");

      await expect(page.getByRole("heading", { name: "Signal Wizard" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Approved Feature Registry selection" })).toBeVisible();
      await expect(page.getByLabel("Use atr.v1")).toBeChecked();
      await expect(page.getByText("Live authority")).toBeVisible();

      await page.getByLabel("Use rsi.v1").check();
      await page.getByLabel("rsi.v1 period").fill("21");
      await page.getByLabel("Condition feature").selectOption("rsi.v1");
      await page.getByLabel("Condition operator").selectOption("lt");
      await page.getByLabel("Condition value").fill("35");
      await page.getByRole("button", { name: "Generate canonical preview" }).click();

      await expect(page.getByRole("heading", { name: "Strategy preview" })).toBeVisible();
      await expect(page.getByText("SIGNAL_WIZARD_PREVIEW_VALIDATED")).toBeVisible();
      await expect(page.getByText("Execution authority").last()).toBeVisible();

      await page.getByLabel("Experiment name").fill("RSI closed-bar research candidate");
      await page.getByRole("button", { name: "Submit research experiment candidate" }).click();

      await expect(page.getByText("Experiment candidate accepted")).toBeVisible();
      await expect(page.getByText("SIGNAL_WIZARD_CANDIDATE_PERSISTED")).toBeVisible();
      await expect(page.getByText(/Execution authority: no/)).toBeVisible();
    },
  );

  test("renders stale, empty and fail-closed registry states", async ({ page }) => {
    await page.goto("/ai/signal-wizard?wizard_view=stale");
    await expect(page.getByText("Feature Registry snapshot is stale")).toBeVisible();
    await expect(page.getByText(/FEATURE_REGISTRY_SNAPSHOT_STALE/)).toBeVisible();

    await page.goto("/ai/signal-wizard?wizard_view=empty");
    await expect(page.getByText("No approved AI features are available")).toBeVisible();

    await page.goto("/ai/signal-wizard?wizard_view=failure");
    await expect(page.getByText("Signal Wizard unavailable")).toBeVisible();
    await expect(page.getByText("Fixture Feature Registry request failed closed")).toBeVisible();
  });

  test("blocks submission when preview contains a leakage warning", async ({ page }) => {
    await page.goto("/ai/signal-wizard");
    await page.getByLabel("Strategy ID").fill("leakage-warning-candidate");
    await page.getByRole("button", { name: "Generate canonical preview" }).click();

    await expect(page.getByText("FEATURE_TIMESTAMP_POLICY_REQUIRES_REVIEW")).toBeVisible();
    await expect(page.getByText(/blocking repaint\/leakage warning/)).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Submit research experiment candidate" }),
    ).toBeDisabled();
  });

  test(
    "fails closed for cross-tenant reads and mutation without CSRF",
    { tag: [tags.security, tags.permissions] },
    async ({ identity, page, request }) => {
      await identity.setState("cross_tenant");
      await page.goto("/ai/signal-wizard");
      await expect(page.getByText("Signal Wizard access denied")).toBeVisible();
      await expect(page.getByText("Authenticated membership does not authorize this tenant")).toBeVisible();

      await identity.authenticateRequest();
      const response = await request.post("/api/ai/signal-wizard/preview", {
        data: {
          contract_version: "v2",
          idempotency_key: "no-csrf",
          strategy_id: "blocked",
          feature_selections: [],
          condition_ast: {},
          capability: { capability: "strategy.research" },
        },
      });
      expect(response.status()).toBe(403);
      await expect(response.json()).resolves.toMatchObject({ code: "CSRF_MISSING" });
    },
  );

  test("surfaces submit conflicts without claiming persistence", async ({ page }) => {
    await page.goto("/ai/signal-wizard");
    await page.getByRole("button", { name: "Generate canonical preview" }).click();
    await page.getByLabel("Experiment name").fill("conflict");
    await page.getByRole("button", { name: "Submit research experiment candidate" }).click();

    await expect(page.getByText("Signal Wizard conflict")).toBeVisible();
    await expect(page.getByText("Preview version changed before submission")).toBeVisible();
    await expect(page.getByText("Experiment candidate accepted")).not.toBeVisible();
  });
});
