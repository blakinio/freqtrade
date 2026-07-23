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
export type TradeSide = "BUY" | "SELL";
export type TerminalExecutionState = "REJECTED" | "BLOCKED" | "SUBMITTED";
export type ModelLifecycleState =
  | "EXPERIMENTAL"
  | "CANDIDATE"
  | "VALIDATED"
  | "PROMOTED"
  | "DRY_RUN"
  | "SHADOW"
  | "LIVE_SMALL"
  | "PRODUCTION"
  | "DEPRECATED"
  | "REJECTED";
export type ReconciliationStatus = "SYNCED" | "PENDING" | "SOURCE_UNAVAILABLE" | "MISMATCH";
export type DiagnosisCode =
  | "PROFITABLE"
  | "LOSS_WITHIN_EXPECTED_RISK"
  | "LOSS_REQUIRES_REVIEW"
  | "DATA_GAP";
export type InsightSeverity = "INFO" | "ATTENTION" | "SEVERE";
export type AutonomyLevel = "L0" | "L1" | "L2" | "L3" | "L4";
export type ExperimentOutcome = "PENDING" | "POSITIVE" | "NEGATIVE" | "INCONCLUSIVE";
export type OrderState = "SUBMITTED" | "OPEN" | "PARTIALLY_FILLED" | "FILLED" | "CANCELED" | "REJECTED";

export interface CorrelationContext {
  request_id: string;
  correlation_id: string;
  causation_id: string | null;
}

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

export interface TerminalIntentRequest {
  bot_id: string;
  pair: string;
  side: TradeSide;
  amount: string;
}

export interface TerminalRiskDecision {
  risk_decision_id: string;
  trade_intent_id: string;
  risk_policy_version: string;
  decision: "APPROVED" | "REJECTED";
  reason_codes: string[];
}

export interface TerminalOrder {
  order_id: string;
  pair: string;
  side: TradeSide;
  state: string;
  amount: string;
}

export interface TerminalIntentResult {
  risk_decision: TerminalRiskDecision;
  execution_state: TerminalExecutionState;
  execution_reason_code: string;
  order: TerminalOrder | null;
}

export interface TrainingWindow {
  start_at: string;
  end_at: string;
}

export interface ModelParameter {
  name: string;
  value_json: string;
}

export interface ExperimentReference {
  experiment_id: string;
  tenant_id: string;
  run_id: string;
}

export interface ModelVersion {
  model_version_id: string;
  tenant_id: string;
  model_family_id: string;
  artifact_id: string;
  artifact_sha256: string;
  feature_schema_version_id: string;
  dataset_version_id: string;
  training_window: TrainingWindow;
  training_pipeline_version_id: string;
  parameters: ModelParameter[];
  git_revision: string;
  created_at: string;
  lifecycle_state: ModelLifecycleState;
  experiment_reference: ExperimentReference | null;
}

export interface DecisionSnapshot {
  snapshot_id: string;
  tenant_id: string;
  bot_id: string;
  trade_intent_id: string;
  risk_decision_id: string;
  config_revision: number;
  strategy_version: string;
  model_version: string;
  risk_policy_version: string;
  source_runtime_id: string;
  pair: string;
  side: TradeSide;
  amount: string;
  decision_at: string;
  evidence_ref: string;
  evidence_sha256: string;
}

export interface TradeOutcome {
  outcome_id: string;
  tenant_id: string;
  trade_id: string;
  bot_id: string;
  source_runtime_id: string;
  pair: string;
  realized_pnl: string;
  fees: string;
  exit_reason: string;
  opened_at: string;
  closed_at: string;
  reconciliation_status: ReconciliationStatus;
  loss_exceeded_risk_budget: boolean;
}

export interface DeterministicDiagnosis {
  diagnosis_id: string;
  tenant_id: string;
  snapshot_id: string;
  outcome_id: string;
  code: DiagnosisCode;
  reason_codes: string[];
  evidence_links: string[];
  created_at: string;
}

