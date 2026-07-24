import type {
  AdministrationOverview,
  CreateGridBotConfigRequest,
  GridBotConfig,
  ModelHealthRecord,
  NotificationEntry,
  NotificationPreference,
  ProfileSecurityView,
  RuntimeLogAvailability,
  RuntimeLogQuery,
  RuntimeLogSearchResult,
  RuntimeObservabilitySourceStatus,
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

const fixtureRuntimeObservabilityStatus: RuntimeObservabilitySourceStatus = {
  source_id: "fixture-loki-private",
  availability: "AVAILABLE",
  checked_at: "2026-07-24T09:00:00Z",
  reason_code: "SOURCE_READY",
  log_retention_days: 14,
  trace_retention_days: 7,
  metric_retention_days: 30,
  trace_source: "fixture-tempo-private",
  metric_source: "fixture-prometheus-private",
  runbook_path: "/docs/ai_platform/portal/runbooks/RUNTIME_OBSERVABILITY.md",
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
        health_record_id:
          "model-validated-2026-07:bot-btc-dryrun-01:runtime-1:revision-1:fixture-source",
        model_version_id: "model-validated-2026-07",
        tenant_id: "tenant-demo",
        model_family_id: "directional-lightgbm",
        lifecycle_state: "DRY_RUN",
        created_at: "2026-07-20T10:00:00Z",
        training_window_end: "2026-05-01T00:00:00Z",
        metadata_age_days: 3,
        drift_status: "HEALTHY",
        drift_reason: "PSI_V1_WITHIN_LIMITS",
        policy_version: "psi-v1",
        reference_window_id: "fixture-reference-2026-07",
        observation_window_id: "fixture-observation-2026-07-24",
        reference_sample_count: 200,
        observation_sample_count: 200,
        accepted_predictions: 180,
        rejected_predictions: 20,
        rejection_reasons: [{ reason_code: "DO_PREDICT_FALSE", count: 20 }],
        prediction_drift_score: "0.000400",
        max_feature_drift_score: "0.001600",
        worst_feature_name: "rsi_14",
        max_feature_quality_issue_rate: "0.000000",
        feature_schema_version_id: "features-v1",
        bot_id: "bot-btc-dryrun-01",
        bot_config_revision_id: "revision-1",
        runtime_id: "runtime-1",
        source_id: "fixture-source",
        source_availability: "AVAILABLE",
        source_checked_at: "2026-07-24T09:00:00Z",
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

export async function getRuntimeObservabilityAvailability(
  cookieHeader?: string | null,
): Promise<RuntimeObservabilitySourceStatus> {
  if (dataMode() === "fixture") return structuredClone(fixtureRuntimeObservabilityStatus);
  return apiFetch<RuntimeObservabilitySourceStatus>("/v1/runtime-observability/availability", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function searchRuntimeLogs(
  query: RuntimeLogQuery,
  cookieHeader?: string | null,
): Promise<RuntimeLogSearchResult> {
  if (dataMode() === "fixture") {
    return {
      query: { ...structuredClone(query), limit: query.limit ?? 100 },
      source_status: structuredClone(fixtureRuntimeObservabilityStatus),
      records: [
        {
          record_id: "fixture-runtime-log-1",
          tenant_id: "tenant-demo",
          timestamp: "2026-07-24T08:55:00Z",
          service: "freqtrade-runtime",
          component: "exchange-loop",
          environment: "test",
          runtime_id: "runtime-1",
          bot_id: "bot-btc-dryrun-01",
          correlation_id: "43434343-4343-4434-8434-434343434343",
          trace_id: "fixture-trace-1",
          span_id: "fixture-span-1",
          level: "ERROR",
          message: "Exchange request failed and remained operational evidence only.",
          fields: { reason_code: "EXCHANGE_REQUEST_TIMEOUT", authorization: "[REDACTED]" },
          source_id: fixtureRuntimeObservabilityStatus.source_id,
          retention_expires_at: "2026-08-07T08:55:00Z",
          audit_evidence: false,
        },
      ],
      truncated: false,
    };
  }
  return apiFetch<RuntimeLogSearchResult>("/v1/runtime-observability/logs/search", {
    method: "POST",
    headers: cookieHeaders(cookieHeader),
    body: JSON.stringify(query),
  });
}
