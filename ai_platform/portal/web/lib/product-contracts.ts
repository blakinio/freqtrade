import type { ExecutionMode, TradeSide } from "./contracts";

export interface SignalEvent {
  signal_id: string;
  tenant_id: string;
  bot_id: string;
  pair: string;
  side: TradeSide;
  timeframe: string;
  confidence: string;
  rationale: string;
  source: "MANUAL";
  created_by_actor_id: string;
  occurred_at: string;
  context: {
    request_id: string;
    correlation_id: string;
    causation_id: string | null;
  };
  execution_authority: false;
}

export interface SubmitSignalRequest {
  bot_id: string;
  pair: string;
  side: TradeSide;
  timeframe: string;
  confidence: string;
  rationale: string;
}

export interface StrategyCatalogEntry {
  strategy_version: string;
  display_name: string;
  description: string;
  kind: "DIRECTIONAL" | "GRID";
  allowed_execution_modes: ExecutionMode[];
  runtime_status: "BOT_REFERENCE" | "PORTAL_CONFIG_ONLY";
  immutable: boolean;
}

export interface GridBotConfig {
  grid_config_id: string;
  tenant_id: string;
  bot_id: string;
  pair: string;
  strategy_version: string;
  lower_price: string;
  upper_price: string;
  levels: number;
  quote_allocation: string;
  execution_mode: "dry_run";
  created_by_actor_id: string;
  created_at: string;
}

export interface CreateGridBotConfigRequest {
  bot_id: string;
  pair: string;
  lower_price: string;
  upper_price: string;
  levels: number;
  quote_allocation: string;
}

export interface NotificationPreference {
  tenant_id: string;
  actor_id: string;
  in_app_enabled: boolean;
  signal_events: boolean;
  risk_events: boolean;
  execution_events: boolean;
  updated_at: string;
}

export interface NotificationEntry {
  notification_id: string;
  tenant_id: string;
  category: "SIGNAL" | "RISK" | "EXECUTION";
  severity: "INFO" | "ATTENTION";
  summary: string;
  resource_type: string;
  resource_id: string;
  occurred_at: string;
}

export interface ProfileSecurityView {
  tenant_id: string;
  actor_id: string;
  actor_type: "user" | "service" | "agent" | "system";
  permissions: string[];
  authentication_boundary: string;
  mfa_status: string;
  session_management: string;
  secrets_exposed: false;
}

export interface RoleView {
  role_id: string;
  tenant_id: string;
  name: string;
  permissions: string[];
}

export interface AdministrationOverview {
  tenant_id: string;
  current_actor_id: string;
  current_permissions: string[];
  builtin_roles: RoleView[];
  membership_source: string;
}

export interface ModelHealthRecord {
  health_record_id: string;
  model_version_id: string;
  tenant_id: string;
  model_family_id: string;
  lifecycle_state: string;
  created_at: string;
  training_window_end: string;
  metadata_age_days: number;
  drift_status: "HEALTHY" | "ATTENTION" | "DEGRADED" | "INSUFFICIENT_EVIDENCE" | "UNAVAILABLE";
  drift_reason: string;
  policy_version: string | null;
  reference_window_id: string | null;
  observation_window_id: string | null;
  reference_sample_count: number;
  observation_sample_count: number;
  accepted_predictions: number;
  rejected_predictions: number;
  rejection_reasons: Array<{ reason_code: string; count: number }>;
  prediction_drift_score: string | null;
  max_feature_drift_score: string | null;
  worst_feature_name: string | null;
  max_feature_quality_issue_rate: string | null;
  feature_schema_version_id: string | null;
  bot_id: string | null;
  bot_config_revision_id: string | null;
  runtime_id: string | null;
  source_id: string | null;
  source_availability: "AVAILABLE" | "UNAVAILABLE";
  source_checked_at: string | null;
}

export interface RuntimeLogAvailability {
  available: boolean;
  source: string;
  reason_code: string;
  checked_at: string;
}

export interface RuntimeObservabilitySourceStatus {
  source_id: string;
  availability: "AVAILABLE" | "UNAVAILABLE";
  checked_at: string;
  reason_code: string;
  log_retention_days: number;
  trace_retention_days: number;
  metric_retention_days: number;
  trace_source: string;
  metric_source: string;
  runbook_path: string;
}

export interface RuntimeLogQuery {
  start_at: string;
  end_at: string;
  correlation_id?: string | null;
  runtime_id?: string | null;
  bot_id?: string | null;
  service?: string | null;
  component?: string | null;
  level?: string | null;
  limit?: number;
}

export interface RuntimeLogRecord {
  record_id: string;
  tenant_id: string;
  timestamp: string;
  service: string;
  component: string;
  environment: "research" | "test" | "staging" | "production";
  runtime_id: string;
  bot_id: string;
  correlation_id: string;
  trace_id: string | null;
  span_id: string | null;
  level: string;
  message: string;
  fields: Record<string, unknown>;
  source_id: string;
  retention_expires_at: string;
  audit_evidence: false;
}

export interface RuntimeLogSearchResult {
  query: Required<Pick<RuntimeLogQuery, "start_at" | "end_at">> & RuntimeLogQuery;
  source_status: RuntimeObservabilitySourceStatus;
  records: RuntimeLogRecord[];
  truncated: boolean;
}
