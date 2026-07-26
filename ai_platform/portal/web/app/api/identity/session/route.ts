import { NextRequest, NextResponse } from "next/server";

import {
  detailFromPayload,
  FIXTURE_SESSION_COOKIE_NAME,
  fixtureIdentityMode,
  fixtureIdentityState,
  fixtureSession,
  identityBackendFetch,
  identityErrorResponse,
  PortalIdentityBoundaryError,
  requireBrowserSession,
  responsePayload,
} from "@/lib/identity";

export async function GET(request: NextRequest) {
  try {
    if (fixtureIdentityMode() && !request.cookies.get(FIXTURE_SESSION_COOKIE_NAME)?.value) {
      throw new PortalIdentityBoundaryError("Portal session is missing", 401, "SESSION_MISSING");
    }
    requireBrowserSession(request);
    if (fixtureIdentityMode()) {
      return NextResponse.json(fixtureSession(fixtureIdentityState(request)), {
        headers: { "cache-control": "no-store" },
      });
    }

    const upstream = await identityBackendFetch("/v1/identity/session", {
      headers: request.headers.get("cookie")
        ? { cookie: request.headers.get("cookie") as string }
        : undefined,
    });
    const payload = await responsePayload(upstream);
    if (!upstream.ok) {
      return NextResponse.json(
        { detail: detailFromPayload(payload, upstream.status) },
        { status: upstream.status, headers: { "cache-control": "no-store" } },
      );
    }
    return NextResponse.json(payload, { headers: { "cache-control": "no-store" } });
  } catch (error) {
    return (
      identityErrorResponse(error) ??
      NextResponse.json({ detail: "Portal session request failed" }, { status: 502 })
    );
  }
}
