import { tags } from "./config/e2e.config";
import { expect, test } from "./fixtures/test.fixture";


test.describe(
  "AI Platform program closure",
  { tag: [tags.regression] },
  () => {
    test(
      "completes the authenticated paper-shadow journey without direct private-engine access",
      { tag: [tags.critical, tags.security] },
      async ({ botDetail, identity, page, request }) => {
        await identity.setState("authenticated");
        const observedRequests: string[] = [];
        page.on("request", (browserRequest) => {
          observedRequests.push(browserRequest.url());
        });

        await page.goto("/");
        await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
        await expect(page.getByLabel("Portal session")).toContainText(
          "Tenant tenant-demo · MFA verified",
        );
        await expect(page.getByText("Protected portal boundary active")).toBeVisible();
        await expect(page.getByText("Private execution boundary")).toBeVisible();

        await page.goto("/ai/signal-wizard");
        await expect(page.getByRole("heading", { name: "Signal Wizard" })).toBeVisible();
        await page.getByLabel("Use rsi.v1").check();
        await page.getByLabel("rsi.v1 period").fill("21");
        await page.getByLabel("Condition feature").selectOption("rsi.v1");
        await page.getByLabel("Condition operator").selectOption("lt");
        await page.getByLabel("Condition value").fill("35");
        await page.getByRole("button", { name: "Generate canonical preview" }).click();
        await expect(page.getByText("SIGNAL_WIZARD_PREVIEW_VALIDATED")).toBeVisible();
        await expect(page.getByText("Execution authority").last()).toBeVisible();
        await page.getByLabel("Experiment name").fill(
          "Program closure deterministic research candidate",
        );
        await page
          .getByRole("button", { name: "Submit research experiment candidate" })
          .click();
        await expect(page.getByText("Experiment candidate accepted")).toBeVisible();
        await expect(page.getByText("SIGNAL_WIZARD_CANDIDATE_PERSISTED")).toBeVisible();
        await expect(page.getByText(/Execution authority: no/)).toBeVisible();

        await page.goto("/bots/strategies");
        await expect(page.getByRole("heading", { name: "Strategy Catalog" })).toBeVisible();
        await expect(page.getByRole("heading", { name: "Version history" })).toBeVisible();
        await expect(page.getByRole("heading", { name: "Approval evidence" })).toBeVisible();
        await expect(
          page.getByRole("heading", { name: "Paper and shadow deployments" }),
        ).toBeVisible();
        await expect(page.getByRole("cell", { name: "SHADOW" }).last()).toBeVisible();
        await expect(page.getByRole("cell", { name: "ACTIVE" })).toBeVisible();
        await expect(page.getByText("Live capital authority").first()).toBeVisible();
        await page.getByLabel("Target version").selectOption("ai-directional-v2");
        await page.getByLabel("Evidence reason").fill(
          "Restore the last reviewed dry-run version after deterministic closure evidence.",
        );
        await page
          .getByRole("button", { name: "Request evidence-backed rollback" })
          .click();
        await expect(page.getByText("Rollback evidence RECORDED")).toBeVisible();
        await expect(page.getByText(/Audit reference: audit:rollback:/)).toBeVisible();
        await expect(page.getByText("Live capital authority: no")).toBeVisible();

        await botDetail.open();
        await expect(page.getByRole("heading", { name: "Command intent controls" })).toBeVisible();
        await expect(page.getByText("RISK_APPROVED", { exact: true })).toBeVisible();
        await expect(page.getByRole("heading", { name: "Source status" })).toBeVisible();

        await identity.authenticateRequest();
        const lifecyclePayload = {
          bot_id: "bot-btc-dryrun-01",
          action: "PAUSE_NEW_ENTRIES",
          expected_config_revision: 1,
          expected_runtime_generation_id: "fixture-generation:bot-btc-dryrun-01:1",
          idempotency_key: "program-closure-lifecycle-intent",
        };
        const firstIntent = await request.post(
          "/api/bot-management/commands/lifecycle-intents",
          {
            headers: identity.csrfHeaders(),
            data: lifecyclePayload,
          },
        );
        const replayedIntent = await request.post(
          "/api/bot-management/commands/lifecycle-intents",
          {
            headers: identity.csrfHeaders(),
            data: lifecyclePayload,
          },
        );
        expect(firstIntent.status()).toBe(202);
        expect(replayedIntent.status()).toBe(202);
        const firstIntentBody = await firstIntent.json();
        const replayedIntentBody = await replayedIntent.json();
        expect(replayedIntentBody.command_id).toBe(firstIntentBody.command_id);
        expect(replayedIntentBody.command_persisted).toBe(true);
        expect(replayedIntentBody.execution_submission_performed).toBe(false);
        expect(replayedIntentBody.execution_proven).not.toBe(true);

        await page.goto("/performance");
        await expect(page.getByRole("heading", { name: "PNL & Performance" })).toBeVisible();
        await expect(page.getByText("11.60", { exact: true })).toBeVisible();
        await page.goto("/orders");
        await expect(page.getByRole("heading", { name: "Orders" })).toBeVisible();
        await expect(page.getByText("fixture-order-1", { exact: true })).toBeVisible();
        await page.goto("/trades");
        await expect(page.getByRole("heading", { name: "Trade History" })).toBeVisible();
        await expect(page.getByText("trade-fixture-1", { exact: true })).toBeVisible();
        await page.goto("/operations/risk-events");
        await expect(page.getByText("RISK_APPROVED", { exact: true })).toBeVisible();
        await page.goto("/operations/audit");
        await expect(page.getByRole("heading", { name: "Audit Events" })).toBeVisible();
        await expect(page.getByText("bot.created", { exact: true })).toBeVisible();
        await page.goto("/operations/execution-logs");
        await expect(page.getByRole("heading", { name: "Execution Activity" })).toBeVisible();
        await expect(page.getByText("trade.manual_intent", { exact: true })).toBeVisible();
        await expect(page.getByText("Raw runtime logs: available")).toBeVisible();

        const requestEvidence = observedRequests.join("\n").toLowerCase();
        for (const forbidden of [
          "freqtrade.internal",
          "/api/v1/forceenter",
          "/api/v1/forceexit",
          "/api/v1/start",
          "/api/v1/stop",
          "api.binance.com",
          "api.bybit.com",
          "www.okx.com/api",
          "vault://",
          "credref_",
          "private_endpoint",
        ]) {
          expect(requestEvidence).not.toContain(forbidden);
        }
      },
    );

    test(
      "shows deterministic loading, stale, empty, denied, conflict and error states",
      { tag: [tags.critical] },
      async ({ identity, page }) => {
        await identity.setState("authenticated");
        let releaseCatalog: (() => void) | undefined;
        const catalogGate = new Promise<void>((resolve) => {
          releaseCatalog = resolve;
        });
        await page.route(/\/api\/strategy-catalog(?:\?.*)?$/, async (route) => {
          await catalogGate;
          await route.continue();
        });
        await page.goto("/bots/strategies");
        await expect(page.getByText("Loading Strategy Catalog…")).toBeVisible();
        releaseCatalog?.();
        await expect(page.getByRole("heading", { name: "Version history" })).toBeVisible();
        await page.unroute(/\/api\/strategy-catalog(?:\?.*)?$/);

        await page.goto("/ai/signal-wizard?wizard_view=stale");
        await expect(page.getByText("Feature Registry snapshot is stale")).toBeVisible();
        await expect(page.getByText(/FEATURE_REGISTRY_SNAPSHOT_STALE/)).toBeVisible();
        await page.goto("/ai/signal-wizard?wizard_view=empty");
        await expect(page.getByText("No approved AI features are available")).toBeVisible();
        await page.goto("/ai/signal-wizard?wizard_view=failure");
        await expect(page.getByText("Signal Wizard validation failed")).toBeVisible();
        await expect(
          page.getByText("Fixture Feature Registry request failed closed"),
        ).toBeVisible();

        await page.goto("/bots/strategies?catalog_view=stale");
        await expect(page.getByText("Catalog snapshot is stale")).toBeVisible();
        await expect(page.getByText("CATALOG_SNAPSHOT_STALE")).toBeVisible();
        await page.goto("/bots/strategies?catalog_view=empty");
        await expect(page.getByText("No strategy versions are available")).toBeVisible();
        await page.goto("/bots/strategies?catalog_view=failure");
        await expect(page.getByText("Strategy Catalog unavailable")).toBeVisible();

        await page.goto("/ai/signal-wizard");
        await page.getByRole("button", { name: "Generate canonical preview" }).click();
        await page.getByLabel("Experiment name").fill("conflict");
        await page
          .getByRole("button", { name: "Submit research experiment candidate" })
          .click();
        await expect(page.getByText("Signal Wizard conflict")).toBeVisible();
        await expect(page.getByText("Experiment candidate accepted")).not.toBeVisible();

        await identity.setState("cross_tenant");
        for (const deniedPath of ["/bots/strategies", "/ai/signal-wizard"]) {
          await page.goto(deniedPath);
          await expect(page).toHaveURL(/\/denied\?reason=cross_tenant$/);
          await expect(
            page.getByRole("heading", {
              name: "You do not have permission to view this resource",
            }),
          ).toBeVisible();
        }
      },
    );

    test(
      "enforces tenant, session, CSRF and secret-exclusion boundaries",
      { tag: [tags.security, tags.permissions, tags.critical] },
      async ({ identity, page, request }) => {
        await identity.setState("authenticated");
        await page.goto("/bots");
        await expect(page.getByLabel("Portal session")).toContainText(
          "Tenant tenant-demo · MFA verified",
        );
        const cookies = await page.context().cookies();
        expect(
          cookies.some(
            (cookie) => cookie.name === "portal_fixture_session" && cookie.httpOnly,
          ),
        ).toBe(true);
        expect(
          cookies.some(
            (cookie) => cookie.name === "portal_fixture_csrf" && !cookie.httpOnly,
          ),
        ).toBe(true);
        expect(cookies.some((cookie) => /access|refresh|id_token/i.test(cookie.name))).toBe(
          false,
        );

        await identity.authenticateRequest();
        const noCsrf = await request.post(
          "/api/strategy-catalog/ai-directional-v3/rollback",
          {
            data: {
              to_strategy_version: "ai-directional-v2",
              reason: "Program closure security request without CSRF.",
              idempotency_key: "program-closure-no-csrf",
            },
          },
        );
        expect(noCsrf.status()).toBe(403);
        await expect(noCsrf.json()).resolves.toMatchObject({ code: "CSRF_MISSING" });

        await identity.setState("cross_tenant");
        const crossTenant = await page.request.post("/api/terminal", {
          headers: identity.csrfHeaders(),
          data: {
            bot_id: "bot-btc-dryrun-01",
            pair: "BTC/USDT",
            side: "BUY",
            amount: "0.01",
          },
        });
        expect(crossTenant.status()).toBe(403);
        await expect(crossTenant.json()).resolves.toMatchObject({
          code: "CROSS_TENANT_DENIED",
        });
      },
    );

    test(
      "keeps critical closure surfaces usable at 390px",
      { tag: [tags.responsive] },
      async ({ identity, page }) => {
        await identity.setState("authenticated");
        await page.setViewportSize({ width: 390, height: 844 });

        for (const [path, heading] of [
          ["/ai/signal-wizard", "Signal Wizard"],
          ["/bots/strategies", "Strategy Catalog"],
          ["/performance", "PNL & Performance"],
        ] as const) {
          await page.goto(path);
          await expect(page.getByRole("heading", { name: heading })).toBeVisible();
          const overflow = await page.evaluate(
            () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
          );
          expect(overflow).toBeLessThanOrEqual(1);
        }
      },
    );
  },
);
