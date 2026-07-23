import type {
  BotInstance,
  CreateBotRequest,
  DashboardSnapshot,
  LearningHistoryEntry,
  ModelVersion,
  PortalEnvironment,
  TerminalIntentRequest,
  TerminalIntentResult,
  TradeAnalysis,
  TradeInsight,
} from "./contracts";
import {
  createFixtureBot,
  fixtureDashboard,
  listFixtureBots,
  listFixtureInsights,
  listFixtureLearningHistory,
  listFixtureModels,
  listFixtureTradeAnalyses,
  submitFixtureTerminalIntent,
} from "./fixtures";

export class PortalApiConfigurationError extends Error {}
export class PortalApiResponseError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

type DataMode = "api" | "fixture";

export function dataMode(): DataMode {
  return process.env.PORTAL_WEB_DATA_MODE === "fixture" ? "fixture" : "api";
}

export function portalEnvironment(): PortalEnvironment {
  const value = process.env.PORTAL_ENVIRONMENT;
  if (value === "research" || value === "test" || value === "staging" || value === "production") {
    return value;
  }
  if (dataMode() === "fixture") {
    return "test";
  }
  throw new PortalApiConfigurationError("PORTAL_ENVIRONMENT is required in API mode");
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

export async function listBots(cookieHeader?: string | null): Promise<BotInstance[]> {
  if (dataMode() === "fixture") {
    return listFixtureBots();
  }
  return apiFetch<BotInstance[]>("/v1/bots", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function getBot(
  botId: string,
  cookieHeader?: string | null,
): Promise<BotInstance | null> {
  if (dataMode() === "fixture") {
    return listFixtureBots().find((bot) => bot.bot_id === botId) ?? null;
  }
  try {
    return await apiFetch<BotInstance>(`/v1/bots/${encodeURIComponent(botId)}`, {
      headers: cookieHeaders(cookieHeader),
    });
  } catch (error) {
    if (error instanceof PortalApiResponseError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function createBot(
  request: CreateBotRequest,
  cookieHeader?: string | null,
): Promise<BotInstance> {
  if (dataMode() === "fixture") {
    return createFixtureBot(request);
  }
  return apiFetch<BotInstance>("/v1/bots", {
    method: "POST",
    headers: cookieHeaders(cookieHeader),
    body: JSON.stringify(request),
  });
}

export async function submitTerminalIntent(
  request: TerminalIntentRequest,
  cookieHeader?: string | null,
): Promise<TerminalIntentResult> {
  if (dataMode() === "fixture") {
    return submitFixtureTerminalIntent(request);
  }
  return apiFetch<TerminalIntentResult>("/v1/terminal/intents", {
    method: "POST",
    headers: cookieHeaders(cookieHeader),
    body: JSON.stringify(request),
  });
}

export async function listModels(cookieHeader?: string | null): Promise<ModelVersion[]> {
  if (dataMode() === "fixture") {
    return listFixtureModels();
  }
  return apiFetch<ModelVersion[]>("/v1/models", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function listTradeAnalyses(cookieHeader?: string | null): Promise<TradeAnalysis[]> {
  if (dataMode() === "fixture") {
    return listFixtureTradeAnalyses();
  }
  return apiFetch<TradeAnalysis[]>("/v1/trade-analysis", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function listInsights(cookieHeader?: string | null): Promise<TradeInsight[]> {
  if (dataMode() === "fixture") {
    return listFixtureInsights();
  }
  return apiFetch<TradeInsight[]>("/v1/insights", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function listLearningHistory(
  cookieHeader?: string | null,
): Promise<LearningHistoryEntry[]> {
  if (dataMode() === "fixture") {
    return listFixtureLearningHistory();
  }
  return apiFetch<LearningHistoryEntry[]>("/v1/learning/history", {
    headers: cookieHeaders(cookieHeader),
  });
}

export async function dashboardSnapshot(cookieHeader?: string | null): Promise<DashboardSnapshot> {
  const environment = portalEnvironment();
  if (dataMode() === "fixture") {
    return fixtureDashboard(environment);
  }
  const bots = await listBots(cookieHeader);
  return {
    environment,
    freshnessLabel: "Live control-plane snapshot",
    activeBots: bots.filter((bot) => bot.observed_state === "RUNNING").length,
    attentionBots: bots.filter((bot) => bot.observed_state === "ERROR").length,
    runtimeHealth: bots.some((bot) => bot.observed_state === "ERROR") ? "degraded" : "healthy",
    modelHealth: "unknown",
    riskStatus: "unknown",
    bots,
  };
}
