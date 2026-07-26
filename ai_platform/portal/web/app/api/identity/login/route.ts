import { NextRequest, NextResponse } from "next/server";

import {
  detailFromPayload,
  fixtureIdentityMode,
  identityBackendFetch,
  identityErrorResponse,
  responsePayload,
  safeExternalAuthorizationLocation,
  safeReturnTo,
  setFixtureIdentity,
} from "@/lib/identity";

export async function GET(request: NextRequest) {
  try {
    const returnTo = safeReturnTo(request.nextUrl.searchParams.get("return_to"));
    if (fixtureIdentityMode()) {
      const response = NextResponse.redirect(new URL(returnTo, request.url), 303);
      setFixtureIdentity(response, "authenticated");
      response.headers.set("cache-control", "no-store");
      return response;
    }

    const parameters = new URLSearchParams({ return_to: returnTo });
    const tenantId = request.nextUrl.searchParams.get("tenant_id")?.trim();
    if (tenantId) parameters.set("tenant_id", tenantId);
    const upstream = await identityBackendFetch(`/v1/identity/login?${parameters.toString()}`);
    if (upstream.status < 300 || upstream.status >= 400) {
      const payload = await responsePayload(upstream);
      return NextResponse.json(
        { detail: detailFromPayload(payload, upstream.status) },
        { status: upstream.status, headers: { "cache-control": "no-store" } },
      );
    }
    const location = safeExternalAuthorizationLocation(upstream.headers.get("location"));
    return NextResponse.redirect(location, 307);
  } catch (error) {
    return (
      identityErrorResponse(error) ??
      NextResponse.json({ detail: "Portal login request failed" }, { status: 502 })
    );
  }
}
