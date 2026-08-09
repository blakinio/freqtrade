import { dataMode } from "./portal-api";
import type {
  EquityPoint,
  ExperimentBundle,
  ExperimentComparison,
  ExperimentCreateRequest,
  ExperimentDetail,
  ExperimentSummary,
  ExperimentTrade,
  SignalExplanation,
  StrategyLabDefinition,
} from "./strategy-lab-contracts";
import {
  compareFixtureStrategyLabExperiments,
  createFixtureStrategyLabExperiment,
  fixtureStrategies,
  getFixtureStrategyLabBundle,
  listFixtureStrategyLabExperiments,
} from "./strategy-lab-fixtures";

interface Page<T> {
  items: T[];
  total: number;
}

const CSRF_COOKIE_NAME = "__Host-portal_csrf";
const CSRF_HEADER_NAME = "x-csrf-token";
const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function controlPlaneUrl(): string {
  const value = process.env.PORTAL_CONTROL_PLANE_URL;
  if (!value) throw new Error("PORTAL_CONTROL_PLANE_URL is required in API mode");
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("PORTAL_CONTROL_PLANE_URL must use http or https");
  }
  return url.toString().replace(/\/$/, "");
}

function csrfHeaders(cookieHeader: string | undefined, init: RequestInit | undefined): HeadersInit {
  const method = (init?.method ?? "GET").toUpperCase();
  if (!MUTATING_METHODS.has(method)) return {};
  if (!cookieHeader) throw new Error("STRATEGY_LAB_CSRF_MISSING: browser session cookies are required");
  const prefix = `${CSRF_COOKIE_NAME}=`;
  const encoded = cookieHeader
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(prefix))
    ?.slice(prefix.length);
  if (!encoded) throw new Error("STRATEGY_LAB_CSRF_MISSING: CSRF cookie is required");
  let token: string;
  try {
    token = decodeURIComponent(encoded);
  } catch {
    throw new Error("STRATEGY_LAB_CSRF_INVALID: CSRF cookie is malformed");
  }
  if (!token) throw new Error("STRATEGY_LAB_CSRF_MISSING: CSRF cookie is empty");
  return { [CSRF_HEADER_NAME]: token };
}

async function apiFetch<T>(path: string, cookieHeader?: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${controlPlaneUrl()}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      accept: "application/json",
      ...(init?.body ? { "content-type": "application/json" } : {}),
      ...(cookieHeader ? { cookie: cookieHeader } : {}),
      ...init?.headers,
      ...csrfHeaders(cookieHeader, init),
    },
  });
  if (!response.ok) {
    let reason = `STRATEGY_LAB_HTTP_${response.status}`;
    let message = `Strategy Lab API failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as {
        detail?: string | { reason_code?: string; message?: string };
      };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (payload.detail) {
        reason = payload.detail.reason_code ?? reason;
        message = payload.detail.message ?? message;
      }
    } catch {
      // Preserve the bounded status-based error when the response is not JSON.
    }
    throw new Error(`${reason}: ${message}`);
  }
  return (await response.json()) as T;
}

export async function listStrategyLabStrategies(cookieHeader?: string): Promise<StrategyLabDefinition[]> {
  if (dataMode() === "fixture") return fixtureStrategies;
  return apiFetch<StrategyLabDefinition[]>("/v1/strategy-lab/strategies", cookieHeader);
}

export async function listStrategyLabExperiments(cookieHeader?: string): Promise<ExperimentSummary[]> {
  if (dataMode() === "fixture") return listFixtureStrategyLabExperiments();
  return apiFetch<ExperimentSummary[]>("/v1/strategy-lab/experiments", cookieHeader);
}

export async function getStrategyLabBundle(
  experimentId: string,
  cookieHeader?: string,
): Promise<ExperimentBundle> {
  if (dataMode() === "fixture") return getFixtureStrategyLabBundle(experimentId);
  const encoded = encodeURIComponent(experimentId);
  const [detail, trades, signals, equity] = await Promise.all([
    apiFetch<ExperimentDetail>(`/v1/strategy-lab/experiments/${encoded}`, cookieHeader),
    apiFetch<Page<ExperimentTrade>>(`/v1/strategy-lab/experiments/${encoded}/trades?limit=200`, cookieHeader),
    apiFetch<Page<SignalExplanation>>(`/v1/strategy-lab/experiments/${encoded}/signals?limit=500`, cookieHeader),
    apiFetch<EquityPoint[]>(`/v1/strategy-lab/experiments/${encoded}/equity`, cookieHeader),
  ]);
  return { detail, trades: trades.items, signals: signals.items, equity };
}

export async function createStrategyLabExperiment(
  request: ExperimentCreateRequest,
  idempotencyKey: string,
  cookieHeader?: string,
): Promise<ExperimentBundle> {
  if (dataMode() === "fixture") return createFixtureStrategyLabExperiment(request);
  const detail = await apiFetch<ExperimentDetail>("/v1/strategy-lab/experiments", cookieHeader, {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(request),
  });
  return getStrategyLabBundle(detail.experiment_id, cookieHeader);
}

export async function compareStrategyLabExperiments(
  baselineId: string,
  variantId: string,
  cookieHeader?: string,
): Promise<ExperimentComparison> {
  if (dataMode() === "fixture") return compareFixtureStrategyLabExperiments(baselineId, variantId);
  const query = new URLSearchParams({ baseline_id: baselineId, variant_id: variantId });
  return apiFetch<ExperimentComparison>(`/v1/strategy-lab/experiments/compare?${query}`, cookieHeader);
}
