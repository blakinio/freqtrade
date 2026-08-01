export const WICKHUNTER_OBSERVABILITY_SCHEMA_VERSION =
  "wickhunter-portal-observability-snapshot-v1" as const;

export type WickHunterBotMode = "research" | "shadow" | "paper";
export type WickHunterRuntimeHealth = "healthy" | "degraded" | "fail_closed";
export type WickHunterSourceHealth = "healthy" | "degraded" | "failed" | "unknown";
export type WickHunterDriftState = "healthy" | "drifted" | "unknown";
export type WickHunterShadowStatus =
  | "simulated_allowed"
  | "ignored"
  | "rejected_by_risk";
export type WickHunterTradeDirection = "long" | "short";

export interface WickHunterRuntimeSourceStatus {
  source: string;
  health: WickHunterSourceHealth;
  observed_at_ms: number;
  last_received_at_ms: number | null;
  age_ms: number | null;
  fresh: boolean;
}

export interface WickHunterRuntimeDecisionSummary {
  shadow_decision_id: string;
  status: WickHunterShadowStatus;
  symbol: string;
  side: WickHunterTradeDirection | null;
  candidate_id: string | null;
  score_id: string | null;
  risk_decision_id: string | null;
  reason_codes: string[];
  observed_at_ms: number;
}

export interface WickHunterSimulatedPosition {
  position_id: string;
  trade_intent_id: string;
  symbol: string;
  side: WickHunterTradeDirection;
  opened_at_ms: number;
  entry_price: string;
  mark_price: string;
  quantity: string;
  take_profit_price: string;
  stop_loss_price: string;
  model_version: string | null;
  model_hash: string | null;
  parameter_version: string;
  parameter_hash: string;
}

export interface WickHunterPortalObservabilitySnapshot {
  schema_version: typeof WICKHUNTER_OBSERVABILITY_SCHEMA_VERSION;
  snapshot_id: string;
  bot_instance: string;
  mode: WickHunterBotMode;
  health: WickHunterRuntimeHealth;
  observed_at_ms: number;
  universe_snapshot_hash: string;
  dynamic_universe: string[];
  source_freshness: WickHunterRuntimeSourceStatus[];
  model_version: string | null;
  model_hash: string | null;
  parameter_version: string | null;
  parameter_hash: string | null;
  dataset_hash: string | null;
  code_sha: string | null;
  decisions: WickHunterRuntimeDecisionSummary[];
  positions: WickHunterSimulatedPosition[];
  cumulative_realized_pnl_quote: string;
  unrealized_pnl_quote: string;
  simulated_equity_quote: string;
  drawdown_ratio: string;
  retraining_state: string;
  validation_state: string;
  model_drift: WickHunterDriftState;
  data_drift: WickHunterDriftState;
  circuit_breaker_active: boolean;
  circuit_breaker_reasons: string[];
  persistence_generation: number;
  runtime_state_sha256: string;
  read_only: true;
  trading_credentials_present: false;
  order_adapter_present: false;
  orders_submitted: 0;
  live_capital_authorized: false;
}

export interface WickHunterObservabilityView {
  snapshot: WickHunterPortalObservabilitySnapshot;
  snapshot_age_ms: number;
  stale: boolean;
  source_path_kind: "fixture" | "configured";
}
