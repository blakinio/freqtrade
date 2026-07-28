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

export interface LifecycleIntentRequest {
  bot_id: string;
  action: LifecycleAction;
  expected_config_revision: number;
  idempotency_key: string;
}

export interface LifecycleIntentResult {
  command_id: string | null;
  bot_id: string;
  action: LifecycleAction;
  status: CommandOutcomeStatus;
  reason_codes: string[];
  command_persisted: boolean;
  execution_submission_performed: false;
}
