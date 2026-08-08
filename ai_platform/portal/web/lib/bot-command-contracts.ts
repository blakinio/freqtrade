export type LifecycleAction =
  | "START"
  | "PAUSE_NEW_ENTRIES"
  | "RESUME"
  | "STOP_KEEP_POSITIONS"
  | "STOP_AFTER_EXIT"
  | "RESTART_RUNTIME"
  | "RETIRE";

export type CommandOutcomeStatus =
  | "ACCEPTED"
  | "REJECTED"
  | "BLOCKED"
  | "PENDING_RECONCILIATION";

export type CommandReasonCode =
  | "CAPABILITY_MISSING"
  | "CONFIRMATION_REQUIRED"
  | "DUPLICATE_IDEMPOTENCY_KEY"
  | "ENVIRONMENT_MISMATCH"
  | "INVALID_COMMAND"
  | "KILL_SWITCH_ACTIVE"
  | "RISK_REJECTED"
  | "RUNTIME_UNAVAILABLE"
  | "RUNTIME_RESPONSE_AMBIGUOUS"
  | "STALE_GENERATION"
  | "STALE_REVISION"
  | "TENANT_MISMATCH";

export interface LifecycleIntentRequest {
  bot_id: string;
  action: LifecycleAction;
  expected_config_revision: number;
  expected_runtime_generation_id: string;
  idempotency_key: string;
}

export interface LifecycleIntentResult {
  command_id: string | null;
  bot_id: string;
  action: LifecycleAction;
  status: CommandOutcomeStatus;
  reason_codes: CommandReasonCode[];
  command_persisted: boolean;
  execution_submission_performed: false;
}
