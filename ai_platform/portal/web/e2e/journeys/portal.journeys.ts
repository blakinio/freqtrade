import { expect, type APIRequestContext, type Page } from "@playwright/test";

import { fixtureCsrfToken } from "../config/e2e.config";

export type FixtureIdentityState =
  | "authenticated"
  | "anonymous"
  | "expired"
  | "revoked"
  | "mfa_missing"
  | "step_up_stale"
  | "cross_tenant";

export class IdentityJourney {
  constructor(
    private readonly page: Page,
    private readonly request: APIRequestContext,
  ) {}

  async setState(state: FixtureIdentityState): Promise<void> {
    const response = await this.page.request.post("/api/identity/fixture-state", {
      data: { state },
    });
    expect(response.status()).toBe(200);
  }

  async authenticateRequest(): Promise<void> {
    const response = await this.request.post("/api/identity/fixture-state", {
      data: { state: "authenticated" },
    });
    expect(response.status()).toBe(200);
  }

  csrfHeaders(): Record<string, string> {
    return { "x-csrf-token": fixtureCsrfToken };
  }
}

export class BotJourney {
  constructor(private readonly page: Page) {}

  async finalizeDryRunConfiguration(botId: string): Promise<void> {
    await this.page.goto("/bots/new");
    await expect(
      this.page.getByRole("heading", { name: "Create Bot Configuration" }),
    ).toBeVisible();
    await this.page.getByLabel("Bot ID").fill(botId);
    await this.page
      .getByRole("button", { name: "Finalize dry-run configuration" })
      .click();
  }

  async submitManualIntent(): Promise<void> {
    await this.page.goto("/terminal");
    await expect(
      this.page.getByRole("heading", { name: "Risk-gated manual intent" }),
    ).toBeVisible();
    await this.page.getByRole("button", { name: "Submit trade intent" }).click();
  }
}
