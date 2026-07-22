import type {
  BotInstance,
  CreateBotRequest,
  DashboardSnapshot,
  PortalEnvironment,
  TerminalIntentRequest,
  TerminalIntentResult,
} from "./contracts";

const fixtureBots: BotInstance[] = [
  {
    bot_id: "bot-btc-dryrun-01",
    tenant_id: "tenant-demo",
    name: "BTC AI Dry Run",
    spec: {
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
    },
    desired_state: "RUNNING",
    observed_state: "RUNNING",
  },
  {
    bot_id: "bot-eth-dryrun-02",
    tenant_id: "tenant-demo",
    name: "ETH Validation Bot",
    spec: {
      tenant_id: "tenant-demo",
      strategy_version: "ai-directional-v1",
      model_version: "model-validated-2026-07",
      risk_policy_version: "risk-default-v1",
      exchange_connection_ref: "exchange-simulated-kraken",
      pair_universe: ["ETH/USDT"],
      timeframe: "15m",
      capital_allocation: "750",
      capital_currency: "USDT",
      runtime_version: "freqtrade-2026.7",
      config_revision: 2,
      environment: "test",
      execution_mode: "dry_run",
    },
    desired_state: "PAUSED",
    observed_state: "PAUSED",
  },
];

export function listFixtureBots(): BotInstance[] {
  return structuredClone(fixtureBots);
}

export function createFixtureBot(request: CreateBotRequest): BotInstance {
  return {
    bot_id: request.bot_id,
    tenant_id: request.spec.tenant_id,
    name: request.name,
    spec: request.spec,
    desired_state: "CREATED",
    observed_state: "CREATED",
  };
}

export function fixtureDashboard(environment: PortalEnvironment): DashboardSnapshot {
  const bots = listFixtureBots();
  return {
    environment,
    freshnessLabel: "Fixture snapshot · deterministic E2E data",
    activeBots: bots.filter((bot) => bot.observed_state === "RUNNING").length,
    attentionBots: bots.filter((bot) => bot.observed_state === "ERROR").length,
    runtimeHealth: "healthy",
    modelHealth: "healthy",
    riskStatus: "normal",
    bots,
  };
}

export function submitFixtureTerminalIntent(request: TerminalIntentRequest): TerminalIntentResult {
  const rejected = Number(request.amount) > 0.5;
  return {
    risk_decision: {
      risk_decision_id: "fixture-risk-decision-1",
      trade_intent_id: "fixture-trade-intent-1",
      risk_policy_version: "risk-default-v1",
      decision: rejected ? "REJECTED" : "APPROVED",
      reason_codes: [rejected ? "ORDER_NOTIONAL_LIMIT_EXCEEDED" : "RISK_APPROVED"],
    },
    execution_state: rejected ? "REJECTED" : "BLOCKED",
    execution_reason_code: rejected
      ? "ORDER_NOTIONAL_LIMIT_EXCEEDED"
      : "ORDER_SUBMISSION_NOT_IMPLEMENTED",
    order: null,
  };
}
