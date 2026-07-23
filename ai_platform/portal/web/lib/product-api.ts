import type {
  AdministrationOverview,
  CreateGridBotConfigRequest,
  GridBotConfig,
  ModelHealthRecord,
  NotificationEntry,
  NotificationPreference,
  ProfileSecurityView,
  RuntimeLogAvailability,
  SignalEvent,
  StrategyCatalogEntry,
  SubmitSignalRequest,
} from "./product-contracts";
import {
  dataMode,
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "./portal-api";

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

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${controlPlaneUrl()}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      accept: "application/json",
      ...(init?.body ? { "content-type": "application/json" } : {}),
      ...init?.headers,
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

function cookieHeaders(cookieHeader?: string | null): HeadersInit | undefined {
  return cookieHeader ? { cookie: cookieHeader } : undefined;
}

const fixtureSignal: SignalEvent = {
  signal_id: "41414141-4141-4414-8414-414141414141",
  tenant_id: "tenant-demo",
  bot_id: "bot-btc-dryrun-01",
  pair: "BTC/USDT",
  side: "BUY",
  timeframe: "5m",
  confidence: "0.82",
  rationale: "Deterministic fixture signal for browser acceptance only.",
  source: "MANUAL",
  created_by_actor_id: "actor-fixture",
  occurred_at: "2026-07-23T18:00:00Z",
  context: {
    request_id: "42424242-4242-4424-8424-424242424242",
    correlation_id: "43434343-4343-4434-8434-434343434343",
    causation_id: null,
  },
  execution_authority: false,
};

const fixtureStrategies: StrategyCatalogEntry[] = [
  {
    strategy_version: "ai-directional-v1",
    display_name: "AI Directional",
    description: "Immutable directional strategy reference subject to deterministic risk controls.",
    kind: "DIRECTIONAL",
    allowed_execution_modes: ["simulated", "dry_run"],
    runtime_status: "BOT_REFERENCE",
    immutable: true,
  },
  {
    strategy_version: "grid-dry-run-v1",
    display_name: "Grid Dry Run",
    description: "Portal-managed grid configuration restricted to dry-run execution mode.",
    kind: "GRID",
    allowed_execution_modes: ["dry_run"],
    runtime_status: "PORTAL_CONFIG_ONLY",
    immutable: true,
  },
];

const fixtureGrid: GridBotConfig = {
  grid_config_id: "44444444-4444-4444-8444-444444444445",
  tenant_id: "tenant-demo",
  bot_id: "bot-grid-dryrun-01",
  pair: "BTC/USDT",
  strategy_version: "grid-dry-run-v1",
  lower_price: "90000",
  upper_price: "110000",
  levels: 10,
  quote_allocation: "1000",
  execution_mode: "dry_run",
  created_by_actor_id: "actor-fixture",
  created_at: "2026-07-23T18:05:00Z",
};

const fixturePreference: NotificationPreference = {
  tenant_id: "tenant-demo",
  actor_id: "actor-fixture",
  in_app_enabled: true,
  signal_events: true,
  risk_events: true,
  execution_events: true,
  updated_at: "2026-07-23T18:10:00Z",
};

export async function listSignals(cookieHeader?: string | null): Promise<SignalEvent[]> {
  if (dataMode() === "fixture") return [structuredClone(fixtureSignal)];
  return apiFetch<SignalEvent[]>("/v1/signals", { headers: cookieHeaders(cookieHeader) });
}

export async function submitSignal(
  request: SubmitSignalRequest,
  cookieHeader?: string | null,
): Promise<SignalEvent> {
  if (dataMode() === "fixture") {
    return { ...structuredClone(fixtureSignal), ...request };
  }
  return apiFetch<SignalEvent>("/v1/signals", {
    method: "POST",
    headers: cookieHeaders(cookieHeader),
    body: JSON.stringify(request),
  });
}

export async function listStrategies(
  cookieHeader?: string | null,
): Promise<StrategyCatalogEntry[]> {
  if (dataMode() === "fixture") return structuredClone(fixtureStrategies);
  return apiFetch<StrategyCatalogEntry[]>("/v1/strategies", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function listGridBotConfigs(
  cookieHeader?: string | null,
): Promise<GridBotConfig[]> {
  if (dataMode() === "fixture") return [structuredClone(fixtureGrid)];
  return apiFetch<GridBotConfig[]>("/v1/grid-bots", { headers: cookieHeaders(cookieHeader) });
}

export async function createGridBotConfig(
  request: CreateGridBotConfigRequest,
  cookieHeader?: string | null,
): Promise<GridBotConfig> {
  if (dataMode() === "fixture") return { ...structuredClone(fixtureGrid), ...request };
  return apiFetch<GridBotConfig>("/v1/grid-bots", {
    method: "POST",
    headers: cookieHeaders(cookieHeader),
    body: JSON.stringify(request),
  });
}

export async function listNotifications(
  cookieHeader?: string | null,
): Promise<NotificationEntry[]> {
  if (dataMode() === "fixture") {
    return [
      {
        notification_id: `signal:${fixtureSignal.signal_id}`,
        tenant_id: fixtureSignal.tenant_id,
        category: "SIGNAL",
        severity: "INFO",
        summary: `BUY signal recorded for ${fixtureSignal.pair} on ${fixtureSignal.bot_id}`,
        resource_type: "signal",
        resource_id: fixtureSignal.signal_id,
        occurred_at: fixtureSignal.occurred_at,
      },
    ];
  }
  return apiFetch<NotificationEntry[]>("/v1/notifications", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function getNotificationPreferences(
  cookieHeader?: string | null,
): Promise<NotificationPreference> {
  if (dataMode() === "fixture") return structuredClone(fixturePreference);
  return apiFetch<NotificationPreference>("/v1/notifications/preferences", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function updateNotificationPreferences(
  request: Omit<NotificationPreference, "tenant_id" | "actor_id" | "updated_at">,
  cookieHeader?: string | null,
): Promise<NotificationPreference> {
  if (dataMode() === "fixture") return { ...structuredClone(fixturePreference), ...request };
  return apiFetch<NotificationPreference>("/v1/notifications/preferences", {
    method: "PUT",
    headers: cookieHeaders(cookieHeader),
    body: JSON.stringify(request),
  });
}

export async function getProfileSecurity(
  cookieHeader?: string | null,
): Promise<ProfileSecurityView> {
  if (dataMode() === "fixture") {
    return {
      tenant_id: "tenant-demo",
      actor_id: "actor-fixture",
      actor_type: "user",
      permissions: ["bot.read", "bot.create", "trade.manual_execute", "model.read"],
      authentication_boundary: "trusted-application-identity",
      mfa_status: "MANAGED_BY_EXTERNAL_IDENTITY_PROVIDER",
      session_management: "MANAGED_BY_EXTERNAL_IDENTITY_PROVIDER",
      secrets_exposed: false,
    };
  }
  return apiFetch<ProfileSecurityView>("/v1/profile", { headers: cookieHeaders(cookieHeader) });
}

export async function getAdministrationOverview(
  cookieHeader?: string | null,
): Promise<AdministrationOverview> {
  if (dataMode() === "fixture") {
    return {
      tenant_id: "tenant-demo",
      current_actor_id: "actor-fixture",
      current_permissions: ["admin.manage", "audit.read", "bot.read"],
      builtin_roles: [
        {
          role_id: "builtin:admin",
          tenant_id: "tenant-demo",
          name: "admin",
          permissions: ["admin.manage", "audit.read", "bot.read"],
        },
      ],
      membership_source: "external-identity-provider",
    };
  }
  return apiFetch<AdministrationOverview>("/v1/admin/overview", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function listModelHealth(
  cookieHeader?: string | null,
): Promise<ModelHealthRecord[]> {
  if (dataMode() === "fixture") {
    return [
      {
        model_version_id: "model-validated-2026-07",
        tenant_id: "tenant-demo",
        model_family_id: "directional-lightgbm",
        lifecycle_state: "DRY_RUN",
        created_at: "2026-07-20T10:00:00Z",
        training_window_end: "2026-05-01T00:00:00Z",
        metadata_age_days: 3,
        drift_status: "UNAVAILABLE",
        drift_reason: "CANONICAL_DRIFT_TELEMETRY_SOURCE_NOT_CONFIGURED",
      },
    ];
  }
  return apiFetch<ModelHealthRecord[]>("/v1/model-health", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function getRuntimeLogAvailability(
  cookieHeader?: string | null,
): Promise<RuntimeLogAvailability> {
  if (dataMode() === "fixture") {
    return {
      available: false,
      source: "portal-execution-activity",
      reason_code: "CENTRALIZED_RUNTIME_STDOUT_STDERR_SOURCE_NOT_CONFIGURED",
      checked_at: "2026-07-23T18:15:00Z",
    };
  }
  return apiFetch<RuntimeLogAvailability>("/v1/runtime-log-availability", {
    headers: cookieHeaders(cookieHeader),
  });
}
