import "server-only";

import type { BotRuntimeTruth } from "./runtime-generation-contracts";
import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "./portal-api";

export async function getBotRuntimeTruth(
  botId: string,
  cookieHeader?: string | null,
): Promise<BotRuntimeTruth | null> {
  if (dataMode() === "fixture") return null;
  const value = process.env.PORTAL_CONTROL_PLANE_URL;
  if (!value) {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL is required in API mode");
  }
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new PortalApiConfigurationError("PORTAL_CONTROL_PLANE_URL must use http or https");
  }
  const response = await fetch(
    `${url.toString().replace(/\/$/, "")}/v1/bots/${encodeURIComponent(botId)}/runtime-truth`,
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
