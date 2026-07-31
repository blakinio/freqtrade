import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";

const snapshotSha = "b".repeat(64);

test.describe("Signal Wizard closure", { tag: [tags.regression, tags.responsive] }, () => {
  test(
    "selects approved features, validates a preview and creates a research experiment",
    { tag: [tags.critical] },
    async ({ page }) => {
      const browserRequests: string[] = [];
      page.on("request", (request) => {
        if (["fetch", "xhr"].includes(request.resourceType())) browserRequests.push(request.url());
      });

      await page.goto("/ai/signal-wizard");
      await expect(page.getByRole("heading", { name: "Signal Wizard" })).toBeVisible();
      await expect(page.getByText("Approved registry boundary")).toBeVisible();
      await expect(page.getByText("Execution authority").first()).toBeVisible();

      await page.getByLabel("Select atr.v1").check();
      await page.getByLabel("atr.v1 period").fill("21");
      await page.getByRole("button", { name: "Build strategy preview" }).click();

      await expect(page.getByRole("heading", { name: "Preview validated" })).toBeVisible();
      await expect(page.getByText("SIGNAL_WIZARD_PREVIEW_VALIDATED")).toBeVisible();
      await expect(page.getByText("No leakage or repaint warning blocks submission")).toBeVisible();
      await expect(page.getByText("Promotion authority").first()).toBeVisible();

      await page.getByLabel("Experiment name").fill("ATR closed-bar research experiment");
      await page.getByRole("button", { name: "Create research experiment" }).click();

      await expect(page.getByRole("heading", { name: "Experiment accepted" })).toBeVisible();
      await expect(page.getByText("SIGNAL_WIZARD_CANDIDATE_PERSISTED")).toBeVisible();
      await expect(page.getByText("Promotion authority").last()).toBeVisible();

      const origin = new URL(page.url()).origin;
      expect(browserRequests.length).toBeGreaterThan(0);
      for (const requestUrl of browserRequests) {
        const parsed = new URL(requestUrl);
        expect(parsed.origin).toBe(origin);
        expect(parsed.pathname).not.toMatch(/freqtrade|exchange|vault/i);
      }
    },
  );

  test("renders stale, empty and failure states without inventing registry evidence", async ({ page }) => {
    await page.goto("/ai/signal-wizard?wizard_view=stale");
    await expect(page.getByText("Feature Registry snapshot is stale")).toBeVisible();
    await expect(page.getByText("FEATURE_REGISTRY_SNAPSHOT_STALE")).toBeVisible();
    await expect(page.getByRole("button", { name: "Build strategy preview" })).toBeDisabled();

    await page.goto("/ai/signal-wizard?wizard_view=empty");
    await expect(page.getByText("No approved AI features are available")).toBeVisible();

    await page.goto("/ai/signal-wizard?wizard_view=failure");
    await expect(page.getByText("Signal Wizard unavailable")).toBeVisible();
    await expect(page.getByText("SIGNAL_WIZARD_REGISTRY_UNAVAILABLE")).toBeVisible();
    await expect(page.getByRole("button", { name: "Retry registry request" })).toBeVisible();
  });

  test("blocks experiment submission when leakage validation is blocking", async ({ page }) => {
    await page.goto("/ai/signal-wizard?wizard_view=leakage");
    await page.getByLabel("Select atr.v1").check();
    await page.getByRole("button", { name: "Build strategy preview" }).click();

    await expect(page.getByText("FEATURE_TIMESTAMP_POLICY_REQUIRES_REVIEW")).toBeVisible();
    await expect(page.getByText(/Blocking/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Create research experiment" })).toBeDisabled();
  });

  test("blocks invalid registry parameter relationships before preview", async ({ page }) => {
    await page.goto("/ai/signal-wizard");
    await page.getByLabel("Select macd.v1").check();
    await page.getByLabel("macd.v1 fast").fill("50");
    await page.getByLabel("macd.v1 slow").fill("20");

    await expect(page.getByText("Parameter constraints are not satisfied")).toBeVisible();
    await expect(page.getByText(/FEATURE_PARAMETER_CONSTRAINT_INVALID/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Build strategy preview" })).toBeDisabled();
  });

  test("surfaces an actionable submit conflict without creating an experiment", async ({ page }) => {
    await page.goto("/ai/signal-wizard?wizard_view=conflict");
    await page.getByLabel("Select atr.v1").check();
    await page.getByRole("button", { name: "Build strategy preview" }).click();
    await expect(page.getByRole("heading", { name: "Preview validated" })).toBeVisible();

    await page.getByRole("button", { name: "Create research experiment" }).click();
    await expect(page.getByText("Experiment submission blocked")).toBeVisible();
    await expect(page.getByText(/SIGNAL_WIZARD_CONFLICT/)).toBeVisible();
    await expect(page.getByRole("heading", { name: "Experiment accepted" })).not.toBeVisible();
  });

  test(
    "denies cross-tenant access, missing CSRF and unapproved feature injection",
    { tag: [tags.security, tags.permissions] },
    async ({ identity, page, request }) => {
      await identity.setState("cross_tenant");
      await page.goto("/ai/signal-wizard");
      await expect(page.getByText("Signal Wizard access denied")).toBeVisible();
      await expect(page.getByText("CROSS_TENANT_DENIED")).toBeVisible();

      await identity.authenticateRequest();
      const requestBody = {
        idempotency_key: "signal-wizard-security-preview",
        strategy_id: "security-strategy",
        base_strategy_version: null,
        registry_version: "1.0.0",
        snapshot_sha256: snapshotSha,
        feature_selections: [
          {
            contract_version: "v2",
            feature_id: "squeeze_ratio.v1",
            timeframe: "5m",
            parameters: {},
            enabled: true,
          },
        ],
        parameter_constraints: [],
        condition_ast: {
          all: [{ feature: "squeeze_ratio.v1", op: "gt", value: 0 }],
        },
      };

      const missingCsrf = await request.post("/api/ai/signal-wizard/preview", {
        data: requestBody,
      });
      expect(missingCsrf.status()).toBe(403);
      await expect(missingCsrf.json()).resolves.toMatchObject({ code: "CSRF_MISSING" });

      const unapproved = await request.post("/api/ai/signal-wizard/preview", {
        headers: identity.csrfHeaders(),
        data: requestBody,
      });
      expect(unapproved.status()).toBe(422);
      await expect(unapproved.json()).resolves.toMatchObject({
        reason_code: "FEATURE_NOT_APPROVED_FOR_AI",
      });
    },
  );
});
