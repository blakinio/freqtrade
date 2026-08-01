import "server-only";

import type { NextRequest } from "next/server";

import {
  FIXTURE_SESSION_COOKIE_NAME,
  fixtureIdentityMode,
  fixtureIdentityState,
  fixtureSession,
  identityBackendFetch,
  PortalIdentityBoundaryError,
  PortalIdentityConfigurationError,
  PortalIdentityUpstreamError,
  requireBrowserSession,
  SESSION_COOKIE_NAME,
  type PortalSessionView,
} from "@/lib/identity";

const sessionTokenPattern = /^[A-Za-z0-9_-]{43,256}$/u;
const readAuthorizedRoles = new Set(["analyst", "model_reviewer", "admin"]);
const defaultTimeoutMs = 2_000;
const maximumTimeoutMs = 10_000;

export async function authorizeMarketEvidenceRequest(request: NextRequest): Promise<void> {
  requireBrowserSession(request);
  const requiredTenant = configuredMarketEvidenceTenant();

  if (fixtureIdentityMode()) {
    if (!request.cookies.get(FIXTURE_SESSION_COOKIE_NAME)?.value) {
      throw new PortalIdentityBoundaryError("Portal session is missing", 401, "SESSION_MISSING");
    }
    const state = fixtureIdentityState(request);
    const current = fixtureSession(state);
    if (current.tenant_id !== requiredTenant) {
      throw new PortalIdentityBoundaryError(
        "Authenticated membership does not authorize this tenant",
        403,
        "CROSS_TENANT_DENIED",
      );
    }
    return;
  }

  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  if (!token) {
    throw new PortalIdentityBoundaryError("Portal session is missing", 401, "SESSION_MISSING");
  }
  if (!sessionTokenPattern.test(token)) {
    throw new PortalIdentityBoundaryError("Portal session is invalid", 401, "SESSION_INVALID");
  }

  let upstream: Response;
  try {
    upstream = await identityBackendFetch("/v1/identity/session", {
      headers: { cookie: `${SESSION_COOKIE_NAME}=${encodeURIComponent(token)}` },
      signal: AbortSignal.timeout(configuredSessionTimeoutMs()),
    });
  } catch {
    throw new PortalIdentityUpstreamError("Portal identity backend is unavailable", 503);
  }

  if (upstream.status === 401 || upstream.status === 404) {
    throw new PortalIdentityBoundaryError("Portal session is invalid", 401, "SESSION_INVALID");
  }
  if (upstream.status === 403) {
    throw new PortalIdentityBoundaryError(
      "Portal session is not authorized",
      403,
      "SESSION_FORBIDDEN",
    );
  }
  if (!upstream.ok) {
    throw new PortalIdentityUpstreamError("Portal identity backend is unavailable", 503);
  }

  const current = await parseSession(upstream);
  const now = Date.now();
  if (Date.parse(current.idle_expires_at) <= now || Date.parse(current.absolute_expires_at) <= now) {
    throw new PortalIdentityBoundaryError("Portal session has expired", 401, "SESSION_EXPIRED");
  }
  if (current.tenant_id !== requiredTenant) {
    throw new PortalIdentityBoundaryError(
      "Authenticated membership does not authorize this tenant",
      403,
      "CROSS_TENANT_DENIED",
    );
  }
  if (!current.roles.some((role) => readAuthorizedRoles.has(role))) {
    throw new PortalIdentityBoundaryError(
      "Market Evidence read permission is required",
      403,
      "MARKET_EVIDENCE_PERMISSION_DENIED",
    );
  }
}

async function parseSession(response: Response): Promise<PortalSessionView> {
  let value: unknown;
  try {
    value = JSON.parse(await response.text()) as unknown;
  } catch {
    throw new PortalIdentityUpstreamError("Portal identity backend response is invalid", 503);
  }
  if (!isPortalSessionView(value)) {
    throw new PortalIdentityUpstreamError("Portal identity backend response is invalid", 503);
  }
  return value;
}

function isPortalSessionView(value: unknown): value is PortalSessionView {
  if (typeof value !== "object" || value === null) return false;
  const item = value as Record<string, unknown>;
  const strings = [
    "principal_id",
    "membership_id",
    "tenant_id",
    "authentication_time",
    "created_at",
    "last_seen_at",
    "idle_expires_at",
    "absolute_expires_at",
  ];
  if (!strings.every((key) => typeof item[key] === "string" && item[key].length > 0)) return false;
  if (!Array.isArray(item.roles) || !item.roles.every((role) => typeof role === "string")) return false;
  if (!Number.isSafeInteger(item.membership_version) || Number(item.membership_version) < 1) return false;
  if (typeof item.mfa_satisfied !== "boolean") return false;
  return ["authentication_time", "created_at", "last_seen_at", "idle_expires_at", "absolute_expires_at"]
    .every((key) => Number.isFinite(Date.parse(item[key] as string)));
}

function configuredMarketEvidenceTenant(): string {
  const configured = process.env.PORTAL_MARKET_EVIDENCE_TENANT_ID?.trim();
  if (configured) return configured;
  if (fixtureIdentityMode()) return "tenant-demo";
  throw new PortalIdentityConfigurationError("PORTAL_MARKET_EVIDENCE_TENANT_ID is required");
}

function configuredSessionTimeoutMs(): number {
  const raw = process.env.PORTAL_IDENTITY_SESSION_TIMEOUT_MS?.trim();
  if (!raw) return defaultTimeoutMs;
  if (!/^\d+$/u.test(raw)) {
    throw new PortalIdentityConfigurationError("PORTAL_IDENTITY_SESSION_TIMEOUT_MS is invalid");
  }
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < 1 || value > maximumTimeoutMs) {
    throw new PortalIdentityConfigurationError("PORTAL_IDENTITY_SESSION_TIMEOUT_MS is invalid");
  }
  return value;
}
