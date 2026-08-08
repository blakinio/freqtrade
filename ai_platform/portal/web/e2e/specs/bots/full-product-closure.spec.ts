import { tags } from "../../config/e2e.config";
import { expect, test } from "../../fixtures/test.fixture";


test.describe(
  "BM-09 bot-management repository closure",
  { tag: [tags.critical, tags.regression, tags.security] },
  () => {
    test("traverses integrated dry-run surfaces without browser-to-Freqtrade traffic", async ({
      appShell,
      botDetail,
      botFleet,
      page,
    }) => {
      const observedRequests: string[] = [];
      page.on("request", (request) => observedRequests.push(request.url()));

      await appShell.open();
      await appShell.expectDashboard();
      await appShell.expectPrimaryNavigation();

      await botFleet.open();
      await expect(page.getByText("BTC AI Dry Run")).toBeVisible();
      await expect(page.getByText("TEST", { exact: true }).first()).toBeVisible();

      await botDetail.open();
      await expect(page.getByRole("heading", { name: "Command intent controls" })).toBeVisible();
      await expect(page.getByText("RISK_APPROVED", { exact: true })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Source status" })).toBeVisible();

      await page.goto("/platform/exchanges");
      await expect(page.getByRole("heading", { name: "Exchange Connections" })).toBeVisible();
      await expect(page.getByText("Simulated dry-run")).toBeVisible();
      await expect(page.getByText("Not exposed", { exact: true })).toBeVisible();

      await page.goto("/bots/signals");
      await expect(page.getByRole("heading", { name: "Signal Control" })).toBeVisible();
      await expect(page.getByText("Authentication provider: UNAVAILABLE")).toBeVisible();
      await expect(page.getByText(/Execution submission: no/)).toBeVisible();

      await page.goto("/bots/grid");
      await expect(page.getByRole("heading", { name: "Grid Control" })).toBeVisible();
      await expect(page.getByText("Capability evidence provider: UNAVAILABLE")).toBeVisible();
      await expect(page.getByText("Not submitted", { exact: true })).toBeVisible();

      const requestEvidence = observedRequests.join("\n").toLowerCase();
      for (const forbidden of [
        "freqtrade.internal",
        "/api/v1/forceenter",
        "/api/v1/forceexit",
        "/open-order",
        "vault://",
        "credref_",
      ]) {
        expect(requestEvidence).not.toContain(forbidden);
      }
    });

    test("keeps accepted lifecycle intent distinct from execution proof", async ({
      identity,
      request,
    }) => {
      await identity.authenticateRequest();
      const payload = {
        bot_id: "bot-btc-dryrun-01",
        action: "PAUSE_NEW_ENTRIES",
        expected_config_revision: 1,
        expected_runtime_generation_id: "fixture-generation:bot-btc-dryrun-01:1",
        idempotency_key: "bm09-lifecycle-replay",
      };

      const first = await request.post("/api/bot-management/commands/lifecycle-intents", {
        headers: identity.csrfHeaders(),
        data: payload,
      });
      const replay = await request.post("/api/bot-management/commands/lifecycle-intents", {
        headers: identity.csrfHeaders(),
        data: payload,
      });

      expect(first.status()).toBe(202);
      expect(replay.status()).toBe(202);
      const firstBody = await first.json();
      const replayBody = await replay.json();
      expect(replayBody.command_id).toBe(firstBody.command_id);
      expect(replayBody.command_persisted).toBe(true);
      expect(replayBody.execution_submission_performed).toBe(false);
      expect(replayBody.execution_proven).not.toBe(true);
    });
  },
);
