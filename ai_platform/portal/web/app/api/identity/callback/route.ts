import { NextRequest, NextResponse } from "next/server";

import {
  copySetCookieHeaders,
  detailFromPayload,
  fixtureIdentityMode,
  identityBackendFetch,
  identityErrorResponse,
  responsePayload,
  safeBackendReturnLocation,
  safeReturnTo,
  setFixtureIdentity,
} from "@/lib/identity";

export async function GET(request: NextRequest) {
  try {
    const code = request.nextUrl.searchParams.get("code");
    const state = request.nextUrl.searchParams.get("state");
    if (!code || !state) {
      return NextResponse.json(
        { detail: "OIDC callback requires code and state" },
        { status: 422, headers: { "cache-control": "no-store" } },
      );
    }

    if (fixtureIdentityMode()) {
      const returnTo = safeReturnTo(request.nextUrl.searchParams.get("return_to"));
      const response = NextResponse.redirect(new URL(returnTo, request.url), 303);
      setFixtureIdentity(response, "authenticated");
      response.headers.set("cache-control", "no-store");
      return response;
    }

    const parameters = new URLSearchParams({ code, state });
    const upstream = await identityBackendFetch(`/v1/identity/callback?${parameters.toString()}`);
    if (upstream.status < 300 || upstream.status >= 400) {
      const payload = await responsePayload(upstream);
      return NextResponse.json(
        { detail: detailFromPayload(payload, upstream.status) },
        { status: upstream.status, headers: { "cache-control": "no-store" } },
      );
    }

    const response = NextResponse.redirect(
      safeBackendReturnLocation(upstream.headers.get("location"), request.nextUrl.origin),
      303,
    );
    copySetCookieHeaders(upstream, response);
    response.headers.set("cache-control", "no-store");
    return response;
  } catch (error) {
    return (
      identityErrorResponse(error) ??
      NextResponse.json({ detail: "Portal callback request failed" }, { status: 502 })
    );
  }
}
