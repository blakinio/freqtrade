import type { BotInstance } from "./contracts";

export type BotConfigRevisionState = "DRAFT" | "PROMOTED" | "DEPRECATED";
export type BotRolloutStatus =
  | "REQUESTED"
  | "PRECHECK"
  | "BLOCKED"
  | "STOPPING_PREVIOUS"
  | "PREVIOUS_STOPPED"
  | "PROVISIONING"
  | "STARTING"
  | "VERIFYING"
  | "SUCCEEDED"
  | "FAILED";

export type RuntimeGenerationAwareBot = BotInstance & {
  latest_authored_revision_id: string | null;
  desired_revision_id: string | null;
  desired_runtime_generation_id: string | null;
  observed_runtime_generation_id: string | null;
  state_version: number;
};

export interface BotConfigRevisionTruth {
  revision_id: string;
  revision: number;
  state: BotConfigRevisionState;
  revision_content_digest: string | null;
}

export interface RuntimeGenerationTruth {
  generation_id: string;
  generation_ordinal: number;
  config_revision_id: string;
  config_revision_number: number;
  generation_spec_digest: string;
}

export interface BotRolloutTruth {
  rollout_id: string;
  from_generation_id: string | null;
  to_generation_id: string;
  status: BotRolloutStatus;
  reason_code: string | null;
  updated_at: string;
  completed_at: string | null;
}

export interface BotRuntimeTruth {
  bot: RuntimeGenerationAwareBot;
  revisions: BotConfigRevisionTruth[];
  desired_generation: RuntimeGenerationTruth | null;
  latest_rollout: BotRolloutTruth | null;
  pending_rollout: boolean;
}
