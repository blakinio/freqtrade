export type PortalEnvironment = "research" | "test" | "staging" | "production";
export type ExecutionMode = "simulated" | "dry_run";
export type BotDesiredState = "CREATED" | "RUNNING" | "PAUSED" | "STOPPED";
export type BotObservedState =
  | "CREATED"
  | "PROVISIONING"
  | "STARTING"
  | "RUNNING"
  | "PAUSED"
  | "STOPPING"
  | "STOPPED"
  | "ERROR";

export interface BotSpec {
  tenant_id: string;
  strategy_version: string;
  model_version: string;
  risk_policy_version: string;
  exchange_connection_ref: string;
  pair_universe: string[];
  timeframe: string;
  capital_allocation: string;
  capital_currency: string;
  runtime_version: string;
  config_revision: number;
  environment: PortalEnvironment;
  execution_mode: ExecutionMode;
}

export interface BotInstance {
  bot_id: string;
  tenant_id: string;
  name: string;
  spec: BotSpec;
  desired_state: BotDesiredState;
  observed_state: BotObservedState;
}

export interface CreateBotRequest {
  bot_id: string;
  name: string;
  spec: BotSpec;
}

export interface DashboardSnapshot {
  environment: PortalEnvironment;
  freshnessLabel: string;
  activeBots: number;
  attentionBots: number;
  runtimeHealth: "healthy" | "degraded" | "unknown";
  modelHealth: "healthy" | "degraded" | "unknown";
  riskStatus: "normal" | "attention" | "unknown";
  bots: BotInstance[];
}
