import "server-only";

import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "./portal-api";

export interface GridControlOverview {
  capability_evidence_provider_status: "AVAILABLE" | "UNAVAILABLE";
  canonical_preview_enabled: boolean;
  policy_persistence_enabled: boolean;
  browser_supplied_capability_evidence_accepted: false;
  execution_submission_enabled: false;
}

const fixtureOverview: GridControlOverview = {
  capability_evidence_provider_status: "UNAVAILABLE",
  canonical_preview_enabled: false,
  policy_persistence_enabled: false,
  browser_supplied_capability_evidence_accepted: false,
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

export async function loadGridControlOverview(
  cookieHeader?: string | null,
): Promise<GridControlOverview> {
  if (dataMode() === "fixture") return structuredClone(fixtureOverview);
  const response = await fetch(`${controlPlaneUrl()}/v1/bot-management/grid/overview`, {
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
  return (await response.json()) as GridControlOverview;
}
