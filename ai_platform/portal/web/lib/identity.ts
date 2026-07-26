import { NextRequest, NextResponse } from "next/server";

export const SESSION_COOKIE_NAME = "__Host-portal_session";
export const CSRF_COOKIE_NAME = "__Host-portal_csrf";
export const CSRF_HEADER_NAME = "x-csrf-token";

export const FIXTURE_STATE_COOKIE_NAME = "portal_fixture_identity_state";
export const FIXTURE_SESSION_COOKIE_NAME = "portal_fixture_session";
export const FIXTURE_CSRF_COOKIE_NAME = "portal_fixture_csrf";
export const FIXTURE_CSRF_TOKEN = "fixture-csrf-token";

export type FixtureIdentityState =
  | "authenticated"
  | "anonymous"
  | "expired"
  | "revoked"
  | "mfa_missing"
  | "step_up_stale"
  | "cross_tenant";

export interface PortalSessionView {
  principal_id: string;
  membership_id: string;
  tenant_id: string;
  roles: string[];
  membership_version: number;
  mfa_satisfied: boolean;
  authentication_time: string;
  created_at: string;
  last_seen_at: string;
  idle_expires_at: string;
  absolute_expires_at: string;
}

export class PortalIdentityBoundaryError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string,
  ) {
    super(message);
  }
}

export class PortalIdentityConfigurationError extends Error {}

export class PortalIdentityUpstreamError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

const unsafeMethods = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const validFixtureStates = new Set<FixtureIdentityState>([
  "authenticated",
  "anonymous",
  "expired",
  "revoked",
  "mfa_missing",
  "step_up_stale",
  "cross_tenant",
]);

export function fixtureIdentityMode(): boolean {
  return (
    process.env.PORTAL_WEB_DATA_MODE === "fixture" &&
    process.env.PORTAL_ENVIRONMENT === "test" &&
    process.env.PORTAL_IDENTITY_FIXTURE_MODE === "enabled"
  );
}

export function isFixtureIdentityState(value: unknown): value is FixtureIdentityState {
  return typeof value === "string" && validFixtureStates.has(value as FixtureIdentityState);
}

export function fixtureIdentityState(request: NextRequest): FixtureIdentityState {
  const value = request.cookies.get(FIXTURE_STATE_COOKIE_NAME)?.value;
  return isFixtureIdentityState(value) ? value : "authenticated";
}

export function fixtureSession(state: FixtureIdentityState): PortalSessionView {
  const tenantId = state === "cross_tenant" ? "tenant-other" : "tenant-demo";
  const authenticationTime =
    state === "step_up_stale" ? "2026-07-26T10:00:00Z" : "2026-07-26T12:58:00Z";
  return {
    principal_id: "principal-fixture",
    membership_id: `membership-${tenantId}`,
    tenant_id: tenantId,
    roles: ["operator"],
    membership_version: 1,
    mfa_satisfied: state !== "mfa_missing",
    authentication_time: authenticationTime,
    created_at: "2026-07-26T12:55:00Z",
    last_seen_at: "2026-07-26T13:00:00Z",
    idle_expires_at: "2099-07-26T13:30:00Z",
    absolute_expires_at: "2099-07-27T01:00:00Z",
  };
}

export function safeReturnTo(value: string | null | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return "/";
  return value;
}

export function requireBrowserSession(request: NextRequest): void {
  if (fixtureIdentityMode()) {
    const state = fixtureIdentityState(request);
    if (state === "anonymous") {
      throw new PortalIdentityBoundaryError("Portal session is missing", 401, "SESSION_MISSING");
    }
    if (state === "expired") {
      throw new PortalIdentityBoundaryError("Portal session has expired", 401, "SESSION_EXPIRED");
    }
    if (state === "revoked") {
      throw new PortalIdentityBoundaryError("Portal session has been revoked", 401, "SESSION_REVOKED");
    }
    if (state === "cross_tenant") {
      throw new PortalIdentityBoundaryError(
        "Authenticated membership does not authorize this tenant",
        403,
        "CROSS_TENANT_DENIED",
      );
    }
    return;
  }

  if (!request.cookies.get(SESSION_COOKIE_NAME)?.value) {
    throw new PortalIdentityBoundaryError("Portal session is missing", 401, "SESSION_MISSING");
  }
}

export function requireBrowserMutation(request: NextRequest): string {
  requireBrowserSession(request);
  const fixtureState = fixtureIdentityMode() ? fixtureIdentityState(request) : null;
  if (fixtureState === "mfa_missing") {
    throw new PortalIdentityBoundaryError(
      "MFA is required for mutation-capable memberships",
      403,
      "MFA_REQUIRED",
    );
  }
  if (fixtureState === "step_up_stale") {
    throw new PortalIdentityBoundaryError(
      "Recent authentication is required for this privileged action",
      403,
      "STEP_UP_REQUIRED",
    );
  }

  const csrfCookie = fixtureIdentityMode()
    ? request.cookies.get(FIXTURE_CSRF_COOKIE_NAME)?.value
    : request.cookies.get(CSRF_COOKIE_NAME)?.value;
  const csrfHeader = request.headers.get(CSRF_HEADER_NAME);
  if (!csrfCookie || !csrfHeader) {
    throw new PortalIdentityBoundaryError("CSRF token is missing", 403, "CSRF_MISSING");
  }
  if (csrfCookie !== csrfHeader) {
    throw new PortalIdentityBoundaryError("CSRF token mismatch", 403, "CSRF_MISMATCH");
  }
  return csrfHeader;
}

export function isUnsafeMethod(method: string): boolean {
  return unsafeMethods.has(method.toUpperCase());
}

