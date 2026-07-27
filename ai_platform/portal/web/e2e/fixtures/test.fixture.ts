import { test as base, expect } from "@playwright/test";

import { BotJourney, IdentityJourney } from "../journeys/portal.journeys";
import {
  AppShellPage,
  BotDetailPage,
  BotFleetPage,
  LiquidationsPage,
} from "../pages/portal.pages";
import { attachFailureEvidence } from "../support/quality";

type PortalFixtures = {
  appShell: AppShellPage;
  botDetail: BotDetailPage;
  botFleet: BotFleetPage;
  botJourney: BotJourney;
  identity: IdentityJourney;
  liquidations: LiquidationsPage;
  failureEvidence: void;
};

export const test = base.extend<PortalFixtures>({
  appShell: async ({ page }, provide) => {
    await provide(new AppShellPage(page));
  },
  botDetail: async ({ page }, provide) => {
    await provide(new BotDetailPage(page));
  },
  botFleet: async ({ page }, provide) => {
    await provide(new BotFleetPage(page));
  },
  botJourney: async ({ page }, provide) => {
    await provide(new BotJourney(page));
  },
  identity: async ({ page, request }, provide) => {
    await provide(new IdentityJourney(page, request));
  },
  liquidations: async ({ page }, provide) => {
    await provide(new LiquidationsPage(page));
  },
  failureEvidence: [
    async ({ page }, provide, testInfo) => {
      const consoleMessages: string[] = [];
      const failedRequests: string[] = [];

      page.on("console", (message) => {
        if (["warning", "error"].includes(message.type())) {
          consoleMessages.push(`${message.type()}: ${message.text()}`);
        }
      });
      page.on("requestfailed", (request) => {
        const failure = request.failure();
        failedRequests.push(`${request.method()} ${request.url()} :: ${failure?.errorText ?? "unknown"}`);
      });

      await provide();
      await attachFailureEvidence(testInfo, consoleMessages, failedRequests);
    },
    { auto: true },
  ],
});

export { expect };
