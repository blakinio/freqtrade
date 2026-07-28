import { expect, type Page } from "@playwright/test";

export class AppShellPage {
  constructor(private readonly page: Page) {}

  async open(path = "/"): Promise<void> {
    await this.page.goto(path);
  }

  async expectDashboard(): Promise<void> {
    await expect(this.page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(this.page.getByTestId("environment-badge")).toHaveText("TEST");
  }

  async expectPrimaryNavigation(): Promise<void> {
    await expect(this.page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
    await expect(this.page.getByRole("link", { name: "PNL & Performance" })).toBeVisible();
    await expect(this.page.getByRole("link", { name: "Trade Analysis" })).toBeVisible();
    await expect(this.page.getByRole("link", { name: "Runtime Health" })).toBeVisible();
  }
}

export class BotFleetPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto("/bots");
    await expect(this.page.getByRole("heading", { name: "Bot fleet" })).toBeVisible();
  }

  async openFirstBot(): Promise<void> {
    await this.page.getByRole("link", { name: "Open", exact: true }).first().click();
  }

  async filterByMarket(market: string): Promise<void> {
    await this.page.getByLabel("Market").fill(market);
    await this.page.getByRole("button", { name: "Apply filters" }).click();
  }
}

export class BotDetailPage {
  constructor(private readonly page: Page) {}

  async open(botId = "bot-btc-dryrun-01"): Promise<void> {
    await this.page.goto(`/bots/detail/${botId}`);
    await expect(this.page.getByRole("heading", { name: "BTC AI Dry Run" })).toBeVisible();
  }

  async createRevision(modelVersion: string): Promise<void> {
    this.page.once("dialog", (dialog) => dialog.accept());
    await this.page.getByLabel("Model version").fill(modelVersion);
    await this.page.getByRole("button", { name: "Create revision 2" }).click();
  }

  async requestPause(): Promise<void> {
    this.page.once("dialog", (dialog) => dialog.accept());
    await this.page.getByRole("button", { name: "Pause" }).click();
  }
}

export class LiquidationsPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto("/market/liquidations");
    await expect(this.page.getByRole("heading", { name: "Likwidacje", exact: true })).toBeVisible();
  }

  async filterBySource(source: "binance-usdm" | "bybit-linear"): Promise<void> {
    await this.page.getByLabel("Źródło").selectOption(source);
  }

  async filterBySymbol(symbol: string): Promise<void> {
    await this.page.getByLabel("Symbol").fill(symbol);
  }
}
