import { NextRequest, NextResponse } from "next/server";

import {
  FIXTURE_SESSION_COOKIE_NAME,
  FIXTURE_STATE_COOKIE_NAME,
  fixtureIdentityMode,
  fixtureIdentityState,
  identityErrorResponse,
  isUnsafeMethod,
  PortalIdentityBoundaryError,
  requireBrowserMutation,
  requireBrowserSession,
  safeReturnTo,
  SESSION_COOKIE_NAME,
  setFixtureIdentity,
} from "@/lib/identity";
import {
  applyBrowserSecurityHeaders,
  BrowserSecurityContext,
  createBrowserSecurityContext,
} from "@/lib/security-headers";

const publicPaths = new Set([
  "/login",
  "/denied",
  "/api/identity/login",
  "/api/identity/callback",
  "/api/identity/session",
  "/api/identity/fixture-state",
]);

export function proxy(request: NextRequest) {
  const security = createBrowserSecurityContext(request.headers);
  const pathname = request.nextUrl.pathname;
  if (publicPaths.has(pathname)) return nextResponse(security);

  if (pathname.startsWith("/api/")) {
    try {
      requireSessionPresence(request);
      if (isUnsafeMethod(request.method)) requireBrowserMutation(request);
      return nextResponse(security);
    } catch (error) {
      const response =
        identityErrorResponse(error) ??
        NextResponse.json({ detail: "Portal identity boundary failed" }, { status: 500 });
      return secureResponse(response, security);
    }
  }

  if (fixtureIdentityMode() && shouldBootstrapFixtureSession(request)) {
    const response = nextResponse(security);
    setFixtureIdentity(response, "authenticated");
    return response;
  }

  try {
    requireSessionPresence(request);
    return nextResponse(security);
  } catch (error) {
    if (error instanceof PortalIdentityBoundaryError && error.code === "CROSS_TENANT_DENIED") {
      return secureResponse(
        NextResponse.redirect(new URL("/denied?reason=cross_tenant", request.url)),
        security,
      );
    }
    const returnTo = safeReturnTo(`${pathname}${request.nextUrl.search}`);
    const reason =
      error instanceof PortalIdentityBoundaryError ? error.code.toLowerCase() : "session_required";
    const login = new URL("/login", request.url);
    login.searchParams.set("return_to", returnTo);
    login.searchParams.set("reason", reason);
    return secureResponse(NextResponse.redirect(login), security);
  }
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};

function nextResponse(security: BrowserSecurityContext): NextResponse {
  return secureResponse(
    NextResponse.next({ request: { headers: security.requestHeaders } }),
    security,
  );
}

function secureResponse<T extends NextResponse>(
  response: T,
  security: BrowserSecurityContext,
): T {
  return applyBrowserSecurityHeaders(response, security.contentSecurityPolicy);
}

function requireSessionPresence(request: NextRequest): void {
  if (fixtureIdentityMode()) {
    const state = fixtureIdentityState(request);
    if (!request.cookies.get(FIXTURE_SESSION_COOKIE_NAME)?.value && state === "authenticated") {
      throw new PortalIdentityBoundaryError("Portal session is missing", 401, "SESSION_MISSING");
    }
  } else if (!request.cookies.get(SESSION_COOKIE_NAME)?.value) {
    throw new PortalIdentityBoundaryError("Portal session is missing", 401, "SESSION_MISSING");
  }
  requireBrowserSession(request);
}

function shouldBootstrapFixtureSession(request: NextRequest): boolean {
  return (
    !request.cookies.get(FIXTURE_STATE_COOKIE_NAME)?.value &&
    !request.cookies.get(FIXTURE_SESSION_COOKIE_NAME)?.value
  );
}
