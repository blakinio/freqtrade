import "server-only";

import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "./portal-api";

export interface PublicSignalEndpointView {
  endpoint_id: string;
  revision: number;
  display_name: string;
  authentication_mode: string;
  schema_id: string;
  schema_revision: number;
  supported_commands: string[];
  authority: string;
  max_past_age_seconds: number;
  max_future_skew_seconds: number;
  replay_window_seconds: number;
  require_nonce: boolean;
  enabled: boolean;
  created_at: string;
  authentication_reference_exposed: false;
  webhook_slug_exposed: false;
}

export interface SignalControlOverview {
  authentication_provider_status: "AVAILABLE" | "UNAVAILABLE";
  endpoints: PublicSignalEndpointView[];
  accepted_signal_processing_enabled: boolean;
  execution_submission_enabled: false;
}

const fixtureOverview: SignalControlOverview = {
  authentication_provider_status: "UNAVAILABLE",
  endpoints: [],
  accepted_signal_processing_enabled: false,
  execution_submission_enabled: false,
};

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

export async function loadSignalControlOverview(
  cookieHeader?: string | null,
): Promise<SignalControlOverview> {
  if (dataMode() === "fixture") return structuredClone(fixtureOverview);
  const response = await fetch(`${controlPlaneUrl()}/v1/bot-management/signals/overview`, {
    cache: "no-store",
    headers: {
      accept: "application/json",
      ...(cookieHeader ? { cookie: cookieHeader } : {}),
    },
  });
  if (!response.ok) {
    throw new PortalApiResponseError(
      `Portal API request failed with status ${response.status}`,
      response.status,
    );
  }
  return (await response.json()) as SignalControlOverview;
}
