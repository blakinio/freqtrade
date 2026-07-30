import { NextRequest, NextResponse } from "next/server";

import {
  identityErrorResponse,
  requireBrowserSession,
} from "@/lib/identity";
import {
  PortalApiConfigurationError,
  PortalApiResponseError,
} from "@/lib/portal-api";
import { getStrategyCatalogDetail } from "@/lib/strategy-catalog-api";

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
    { detail: "Strategy Catalog detail request failed closed" },
    { status: 502, headers: { "cache-control": "no-store" } },
  );
}

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ strategyVersion: string }> },
) {
  try {
    requireBrowserSession(request);
    const { strategyVersion } = await context.params;
    const detail = await getStrategyCatalogDetail(
      strategyVersion,
      request.headers.get("cookie"),
    );
    if (!detail) {
      return NextResponse.json(
        { detail: "Strategy version was not found" },
        { status: 404, headers: { "cache-control": "no-store" } },
      );
    }
    return NextResponse.json(detail, {
      headers: { "cache-control": "no-store" },
    });
  } catch (error) {
    return errorResponse(error);
  }
}
