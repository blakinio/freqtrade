import "server-only";

import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "./portal-api";

export interface PublicExchangeConnectionView {
  connection_id: string;
  metadata_revision: number;
  display_name: string;
  exchange_id: string;
  exchange_profile_ref: string;
  enabled_market_types: string[];
  verification_status: string;
  rotation_status: string;
  revocation_status: string;
  product_status: string;
  availability_status: string;
  trading_permission_status: string;
  withdrawal_permission_status: string;
  last_verified_at: string | null;
  reason_codes: string[];
  capability_profile: {
    profile_ref: string;
    capability: {
      supports_order_replace: boolean;
      supports_short: boolean;
      supports_subaccounts: boolean;
      maximum_leverage: string | null;
    };
    functions: string[];
  };
  updated_at: string;
  credential_material_exposed: false;
}

const fixtureConnection: PublicExchangeConnectionView = {
  connection_id: "simulated-dry-run",
  metadata_revision: 1,
  display_name: "Simulated dry-run",
  exchange_id: "simulated",
  exchange_profile_ref: "simulated-spot@1",
  enabled_market_types: ["spot"],
  verification_status: "VERIFIED",
  rotation_status: "CURRENT",
  revocation_status: "ACTIVE",
  product_status: "READY",
  availability_status: "AVAILABLE",
  trading_permission_status: "ENABLED",
  withdrawal_permission_status: "DISABLED_CONFIRMED",
  last_verified_at: "2026-07-28T08:24:26Z",
  reason_codes: [],
  capability_profile: {
    profile_ref: "simulated-spot@1",
    capability: {
      supports_order_replace: true,
      supports_short: false,
      supports_subaccounts: false,
      maximum_leverage: null,
    },
    functions: [
      "CANCEL_ORDER",
      "CREATE_ORDER",
      "FETCH_BALANCES",
      "FETCH_OPEN_ORDERS",
      "REPLACE_ORDER",
    ],
  },
  updated_at: "2026-07-28T08:24:26Z",
  credential_material_exposed: false,
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

export async function listPublicExchangeConnections(
  cookieHeader?: string | null,
): Promise<PublicExchangeConnectionView[]> {
  if (dataMode() === "fixture") return [structuredClone(fixtureConnection)];
  const response = await fetch(`${controlPlaneUrl()}/v1/bot-management/exchanges`, {
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
  return (await response.json()) as PublicExchangeConnectionView[];
}
