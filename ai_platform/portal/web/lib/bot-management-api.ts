import "server-only";

import type { BotCatalogSnapshot, CatalogVersionRef } from "./bot-management-contracts";
import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "./portal-api";

const APPROVED_CATALOG_ID = "portal-approved-dry-run";

const fixtureCatalog: BotCatalogSnapshot = {
  catalog_id: APPROVED_CATALOG_ID,
  revision: 1,
  published_at: "2026-07-28T08:24:26Z",
  templates: [
    {
      template: {
        template_id: "ai-directional-dry-run",
        revision: 1,
        display_name: "AI Directional Dry Run",
        bot_family: "directional",
        supported_strategy_versions: ["ai-directional-v1"],
        supported_model_versions: ["model-validated-2026-07"],
        supported_exchange_profile_versions: ["simulated-spot-v1"],
        supported_market_types: ["spot"],
        supported_directions: ["long"],
        supported_execution_modes: ["dry_run"],
        required_policy_families: [
          "entry",
          "exit",
          "market",
          "position_sizing",
          "risk_reference",
          "runtime",
        ],
        optional_policy_families: [],
        created_at: "2026-07-28T08:24:26Z",
      },
      state: "ACTIVE",
      model_requirement: "REQUIRED",
      sha256: "a".repeat(64),
      published_at: "2026-07-28T08:24:26Z",
    },
  ],
  strategies: [
    {
      strategy_id: "ai-directional",
      version: "ai-directional-v1",
      state: "ACTIVE",
      supported_market_types: ["spot"],
      supported_directions: ["long"],
      supported_execution_modes: ["dry_run"],
      supported_model_versions: ["model-validated-2026-07"],
      supported_runtime_versions: ["freqtrade-2026.7"],
      supported_risk_policy_versions: ["risk-default-v1"],
      supported_policy_families: [
        "entry",
        "exit",
        "market",
        "position_sizing",
        "risk_reference",
        "runtime",
      ],
    },
  ],
  models: [
    {
      model_id: "model-validated",
      version: "model-validated-2026-07",
      state: "ACTIVE",
      compatible_strategy_versions: ["ai-directional-v1"],
      supported_runtime_versions: ["freqtrade-2026.7"],
    },
  ],
  exchange_profiles: [
    {
      version: "simulated-spot-v1",
      state: "ACTIVE",
      profile: {
        profile_id: "simulated-spot",
        revision: 1,
        exchange_id: "simulated",
        market_types: ["spot"],
        supports_short: false,
      },
    },
  ],
  runtimes: [
    {
      runtime_id: "freqtrade",
      version: "freqtrade-2026.7",
      state: "ACTIVE",
      supported_market_types: ["spot"],
      supported_execution_modes: ["dry_run"],
    },
  ],
  risk_policies: [
    {
      risk_policy_id: "risk-default",
      version: "risk-default-v1",
      state: "ACTIVE",
      supported_market_types: ["spot"],
      supported_execution_modes: ["dry_run"],
      supported_policy_families: [
        "entry",
        "exit",
        "market",
        "position_sizing",
        "risk_reference",
        "runtime",
      ],
    },
  ],
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

async function apiFetch<T>(path: string, cookieHeader?: string | null): Promise<T> {
  const response = await fetch(`${controlPlaneUrl()}${path}`, {
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
  return (await response.json()) as T;
}

export async function loadApprovedBotCatalog(
  cookieHeader?: string | null,
): Promise<BotCatalogSnapshot> {
  if (dataMode() === "fixture") return structuredClone(fixtureCatalog);
  const latest = await apiFetch<CatalogVersionRef>(
    `/v1/bot-management/catalog/${APPROVED_CATALOG_ID}/latest`,
    cookieHeader,
  );
  return apiFetch<BotCatalogSnapshot>(
    `/v1/bot-management/catalog/${encodeURIComponent(latest.catalog_id)}/${encodeURIComponent(latest.version)}`,
    cookieHeader,
  );
}
