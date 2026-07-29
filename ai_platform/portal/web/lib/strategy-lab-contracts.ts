export type StrategyParameterKind = "integer" | "number" | "boolean" | "enum";
export type ExperimentStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
export type SignalDecision = "ENTER_LONG" | "EXIT_LONG" | "HOLD";

export interface StrategyParameterSpec {
  name: string;
  kind: StrategyParameterKind;
  default: unknown;
  minimum: string | null;
  maximum: string | null;
  choices: unknown[];
}

export interface StrategyLabDefinition {
  strategy_id: string;
  strategy_version: string;
  display_name: string;
  source_type: "tradingview_inspired_clean_room";
  provenance: Record<string, unknown>;
  features: string[];
  entry_rules: string[];
  exit_rules: string[];
  parameters: StrategyParameterSpec[];
  timeframe_semantics: string;
  warm_up: number;
  confirmation_policy: "closed_bar" | "confirmed_htf";
  risk_defaults: Record<string, unknown>;
  supported_directions: string[];
}

export interface ExperimentTimerange {
  start_at: string;
  end_at: string;
}

export interface ExperimentCreateRequest {
  strategy_id: string;
  strategy_version: string;
  pair: string;
  timeframe: string;
  timerange: ExperimentTimerange;
  starting_balance: string;
  fee_rate: string;
  slippage_rate: string;
  parameter_overrides: Record<string, unknown>;
  execution_mode: "backtest";
}

export interface ExperimentSummary {
  experiment_id: string;
  status: ExperimentStatus;
  strategy_id: string;
  strategy_version: string;
  pair: string;
  timeframe: string;
  started_at: string;
  trade_count: number;
  profit_abs: string;
  profit_pct: string;
  max_drawdown: string;
}

export interface ExperimentDetail extends ExperimentSummary {
  tenant_id: string;
  timerange: ExperimentTimerange;
  data_identity: string;
  code_identity: string;
  parameters: Record<string, unknown>;
  finished_at: string;
  wins: number;
  losses: number;
  win_rate: string;
  average_trade: string;
  exposure: string;
  result_hash: string;
  research_only: true;
  order_submission_performed: false;
}

export interface ExperimentTrade {
  trade_id: string;
  pair: string;
  side: "long";
  entry_at: string;
  exit_at: string;
  entry_price: string;
  exit_price: string;
  quantity: string;
  fee_abs: string;
  profit_abs: string;
  profit_pct: string;
  entry_signal_id: string;
  exit_signal_id: string;
  entry_reason_codes: string[];
  exit_reason_codes: string[];
}

export interface SignalExplanation {
  signal_id: string;
  timestamp: string;
  pair: string;
  timeframe: string;
  strategy_id: string;
  strategy_version: string;
  decision: SignalDecision;
  matched_conditions: string[];
  feature_values: Record<string, unknown>;
  parameter_values: Record<string, unknown>;
  reason_codes: string[];
  price: string;
}

export interface EquityPoint {
  timestamp: string;
  equity: string;
  drawdown_pct: string;
}

export interface ExperimentComparison {
  baseline_experiment_id: string;
  variant_experiment_id: string;
  metric_deltas: Record<string, string>;
  parameter_differences: Record<string, [unknown | null, unknown | null]>;
}

export interface ExperimentBundle {
  detail: ExperimentDetail;
  trades: ExperimentTrade[];
  signals: SignalExplanation[];
  equity: EquityPoint[];
}
