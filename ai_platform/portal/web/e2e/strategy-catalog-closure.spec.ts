import { tags } from "./config/e2e.config";
import { expect, test } from "./fixtures/test.fixture";


test.describe("Strategy Catalog closure", { tag: [tags.regression, tags.responsive] }, () => {
  test(
    "shows immutable history, approval, paper-shadow deployment and rollback evidence",
    { tag: [tags.critical] },
    async ({ page }) => {
      await page.goto("/bots/strategies");

      await expect(page.getByRole("heading", { name: "Strategy Catalog" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Version history" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Approval evidence" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Paper and shadow deployments" })).toBeVisible();
      await expect(page.getByText("OOS_EVIDENCE_ACCEPTED")).toBeVisible();
      await expect(page.getByRole("cell", { name: "SHADOW" }).last()).toBeVisible();
      await expect(page.getByRole("cell", { name: "ACTIVE" })).toBeVisible();
      await expect(page.getByText("Live capital authority").first()).toBeVisible();

      await page.getByLabel("Target version").selectOption("ai-directional-v2");
      await page.getByLabel("Evidence reason").fill(
        "Restore the last reviewed dry-run version after the shadow evidence review.",
      );
      await page.getByRole("button", { name: "Request evidence-backed rollback" }).click();

      await expect(page.getByText("Rollback evidence RECORDED")).toBeVisible();
      await expect(page.getByText("Source: ai-directional-v3")).toBeVisible();
      await expect(page.getByText("Target: ai-directional-v2")).toBeVisible();
      await expect(page.getByText(/Audit reference: audit:rollback:/)).toBeVisible();
      await expect(page.getByText("Live capital authority: no")).toBeVisible();
    },
  );

  test("renders stale, empty and failure states without inventing lifecycle evidence", async ({ page }) => {
    await page.goto("/bots/strategies?catalog_view=stale");
    await expect(page.getByText("Catalog snapshot is stale")).toBeVisible();
    await expect(page.getByText("CATALOG_SNAPSHOT_STALE")).toBeVisible();

    await page.goto("/bots/strategies?catalog_view=empty");
    await expect(page.getByText("No strategy versions are available")).toBeVisible();

    await page.goto("/bots/strategies?catalog_view=failure");
    await expect(page.getByText("Strategy Catalog unavailable")).toBeVisible();
    await expect(page.getByRole("button", { name: "Retry catalog request" })).toBeVisible();
  });

  test(
    "blocks cross-tenant reads and mutation requests without CSRF",
    { tag: [tags.security, tags.permissions] },
    async ({ identity, page, request }) => {
      await identity.setState("cross_tenant");
      await page.goto("/bots/strategies");
      await expect(page.getByText("Strategy Catalog access denied")).toBeVisible();
      await expect(page.getByText("Authenticated membership does not authorize this tenant")).toBeVisible();

      await identity.authenticateRequest();
      const response = await request.post(
        "/api/strategy-catalog/ai-directional-v3/rollback",
        {
          data: {
            to_strategy_version: "ai-directional-v2",
            reason: "Security check without a CSRF header.",
            idempotency_key: "strategy-catalog-no-csrf",
          },
        },
      );
      expect(response.status()).toBe(403);
      await expect(response.json()).resolves.toMatchObject({ code: "CSRF_MISSING" });
    },
  );

  test("rejects stale or invalid rollback targets at the same-origin boundary", async ({ identity, request }) => {
    await identity.authenticateRequest();
    const response = await request.post(
      "/api/strategy-catalog/ai-directional-v3/rollback",
      {
        headers: identity.csrfHeaders(),
        data: {
          to_strategy_version: "grid-dry-run-v2",
          reason: "Attempt a cross-strategy rollback target.",
          idempotency_key: "strategy-catalog-invalid-target",
        },
      },
    );
    expect(response.status()).toBe(409);
    await expect(response.json()).resolves.toMatchObject({
      detail: "Rollback target is not available for this strategy",
    });
  });
});
