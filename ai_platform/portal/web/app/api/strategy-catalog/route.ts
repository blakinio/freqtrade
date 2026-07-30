import { NextRequest, NextResponse } from "next/server";

import {
  identityErrorResponse,
  requireBrowserSession,
} from "@/lib/identity";
import {
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "@/lib/portal-api";
import {
  listStrategyCatalog,
  type StrategyCatalogFixtureView,
} from "@/lib/strategy-catalog-api";

const fixtureViews = new Set<StrategyCatalogFixtureView>([
  "default",
  "empty",
  "stale",
  "failure",
]);

function errorResponse(error: unknown) {
  const identityResponse = identityErrorResponse(error);
  if (identityResponse) return identityResponse;
  if (error instanceof PortalApiResponseError) {
    return NextResponse.json(
      { detail: error.message },
      { status: error.status, headers: { "cache-control": "no-store" } },
    );
  }
  if (error instanceof PortalApiConfigurationError) {
    return NextResponse.json(
      { detail: "Strategy Catalog backend is not configured" },
      { status: 503, headers: { "cache-control": "no-store" } },
    );
  }
  return NextResponse.json(
    { detail: "Strategy Catalog request failed closed" },
    { status: 502, headers: { "cache-control": "no-store" } },
  );
}

function fixtureView(request: NextRequest): StrategyCatalogFixtureView {
  const value = request.nextUrl.searchParams.get("view") ?? "default";
  return fixtureViews.has(value as StrategyCatalogFixtureView)
    ? (value as StrategyCatalogFixtureView)
    : "default";
}

export async function GET(request: NextRequest) {
  try {
    requireBrowserSession(request);
    const payload = await listStrategyCatalog(
      request.headers.get("cookie"),
      fixtureView(request),
    );
    return NextResponse.json(payload, {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return errorResponse(error);
  }
}
