import type { PortalEnvironment } from "./contracts";

export type CatalogEntryState = "ACTIVE" | "DEPRECATED" | "UNAVAILABLE";
export type ExecutionMode = "dry_run";
export type MarketType = "spot" | "margin" | "futures";
export type TradeDirection = "long" | "short" | "both";

export interface CatalogVersionRef {
  catalog_id: string;
  version: string;
}

export interface BotTemplateVersion {
  template_id: string;
  revision: number;
  display_name: string;
  bot_family: "directional" | "dca" | "signal" | "grid";
  supported_strategy_versions: string[];
  supported_model_versions: string[];
  supported_exchange_profile_versions: string[];
  supported_market_types: MarketType[];
  supported_directions: TradeDirection[];
  supported_execution_modes: ExecutionMode[];
  required_policy_families: string[];
  optional_policy_families: string[];
  created_at: string;
}

export interface CatalogTemplateEntry {
  template: BotTemplateVersion;
  state: CatalogEntryState;
  model_requirement: "FORBIDDEN" | "OPTIONAL" | "REQUIRED";
  sha256: string;
  published_at: string;
}

export interface StrategyCatalogEntry {
  strategy_id: string;
  version: string;
  state: CatalogEntryState;
  supported_market_types: MarketType[];
  supported_directions: TradeDirection[];
  supported_execution_modes: ExecutionMode[];
  supported_model_versions: string[];
  supported_runtime_versions: string[];
  supported_risk_policy_versions: string[];
  supported_policy_families: string[];
}

export interface ModelCatalogEntry {
  model_id: string;
  version: string;
  state: CatalogEntryState;
  compatible_strategy_versions: string[];
  supported_runtime_versions: string[];
}

export interface ExchangeProfileCatalogEntry {
  version: string;
  state: CatalogEntryState;
  profile: {
    profile_id: string;
    revision: number;
    exchange_id: string;
    market_types: MarketType[];
    supports_short: boolean;
  };
}

export interface RuntimeCatalogEntry {
  runtime_id: string;
  version: string;
  state: CatalogEntryState;
  supported_market_types: MarketType[];
  supported_execution_modes: ExecutionMode[];
}

export interface RiskPolicyCatalogEntry {
  risk_policy_id: string;
  version: string;
  state: CatalogEntryState;
  supported_market_types: MarketType[];
  supported_execution_modes: ExecutionMode[];
  supported_policy_families: string[];
}

export interface BotCatalogSnapshot {
  catalog_id: string;
  revision: number;
  published_at: string;
  templates: CatalogTemplateEntry[];
  strategies: StrategyCatalogEntry[];
  models: ModelCatalogEntry[];
  exchange_profiles: ExchangeProfileCatalogEntry[];
  runtimes: RuntimeCatalogEntry[];
  risk_policies: RiskPolicyCatalogEntry[];
}

export interface BotConfigurationDraftPayload {
  catalog_ref: CatalogVersionRef;
  template_ref: CatalogVersionRef;
  strategy_version: string;
  model_version: string | null;
  exchange_connection_ref: string;
  exchange_profile_version: string;
  market_policy: {
    policy_id: string;
    revision: number;
    pairs: string[];
    market_type: MarketType;
    direction: TradeDirection;
    timeframe: string;
    margin_mode: null;
    leverage: null;
  };
  entry_policy: {
    policy_id: string;
    revision: number;
    order_type: "market";
    limit_offset_percent: null;
    cooldown_seconds: number;
    duplicate_signal_behavior: "reject";
    max_concurrent_positions: number;
  };
  position_sizing_policy: {
    policy_id: string;
    revision: number;
    mode: "fixed_quote_amount";
    fixed_base_quantity: null;
    fixed_quote_amount: string;
    quote_allocation_percent: null;
    max_per_pair_allocation_percent: string;
    max_total_allocation_percent: string;
  };
  dca_policy: null;
  exit_policy: {
    policy_id: string;
    revision: number;
    take_profit: null;
    stop_loss: null;
    break_even: null;
    trailing_stop: null;
    time_exit_seconds: null;
    strategy_exit_enabled: true;
  };
  risk_policy_version: string;
  signal_policy: null;
  grid_policy: null;
  runtime_policy: {
    policy_id: string;
    revision: number;
    runtime_version: string;
    execution_mode: ExecutionMode;
    heartbeat_timeout_seconds: number;
    command_timeout_seconds: number;
    reconciliation_timeout_seconds: number;
    restart_policy: "never";
    max_restart_attempts: 0;
  };
  environment: PortalEnvironment;
  execution_mode: ExecutionMode;
}

export interface CreateBotConfigurationDraftRequest {
  draft_id: string;
  bot_id: string;
  payload: BotConfigurationDraftPayload;
}

export interface FinalizedConfigurationSummary {
  draft_id: string;
  configuration_id: string;
  bot_id: string;
  revision: number;
  configuration_sha256: string;
  compatibility_status: "COMPATIBLE";
  execution_mode: ExecutionMode;
  runtime_submission_performed: false;
}
