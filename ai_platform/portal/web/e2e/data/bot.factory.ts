import type { TestInfo } from "@playwright/test";

export const canonicalBtcBotSpec = {
  tenant_id: "tenant-demo",
  strategy_version: "ai-directional-v1",
  model_version: "model-validated-2026-07",
  risk_policy_version: "risk-default-v1",
  exchange_connection_ref: "exchange-simulated-kraken",
  pair_universe: ["BTC/USDT"],
  timeframe: "5m",
  capital_allocation: "1000",
  capital_currency: "USDT",
  runtime_version: "freqtrade-2026.7",
  config_revision: 1,
  environment: "test",
  execution_mode: "dry_run",
} as const;

export function createUniqueBot(testInfo: TestInfo) {
  const slug = testInfo.title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 32);
  const suffix = `${testInfo.project.name}-${testInfo.workerIndex}`
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-");
  const botId = `bot-e2e-${slug}-${suffix}`.slice(0, 64);

  return {
    botId,
    name: `E2E Dry Run ${testInfo.workerIndex}`,
    spec: { ...canonicalBtcBotSpec },
  };
}
