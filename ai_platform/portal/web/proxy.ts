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

const publicPaths = new Set([
  "/login",
  "/denied",
  "/api/identity/login",
  "/api/identity/callback",
  "/api/identity/session",
  "/api/identity/fixture-state",
]);

export function proxy(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  if (publicPaths.has(pathname)) return NextResponse.next();

  if (pathname.startsWith("/api/")) {
    try {
      requireSessionPresence(request);
      if (isUnsafeMethod(request.method)) requireBrowserMutation(request);
      return NextResponse.next();
    } catch (error) {
      return identityErrorResponse(error) ?? NextResponse.json(
        { detail: "Portal identity boundary failed" },
        { status: 500 },
      );
    }
  }

  if (fixtureIdentityMode() && shouldBootstrapFixtureSession(request)) {
    const response = NextResponse.next();
    setFixtureIdentity(response, "authenticated");
    return response;
  }

  try {
    requireSessionPresence(request);
    return NextResponse.next();
  } catch (error) {
    if (error instanceof PortalIdentityBoundaryError && error.code === "CROSS_TENANT_DENIED") {
      return NextResponse.redirect(new URL("/denied?reason=cross_tenant", request.url));
    }
    const returnTo = safeReturnTo(`${pathname}${request.nextUrl.search}`);
    const reason =
      error instanceof PortalIdentityBoundaryError ? error.code.toLowerCase() : "session_required";
    const login = new URL("/login", request.url);
    login.searchParams.set("return_to", returnTo);
    login.searchParams.set("reason", reason);
    return NextResponse.redirect(login);
  }
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};

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