export function forwardedIdentityHeaders(cookieHeader?: string | null): HeadersInit | undefined {
  if (!cookieHeader) return undefined;
  const csrfToken = cookieValue(cookieHeader, CSRF_COOKIE_NAME) ?? cookieValue(
    cookieHeader,
    FIXTURE_CSRF_COOKIE_NAME,
  );
  return {
    cookie: cookieHeader,
    ...(csrfToken ? { [CSRF_HEADER_NAME]: csrfToken } : {}),
  };
}

export async function forwardControlPlaneMutation<T>(
  request: NextRequest,
  path: string,
  method: "POST" | "PUT" | "PATCH" | "DELETE",
  body?: unknown,
): Promise<T> {
  const csrfToken = requireBrowserMutation(request);
  const cookieHeader = request.headers.get("cookie");
  if (!cookieHeader) {
    throw new PortalIdentityBoundaryError("Portal session is missing", 401, "SESSION_MISSING");
  }
  const response = await fetch(`${controlPlaneUrl()}${path}`, {
    method,
    cache: "no-store",
    redirect: "manual",
    headers: {
      accept: "application/json",
      cookie: cookieHeader,
      [CSRF_HEADER_NAME]: csrfToken,
      ...(body === undefined ? {} : { "content-type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const payload = await responsePayload(response);
  if (!response.ok) {
    throw new PortalIdentityUpstreamError(detailFromPayload(payload, response.status), response.status);
  }
  return payload as T;
}

export async function identityBackendFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${controlPlaneUrl()}${path}`, {
    ...init,
    cache: "no-store",
    redirect: "manual",
    headers: {
      accept: "application/json",
      ...init?.headers,
    },
  });
}

export function copySetCookieHeaders(source: Response, target: NextResponse): void {
  const headers = source.headers as Headers & { getSetCookie?: () => string[] };
  const values = headers.getSetCookie?.() ?? singleSetCookie(source.headers.get("set-cookie"));
  for (const value of values) target.headers.append("set-cookie", value);
}

export function setFixtureIdentity(response: NextResponse, state: FixtureIdentityState): void {
  response.cookies.set(FIXTURE_STATE_COOKIE_NAME, state, {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
  });
  if (state === "anonymous") {
    expireCookie(response, FIXTURE_SESSION_COOKIE_NAME, false, true);
    expireCookie(response, FIXTURE_CSRF_COOKIE_NAME, false, false);
    return;
  }
  response.cookies.set(FIXTURE_SESSION_COOKIE_NAME, `fixture-session-${state}`, {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
  });
  response.cookies.set(FIXTURE_CSRF_COOKIE_NAME, FIXTURE_CSRF_TOKEN, {
    httpOnly: false,
    sameSite: "lax",
    secure: false,
    path: "/",
  });
}

export function clearIdentityCookies(response: NextResponse): void {
  expireCookie(response, SESSION_COOKIE_NAME, true, true);
  expireCookie(response, CSRF_COOKIE_NAME, true, false);
  expireCookie(response, FIXTURE_SESSION_COOKIE_NAME, false, true);
  expireCookie(response, FIXTURE_CSRF_COOKIE_NAME, false, false);
  response.cookies.set(FIXTURE_STATE_COOKIE_NAME, "anonymous", {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
  });
}

export function identityErrorResponse(error: unknown): NextResponse | null {
  if (error instanceof PortalIdentityBoundaryError) {
    return NextResponse.json(
      { detail: error.message, code: error.code },
      { status: error.status, headers: { "cache-control": "no-store" } },
    );
  }
  if (error instanceof PortalIdentityUpstreamError) {
    return NextResponse.json(
      { detail: error.message },
      { status: error.status, headers: { "cache-control": "no-store" } },
    );
  }
  if (error instanceof PortalIdentityConfigurationError) {
    return NextResponse.json(
      { detail: "Portal identity backend is not configured" },
      { status: 503, headers: { "cache-control": "no-store" } },
    );
  }
  return null;
}

export async function responsePayload(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { detail: `Portal identity backend returned non-JSON status ${response.status}` };
  }
}

export function detailFromPayload(payload: unknown, status: number): string {
  if (typeof payload === "object" && payload !== null) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail) return detail;
  }
  return `Portal identity request failed with status ${status}`;
}

export function safeBackendReturnLocation(location: string | null, origin: string): URL {
  if (!location || !location.startsWith("/") || location.startsWith("//")) {
    return new URL("/", origin);
  }
  return new URL(location, origin);
}

export function safeExternalAuthorizationLocation(location: string | null): string {
  if (!location) throw new PortalIdentityUpstreamError("OIDC authorization redirect is missing", 502);
  const url = new URL(location);
  if (url.protocol !== "https:") {
    throw new PortalIdentityUpstreamError("OIDC authorization redirect must use HTTPS", 502);
  }
  return url.toString();
}

function controlPlaneUrl(): string {
  const value = process.env.PORTAL_CONTROL_PLANE_URL;
  if (!value) {
    throw new PortalIdentityConfigurationError("PORTAL_CONTROL_PLANE_URL is required");
  }
  const url = new URL(value);
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new PortalIdentityConfigurationError("PORTAL_CONTROL_PLANE_URL must use HTTP or HTTPS");
  }
  return url.toString().replace(/\/$/, "");
}

function cookieValue(header: string, name: string): string | null {
  for (const item of header.split(";")) {
    const [rawName, ...rest] = item.trim().split("=");
    if (rawName === name) return decodeURIComponent(rest.join("="));
  }
  return null;
}

function singleSetCookie(value: string | null): string[] {
  return value ? [value] : [];
}

function expireCookie(
  response: NextResponse,
  name: string,
  secure: boolean,
  httpOnly: boolean,
): void {
  response.cookies.set(name, "", {
    httpOnly,
    sameSite: "lax",
    secure,
    path: "/",
    maxAge: 0,
  });
}