export interface TradeInsight {
  insight_id: string;
  tenant_id: string;
  diagnosis_id: string;
  severity: InsightSeverity;
  summary: string;
  synthesis_source: string;
  evidence_links: string[];
  created_at: string;
}

export interface TradeAnalysis {
  analysis_id: string;
  tenant_id: string;
  snapshot: DecisionSnapshot;
  outcome: TradeOutcome;
  diagnosis: DeterministicDiagnosis;
  insight: TradeInsight;
  created_at: string;
}

export interface EvidenceWindow {
  start_at: string;
  end_at: string;
}

export interface LearningHypothesis {
  hypothesis_id: string;
  tenant_id: string;
  source_insight_id: string;
  statement: string;
  evidence_links: string[];
  created_by_actor_id: string;
  created_at: string;
}

export interface LearningExperiment {
  experiment_id: string;
  tenant_id: string;
  hypothesis_id: string;
  evidence_window: EvidenceWindow;
  autonomy_level: AutonomyLevel;
  outcome: ExperimentOutcome;
  result_summary: string;
  created_by_actor_id: string;
  created_at: string;
}

export interface LearningCandidate {
  candidate_id: string;
  tenant_id: string;
  experiment_id: string;
  model_family_id: string;
  candidate_model_version_id: string;
  dataset_version_id: string;
  feature_schema_version_id: string;
  autonomy_level: AutonomyLevel;
  promoted: boolean;
  assigned_to_bot: boolean;
  created_by_actor_id: string;
  created_at: string;
}

export interface LearningHistoryEntry {
  hypothesis: LearningHypothesis;
  experiments: LearningExperiment[];
  candidates: LearningCandidate[];
}

export interface OperationalOrder {
  tenant_id: string;
  bot_id: string;
  source_runtime_id: string;
  order_id: string;
  execution_intent_id: string;
  pair: string;
  side: TradeSide;
  state: OrderState;
  amount: string;
  created_at: string;
}

export interface OperationalPosition {
  tenant_id: string;
  bot_id: string;
  source_runtime_id: string;
  position_id: string;
  pair: string;
  side: TradeSide;
  amount: string;
  opened_at: string;
}

export interface TradeHistoryEntry {
  tenant_id: string;
  bot_id: string;
  trade_id: string;
  source_runtime_id: string;
  pair: string;
  side: TradeSide;
  amount: string;
  realized_pnl: string;
  fees: string;
  exit_reason: string;
  opened_at: string;
  closed_at: string;
  reconciliation_status: ReconciliationStatus;
  analysis_id: string;
}

export interface PerformanceSummary {
  tenant_id: string;
  bot_id: string;
  realized_pnl: string;
  fees: string;
  net_pnl: string;
  trade_count: number;
  winning_trades: number;
  losing_trades: number;
  reconciliation_gaps: number;
}

export interface RiskLimitEvaluation {
  limit_name: string;
  configured_value: string;
  observed_value: string;
  passed: boolean;
}

export interface RiskDecisionRecord {
  risk_decision_id: string;
  tenant_id: string;
  trade_intent_id: string;
  risk_policy_version: string;
  decision: "APPROVED" | "REJECTED";
  reason_codes: string[];
  evaluated_limits: RiskLimitEvaluation[];
  occurred_at: string;
  context: CorrelationContext;
}

export interface AuditEvent {
  audit_id: string;
  occurred_at: string;
  actor_type: "user" | "service" | "agent" | "system";
  actor_id: string;
  tenant_id: string;
  resource_type: string;
  resource_id: string;
  action: string;
  result: "SUCCEEDED" | "DENIED" | "FAILED";
  request_id: string;
  correlation_id: string;
  causation_id: string | null;
  reason_code: string | null;
  details: Record<string, unknown>;
}

export interface ExecutionActivityEntry {
  audit: AuditEvent;
}
