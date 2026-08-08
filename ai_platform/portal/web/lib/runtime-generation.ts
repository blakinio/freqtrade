import "server-only";

import type { BotInstance } from "./contracts";
import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "./portal-api";

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

function controlPlaneUrl(): string {
  const value = process.env.PORTAL_CONTROL_PLANE_URL;
  if (!value) {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL is required in API mode");
  }
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL must use http or https");
  }
  return url.toString().replace(/\/$/, "");
}

export async function getBotRuntimeTruth(
  botId: string,
  cookieHeader?: string | null,
): Promise<BotRuntimeTruth | null> {
  if (dataMode() === "fixture") return null;
  const response = await fetch(
    `${controlPlaneUrl()}/v1/bots/${encodeURIComponent(botId)}/runtime-truth`,
    {
      cache: "no-store",
      headers: {
        accept: "application/json",
        ...(cookieHeader ? { cookie: cookieHeader } : {}),
      },
    },
  );
  if (response.status === 404) return null;
  if (!response.ok) {
    throw new PortalApiResponseError(
      `Portal API request failed with status ${response.status}`,
      response.status,
    );
  }
  return (await response.json()) as BotRuntimeTruth;
}
